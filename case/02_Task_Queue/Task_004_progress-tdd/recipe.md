# Recipe: Task_004 — TDD: progress.py

## 1. Objective
Implement video/progress.py: prints per-step progress to stdout in a human-readable format. A user running overnight must be able to glance at the log and know where the pipeline is.

## 2. Input Sources
- case/00_Constitution/core.md
- video/checkpoint.py (Task_003 output) — import Checkpoint for type hints

## 3. Output Specification

Write tests/video/test_progress.py FIRST with these test cases:
- test_print_slide_start: print_slide_start("slide_01", 1, 10) outputs "[1/10] slide_01 —"
- test_print_step_ok: print_step("tts", "ok") outputs "  ✓ tts"
- test_print_step_failed: print_step("image", "failed", "timeout") outputs "  ✗ image: timeout"
- test_print_skipped: print_skipped("slide_02") outputs "⏭  slide_02 — already complete, skipping"
- test_print_eta: print_eta(elapsed_sec=120, done=4, total=12) outputs ETA string
- test_print_summary: print_summary(done=10, skipped=1, failed=1) outputs summary line

Then implement video/progress.py with functions (not a class):
- print_slide_start(slide_id: str, index: int, total: int) -> None
- print_step(step_name: str, status: str, error: str = "") -> None
- print_skipped(slide_id: str) -> None
- print_eta(elapsed_sec: float, done: int, total: int) -> None
- print_summary(done: int, skipped: int, failed: int) -> None

All output goes to sys.stdout with flush=True for real-time display.

## 4. Local Definition of Done
- [ ] tests/video/test_progress.py with all 6 test cases passing
- [ ] video/progress.py with all 5 functions
- [ ] Output is captured correctly in tests using capsys (pytest fixture)
- [ ] Unicode symbols (✓ ✗ ⏭) render without error on Windows (UTF-8 stdout)

## 5. Constraints
- No logging module — plain print() only
- No color codes (Windows terminal compatibility)
- Functions must be importable without side effects

## 6. Escalation Trigger
Escalate if stdout UTF-8 encoding cannot be guaranteed on Windows environment.
