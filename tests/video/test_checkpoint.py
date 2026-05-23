"""Tests for video/checkpoint.py — TDD."""
import json
from pathlib import Path

import pytest


@pytest.fixture
def run_dir(tmp_path):
    return tmp_path / "video_output"


@pytest.fixture
def session_id():
    return "test_session_001"


def import_checkpoint():
    from video.checkpoint import Checkpoint
    return Checkpoint


def test_create_new_session(run_dir, session_id):
    """new Checkpoint creates video_progress.json with empty slides dict."""
    Checkpoint = import_checkpoint()
    cp = Checkpoint(run_dir, session_id)
    assert (run_dir / "video_progress.json").exists()
    data = json.loads((run_dir / "video_progress.json").read_text())
    assert data["session_id"] == session_id
    assert data["slides"] == {}


def test_mark_step_done(run_dir, session_id):
    """mark('slide_01', 'tts', 'ok') persists to checkpoint."""
    Checkpoint = import_checkpoint()
    cp = Checkpoint(run_dir, session_id)
    cp.mark("slide_01", "tts", "ok")
    data = json.loads((run_dir / "video_progress.json").read_text())
    assert data["slides"]["slide_01"]["tts"] == "ok"


def test_mark_step_failed(run_dir, session_id):
    """mark('slide_01', 'image', 'failed', 'timeout') adds to errors list."""
    Checkpoint = import_checkpoint()
    cp = Checkpoint(run_dir, session_id)
    cp.mark("slide_01", "image", "failed", "timeout")
    data = json.loads((run_dir / "video_progress.json").read_text())
    assert data["slides"]["slide_01"]["image"] == "failed"
    assert len(data["errors"]) == 1
    assert data["errors"][0]["slide"] == "slide_01"
    assert data["errors"][0]["step"] == "image"
    assert data["errors"][0]["error"] == "timeout"


def test_is_done_true(run_dir, session_id):
    """After marking clip ok, is_done returns True."""
    Checkpoint = import_checkpoint()
    cp = Checkpoint(run_dir, session_id)
    cp.mark("slide_01", "clip", "ok")
    assert cp.is_done("slide_01", "clip") is True


def test_is_done_false(run_dir, session_id):
    """For unmarked step, is_done returns False."""
    Checkpoint = import_checkpoint()
    cp = Checkpoint(run_dir, session_id)
    assert cp.is_done("slide_01", "clip") is False
    assert cp.is_done("slide_99", "tts") is False


def test_resume_skips_completed(run_dir, session_id):
    """Loading existing checkpoint preserves completed steps."""
    Checkpoint = import_checkpoint()
    cp = Checkpoint(run_dir, session_id)
    cp.mark("slide_01", "clip", "ok")
    cp.mark("slide_02", "tts", "ok")

    # Load existing checkpoint
    cp2 = Checkpoint.load_or_create(run_dir, session_id)
    assert cp2.is_done("slide_01", "clip") is True
    assert cp2.is_done("slide_02", "tts") is True
    assert cp2.is_done("slide_02", "clip") is False


def test_concurrent_write_safety(run_dir, session_id):
    """Multiple mark() calls persist correctly without data loss."""
    Checkpoint = import_checkpoint()
    cp = Checkpoint(run_dir, session_id)
    for i in range(10):
        cp.mark(f"slide_{i:02d}", "tts", "ok")
        cp.mark(f"slide_{i:02d}", "image", "ok")
        cp.mark(f"slide_{i:02d}", "clip", "ok")
    data = json.loads((run_dir / "video_progress.json").read_text())
    assert len(data["slides"]) == 10
    for i in range(10):
        slide_id = f"slide_{i:02d}"
        assert data["slides"][slide_id]["tts"] == "ok"
        assert data["slides"][slide_id]["image"] == "ok"
        assert data["slides"][slide_id]["clip"] == "ok"


def test_session_id_stored(run_dir, session_id):
    """Checkpoint JSON has session_id field matching constructor arg."""
    Checkpoint = import_checkpoint()
    cp = Checkpoint(run_dir, session_id)
    data = json.loads((run_dir / "video_progress.json").read_text())
    assert data["session_id"] == session_id


def test_mark_failed(run_dir, session_id):
    """mark_failed records a complete slide failure."""
    Checkpoint = import_checkpoint()
    cp = Checkpoint(run_dir, session_id)
    cp.mark_failed("slide_03", "TTS provider error")
    data = json.loads((run_dir / "video_progress.json").read_text())
    assert len(data["errors"]) == 1
    assert data["errors"][0]["slide"] == "slide_03"


def test_intro_outro_fields(run_dir, session_id):
    """Intro and outro fields start as 'pending'."""
    Checkpoint = import_checkpoint()
    Checkpoint(run_dir, session_id)
    data = json.loads((run_dir / "video_progress.json").read_text())
    assert data["intro"] == "pending"
    assert data["outro"] == "pending"
    assert data["final_concat"] == "pending"


def test_timestamps_present(run_dir, session_id):
    """started_at and last_updated timestamps are ISO 8601."""
    from datetime import datetime
    Checkpoint = import_checkpoint()
    Checkpoint(run_dir, session_id)
    data = json.loads((run_dir / "video_progress.json").read_text())
    # Should parse without error
    datetime.fromisoformat(data["started_at"])
    datetime.fromisoformat(data["last_updated"])

