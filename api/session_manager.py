"""
In-process session state store.
Holds asyncio Queues (for WebSocket streaming) and final MultiGroupResults.
"""
from __future__ import annotations

import asyncio
from typing import Dict, Optional

from models.schemas import MultiGroupResult


class SessionManager:
    def __init__(self) -> None:
        self._queues: Dict[str, asyncio.Queue] = {}
        self._results: Dict[str, Optional[MultiGroupResult]] = {}
        self._errors: Dict[str, Optional[str]] = {}
        self._status: Dict[str, str] = {}  # running | complete | error

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def create(self, session_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._queues[session_id] = q
        self._status[session_id] = "running"
        self._results[session_id] = None
        self._errors[session_id] = None
        return q

    def set_complete(self, session_id: str, result: MultiGroupResult) -> None:
        self._results[session_id] = result
        self._status[session_id] = "complete"

    def set_error(self, session_id: str, error: str) -> None:
        self._errors[session_id] = error
        self._status[session_id] = "error"

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def get_queue(self, session_id: str) -> Optional[asyncio.Queue]:
        return self._queues.get(session_id)

    def get_status(self, session_id: str) -> str:
        return self._status.get(session_id, "not_found")

    def get_result(self, session_id: str) -> Optional[MultiGroupResult]:
        return self._results.get(session_id)

    def get_error(self, session_id: str) -> Optional[str]:
        return self._errors.get(session_id)

    def list_sessions(self) -> list[str]:
        return list(self._status.keys())


# Singleton — imported everywhere
session_manager = SessionManager()
