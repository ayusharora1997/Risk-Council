"""
AuditTrail — persists every iteration and the final session result as JSON.

Files are stored under data/sessions/<session_id>/:
  data/sessions/<session_id>/config.json
  data/sessions/<session_id>/iteration_001.json
  data/sessions/<session_id>/iteration_002.json
  ...
  data/sessions/<session_id>/result.json
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from models.schemas import IterationRecord, SessionConfig, SessionResult

_DATA_ROOT = Path(__file__).resolve().parent.parent / "data" / "sessions"


def _json_default(obj: Any) -> Any:
    """JSON serialiser for types not handled natively."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "model_dump"):  # Pydantic v2
        return obj.model_dump()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serialisable")


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, default=_json_default, ensure_ascii=False)


class AuditTrail:
    """Append-only storage for session configs, iteration records, and results."""

    def __init__(self, data_root: Path = _DATA_ROOT) -> None:
        self.data_root = data_root

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def save_config(self, config: SessionConfig) -> Path:
        """Persist the session configuration at session start."""
        path = self._session_dir(config.session_id) / "config.json"
        _write_json(path, config.model_dump())
        return path

    def save_iteration(self, session_id: str, record: IterationRecord) -> Path:
        """Append a single iteration record to its session directory."""
        filename = f"iteration_{record.iteration_number:03d}.json"
        path = self._session_dir(session_id) / filename
        _write_json(path, record.model_dump())
        return path

    def save_session_result(self, result: SessionResult) -> Path:
        """Write the final consolidated result for a session."""
        path = self._session_dir(result.session_id) / "result.json"
        _write_json(path, result.model_dump())
        return path

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def load_session_result(self, session_id: str) -> dict:
        """Load and return the result JSON for a completed session."""
        path = self._session_dir(session_id) / "result.json"
        if not path.exists():
            raise FileNotFoundError(f"No result found for session '{session_id}'")
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)

    def list_sessions(self) -> list[str]:
        """Return a list of all session IDs stored on disk."""
        if not self.data_root.exists():
            return []
        return sorted(
            d.name
            for d in self.data_root.iterdir()
            if d.is_dir()
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _session_dir(self, session_id: str) -> Path:
        return self.data_root / session_id
