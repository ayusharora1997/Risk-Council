"""
Runs one IterationEngine per generator group in a background thread,
piping progress events into an asyncio Queue for WebSocket streaming.
"""
from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, Callable, Dict, List

from agents.generator_agent import GeneratorAgent
from agents.reviewer_agent import ReviewerAgent
from api.schemas import SessionStartRequest
from engine.iteration_engine import IterationEngine
from models.schemas import (
    GeneratorGroupConfig,
    MultiGroupResult,
    ReviewerConfig,
    SessionConfig,
    SessionResult,
)
from providers import get_provider_with_keys
from storage.audit_trail import AuditTrail


def _enqueue(queue: asyncio.Queue, loop: asyncio.AbstractEventLoop, payload: Dict[str, Any]) -> None:
    asyncio.run_coroutine_threadsafe(queue.put(payload), loop)


def _make_group_callback(
    queue: asyncio.Queue,
    loop: asyncio.AbstractEventLoop,
    group_index: int,
    groups_total: int,
) -> Callable[[Dict[str, Any]], None]:
    def callback(payload: Dict[str, Any]) -> None:
        payload = dict(payload)
        payload["group_index"] = group_index
        payload["groups_total"] = groups_total
        _enqueue(queue, loop, payload)
    return callback


def run_session(
    request: SessionStartRequest,
    session_id: str,
    queue: asyncio.Queue,
    loop: asyncio.AbstractEventLoop,
    on_complete: Callable[[MultiGroupResult], None],
    on_error: Callable[[str], None],
) -> None:
    """Entry point for the background thread — runs all generator groups sequentially."""
    session_start = time.time()

    try:
        audit = AuditTrail()
        groups_total = len(request.generator_groups)
        group_results: List[SessionResult] = []
        group_configs: List[GeneratorGroupConfig] = []

        for i, grp in enumerate(request.generator_groups):
            # Build per-group SessionConfig (reuses the shared session_id)
            config = SessionConfig(
                session_id=session_id,
                scenario=request.scenario,
                document_type=request.document_type,
                reference_content=request.reference_content,
                target_score=request.target_score,
                max_iterations=request.max_iterations,
                generator_provider=grp.generator.provider,
                generator_model=grp.generator.model,
                reviewer_configs=[
                    ReviewerConfig(provider=r.provider, model=r.model, persona=r.persona)
                    for r in grp.reviewers
                ],
            )

            group_configs.append(
                GeneratorGroupConfig(
                    generator_provider=grp.generator.provider,
                    generator_model=grp.generator.model,
                    reviewer_configs=config.reviewer_configs,
                )
            )

            if i == 0:
                audit.save_config(config)

            # Notify client a new group is starting
            _enqueue(queue, loop, {
                "phase": "group_start",
                "group_index": i,
                "groups_total": groups_total,
                "generator": f"{grp.generator.provider}/{grp.generator.model}",
                "reviewers": [f"{r.provider}/{r.model}" for r in grp.reviewers],
            })

            gen_provider = get_provider_with_keys(grp.generator.provider, request.api_keys)
            generator = GeneratorAgent(provider=gen_provider, model=grp.generator.model)

            reviewers = [
                ReviewerAgent(
                    provider=get_provider_with_keys(rc.provider, request.api_keys),
                    model=rc.model,
                    persona=rc.persona,
                )
                for rc in config.reviewer_configs
            ]

            engine = IterationEngine(
                config=config,
                generator=generator,
                reviewers=reviewers,
                audit=audit,
                progress_callback=_make_group_callback(queue, loop, i, groups_total),
            )

            result = engine.run()
            group_results.append(result)

            _enqueue(queue, loop, {
                "phase": "group_complete",
                "group_index": i,
                "groups_total": groups_total,
                "best_score": result.best_score,
                "termination_reason": result.termination_reason,
            })

        best_idx = max(range(len(group_results)), key=lambda k: group_results[k].best_score)

        mgr = MultiGroupResult(
            session_id=session_id,
            scenario=request.scenario,
            document_type=request.document_type,
            reference_content=request.reference_content,
            target_score=request.target_score,
            max_iterations=request.max_iterations,
            generator_groups=group_configs,
            groups=group_results,
            overall_best_score=group_results[best_idx].best_score,
            overall_best_group_index=best_idx,
            total_duration_seconds=round(time.time() - session_start, 1),
        )

        on_complete(mgr)
        _enqueue(queue, loop, {
            "phase": "done",
            "session_id": session_id,
            "overall_best_score": mgr.overall_best_score,
            "overall_best_group_index": best_idx,
        })

    except Exception as exc:
        msg = f"{type(exc).__name__}: {exc}"
        on_error(msg)
        _enqueue(queue, loop, {"phase": "error", "error": msg})
