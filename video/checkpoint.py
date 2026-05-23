"""Checkpoint — Pipeline Progress Persistence.

Writes to video_progress.json for resume-capable pipeline execution.
All writes are atomic (write to .tmp, then rename).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_data(session_id: str) -> dict:
    return {
        "session_id": session_id,
        "slides": {},
        "intro": "pending",
        "outro": "pending",
        "final_concat": "pending",
        "started_at": _iso_now(),
        "last_updated": _iso_now(),
        "errors": [],
    }


class Checkpoint:
    """Persist pipeline progress to video_progress.json."""

    def __init__(self, run_dir: Path, session_id: str) -> None:
        self.run_dir = Path(run_dir)
        self.session_id = session_id
        self.path = self.run_dir / "video_progress.json"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write(_default_data(session_id))

    @classmethod
    def load_or_create(cls, run_dir: Path, session_id: str) -> "Checkpoint":
        """Load existing checkpoint or create a new one."""
        return cls(run_dir, session_id)

    def _read(self) -> dict:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, data: dict) -> None:
        data["last_updated"] = _iso_now()
        tmp_path = self.path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(self.path)

    def is_done(self, slide_id: str, step: str) -> bool:
        """Return True if the given step for this slide is marked 'ok'."""
        data = self._read()
        slide = data["slides"].get(slide_id, {})
        return slide.get(step) == "ok"

    def mark(
        self,
        slide_id: str,
        step: str,
        status: str,
        error: str = "",
    ) -> None:
        """Mark a slide step as ok/failed/pending."""
        data = self._read()
        if slide_id not in data["slides"]:
            data["slides"][slide_id] = {}
        data["slides"][slide_id][step] = status
        if status == "failed" and error:
            data["errors"].append({
                "slide": slide_id,
                "step": step,
                "error": error,
                "ts": _iso_now(),
            })
        self._write(data)

    def mark_failed(self, slide_id: str, error: str) -> None:
        """Record a complete slide failure in the errors list."""
        data = self._read()
        data["errors"].append({
            "slide": slide_id,
            "step": "pipeline",
            "error": error,
            "ts": _iso_now(),
        })
        self._write(data)

    def mark_bookend(self, kind: str, status: str, error: str = "") -> None:
        """Mark intro/outro/final_concat status."""
        data = self._read()
        data[kind] = status
        if status == "failed" and error:
            data["errors"].append({
                "slide": "",
                "step": kind,
                "error": error,
                "ts": _iso_now(),
            })
        self._write(data)

