"""Session CRUD and WebSocket streaming endpoints."""
from __future__ import annotations

import asyncio
import threading
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from api.schemas import SessionResponse, SessionStartRequest
from api.session_manager import session_manager
from api.session_runner import run_session

router = APIRouter()


@router.post("", response_model=SessionResponse, status_code=202)
async def start_session(request: SessionStartRequest) -> SessionResponse:
    """Validate request, create session, launch engine groups in a background thread."""
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    loop = asyncio.get_event_loop()
    queue = session_manager.create(session_id)

    thread = threading.Thread(
        target=run_session,
        args=(
            request,
            session_id,
            queue,
            loop,
            lambda result: session_manager.set_complete(session_id, result),
            lambda err: session_manager.set_error(session_id, err),
        ),
        daemon=True,
        name=f"session-{session_id}",
    )
    thread.start()

    return SessionResponse(session_id=session_id, status="running")


@router.get("/{session_id}")
async def get_session(session_id: str) -> dict[str, Any]:
    """Return current status and result (if complete) for a session."""
    status = session_manager.get_status(session_id)
    if status == "not_found":
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    payload: dict[str, Any] = {"session_id": session_id, "status": status}

    if status == "complete":
        result = session_manager.get_result(session_id)
        if result:
            payload["result"] = result.model_dump()

    if status == "error":
        payload["error"] = session_manager.get_error(session_id)

    return payload


@router.websocket("/{session_id}/ws")
async def session_ws(websocket: WebSocket, session_id: str) -> None:
    """Stream progress events to the client as the engine runs."""
    await websocket.accept()

    queue = session_manager.get_queue(session_id)
    if queue is None:
        await websocket.close(code=4004, reason="Session not found")
        return

    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=25.0)
            except asyncio.TimeoutError:
                await websocket.send_json({"phase": "ping"})
                continue

            await websocket.send_json(event)

            if event.get("phase") in ("done", "error"):
                break

    except WebSocketDisconnect:
        pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
