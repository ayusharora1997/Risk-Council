"""
JSONExporter — serialises a SessionResult to a structured JSON export file.
Includes all iterations, scores, feedback, and both initial and final policies.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from models.schemas import SessionResult

_EXPORT_ROOT = Path(__file__).resolve().parent.parent / "data" / "exports"


def _json_default(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serialisable")


class JSONExporter:
    """Exports a SessionResult to a structured JSON file."""

    def __init__(self, export_dir: Optional[Path] = None) -> None:
        self.export_dir = export_dir or _EXPORT_ROOT

    def export(self, result: SessionResult, filename: Optional[str] = None) -> Path:
        """Serialise the session result and write it to disk.

        Returns:
            Path to the written file.
        """
        filename = filename or f"{result.session_id}_export.json"
        out_path = self.export_dir / filename
        out_path.parent.mkdir(parents=True, exist_ok=True)

        payload = self._build_payload(result)

        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, default=_json_default, ensure_ascii=False)

        return out_path

    # ------------------------------------------------------------------

    def _build_payload(self, result: SessionResult) -> dict:
        """Build the export dict with convenient top-level keys."""
        return {
            "export_meta": {
                "tool": "AI Risk Council",
                "version": "1.0.0",
                "exported_at": datetime.utcnow().isoformat(),
            },
            "session": {
                "session_id": result.session_id,
                "termination_reason": result.termination_reason,
                "final_score": result.final_score,
                "best_score": result.best_score,
                "total_duration_seconds": result.total_duration_seconds,
                "completed_at": result.completed_at,
            },
            "config": result.config.model_dump(),
            "initial_policy": {
                "version": result.initial_policy.version,
                "word_count": result.initial_policy.word_count,
                "content": result.initial_policy.content,
                "generator_model": result.initial_policy.generator_model,
                "generator_provider": result.initial_policy.generator_provider,
                "created_at": result.initial_policy.created_at,
            },
            "final_policy": {
                "version": result.final_policy.version,
                "word_count": result.final_policy.word_count,
                "content": result.final_policy.content,
                "generator_model": result.final_policy.generator_model,
                "generator_provider": result.final_policy.generator_provider,
                "created_at": result.final_policy.created_at,
            },
            "iterations": [
                {
                    "iteration_number": rec.iteration_number,
                    "timestamp": rec.timestamp,
                    "policy_version": rec.policy_version,
                    "aggregated_score": rec.aggregated_score,
                    "score_breakdown": rec.score_breakdown,
                    "generator": f"{rec.generator_provider}/{rec.generator_model}",
                    "reviewers": [
                        f"{rc.provider}/{rc.model}" for rc in rec.reviewer_configs
                    ],
                    "individual_reviews": [
                        {
                            "reviewer": f"{r.reviewer_provider}/{r.reviewer_model}",
                            "score": r.score.as_dict(),
                            "biases": r.biases,
                            "ethical_risks": r.ethical_risks,
                            "implementation_challenges": r.implementation_challenges,
                            "missing_controls": r.missing_controls,
                            "recommendations": r.recommendations,
                            "summary": r.summary,
                        }
                        for r in rec.individual_reviews
                    ],
                    "aggregated_feedback": rec.aggregated_feedback,
                    "policy_content": rec.policy_content,
                }
                for rec in result.iterations
            ],
        }
