"""Progress — Human-readable CLI output for the video pipeline."""
import sys
from typing import TextIO


def print_slide_start(slide_id: str, index: int, total: int) -> None:
    """Print slide start line: [1/10] slide_01 —"""
    print(f"[{index}/{total}] {slide_id} — ", end="", flush=True, file=sys.stdout)


def print_step(step_name: str, status: str, error: str = "") -> None:
    """Print step result:  ✓ tts  or  ✗ image: timeout"""
    symbol = "✓" if status == "ok" else "✗"
    if status == "failed" and error:
        print(f"  {symbol} {step_name}: {error}", flush=True, file=sys.stdout)
    else:
        print(f"  {symbol} {step_name}", flush=True, file=sys.stdout)


def print_skipped(slide_id: str) -> None:
    """Print skip line: ⏭  slide_02 — already complete, skipping"""
    print(f"⏭  {slide_id} — already complete, skipping", flush=True, file=sys.stdout)


def print_eta(elapsed_sec: float, done: int, total: int) -> None:
    """Print ETA based on elapsed time and progress."""
    remaining = total - done
    if remaining <= 0 or elapsed_sec <= 0:
        print("  ETA: ~0s remaining", flush=True, file=sys.stdout)
        return
    per_slide = elapsed_sec / done if done > 0 else 0
    eta_sec = per_slide * remaining
    if eta_sec < 60:
        print(f"  ETA: ~{eta_sec:.0f}s remaining", flush=True, file=sys.stdout)
    else:
        print(f"  ETA: ~{eta_sec / 60:.0f}m remaining", flush=True, file=sys.stdout)


def print_summary(done: int, skipped: int, failed: int) -> None:
    """Print final summary line."""
    print(
        f"Summary: {done} done, {skipped} skipped, {failed} failed",
        flush=True,
        file=sys.stdout,
    )

