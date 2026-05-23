# Recipe: Task_003 — TDD: checkpoint.py

## 1. Objective
Implement video/checkpoint.py using TDD. This module persists pipeline progress to disk (video_progress.json) so interrupted runs can resume without reprocessing completed slides.

## 2. Input Sources
- case/00_Constitution/core.md
- case/01_Roadmap/roadmap.md — output file map
- docs/research/VIDEO_PIPELINE_SPEC.md — Section 4 (checkpoint JSON schema)
- video/providers/base.py — must exist (Task_001 output)

## 3. Output Specification

Write tests/video/test_checkpoint.py FIRST with these test cases:
- test_create_new_session: new Checkpoint(run_dir, session_id) creates video_progress.json with empty slides dict
- test_mark_step_done: mark("slide_01", "tts", "ok") → checkpoint["slides"]["slide_01"]["tts"] == "ok"
- test_mark_step_failed: mark("slide_01", "image", "failed", "timeout") → errors list contains entry
- test_is_done_true: after marking clip ok, is_done("slide_01", "clip") returns True
- test_is_done_false: for unmarked step, is_done returns False
- test_resume_skips_completed: loading existing checkpoint with slide_01 clip ok → is_done("slide_01","clip") True
- test_concurrent_write_safety: multiple mark() calls persist correctly (no data loss)
- test_session_id_stored: checkpoint JSON has session_id field matching constructor arg

Then implement video/checkpoint.py:

class Checkpoint:
    def __init__(self, run_dir: Path, session_id: str) -> None
    def is_done(self, slide_id: str, step: str) -> bool
    def mark(self, slide_id: str, step: str, status: str, error: str = "") -> None
    def mark_failed(self, slide_id: str, error: str) -> None
    def load_or_create(cls, run_dir: Path, session_id: str) -> "Checkpoint"  # classmethod

JSON schema (video_progress.json):
{
  "session_id": "str",
  "slides": {"slide_01": {"tts": "ok", "image": "failed", "clip": "ok"}},
  "errors": [{"slide": "slide_01", "step": "image", "error": "str", "ts": "ISO8601"}],
  "intro": "pending|ok|failed",
  "outro": "pending|ok|failed",
  "final_concat": "pending|ok|failed",
  "started_at": "ISO8601",
  "last_updated": "ISO8601"
}

## 4. Local Definition of Done
- [ ] tests/video/test_checkpoint.py exists with all 8 test cases
- [ ] pytest tests/video/test_checkpoint.py passes (all green)
- [ ] video/checkpoint.py exists with Checkpoint class
- [ ] Coverage >= 90% for checkpoint.py
- [ ] All file writes use pathlib.Path and UTF-8 encoding

## 5. Constraints
- Do NOT use sqlite or any database — JSON file only
- Write JSON atomically (write to .tmp then rename) to avoid corruption on interrupt
- All timestamps in ISO 8601 format with timezone

## 6. Escalation Trigger
Escalate if Task_001 output (video/providers/base.py) does not exist when this task begins.
