"""Tests for video/progress.py — TDD."""
from video.progress import (
    print_slide_start,
    print_step,
    print_skipped,
    print_eta,
    print_summary,
)


def test_print_slide_start(capsys):
    print_slide_start("slide_01", 1, 10)
    captured = capsys.readouterr()
    assert "[1/10]" in captured.out
    assert "slide_01" in captured.out


def test_print_step_ok(capsys):
    print_step("tts", "ok")
    captured = capsys.readouterr()
    assert "✓" in captured.out
    assert "tts" in captured.out


def test_print_step_failed(capsys):
    print_step("image", "failed", "timeout")
    captured = capsys.readouterr()
    assert "✗" in captured.out
    assert "image" in captured.out
    assert "timeout" in captured.out


def test_print_skipped(capsys):
    print_skipped("slide_02")
    captured = capsys.readouterr()
    assert "slide_02" in captured.out
    assert "skipping" in captured.out.lower() or "skip" in captured.out.lower()


def test_print_eta(capsys):
    print_eta(elapsed_sec=120, done=4, total=12)
    captured = capsys.readouterr()
    # Should contain ETA-like text
    assert "ETA" in captured.out or "eta" in captured.out or "remaining" in captured.out.lower()


def test_print_summary(capsys):
    print_summary(done=10, skipped=1, failed=1)
    captured = capsys.readouterr()
    assert "10" in captured.out
    assert "1" in captured.out  # skipped or failed count

