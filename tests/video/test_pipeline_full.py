"""Extended tests for video/pipeline.py to improve coverage."""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from video.pipeline import (
    run_video_pipeline,
    _check_dependencies,
    _discover_slides,
    SlideContext,
)


class TestDiscoverSlides:
    """Tests for _discover_slides."""

    def test_discovers_matching_slides_and_notes(self, tmp_path):
        """Should match slides to notes by prefix."""
        slides_dir = tmp_path / "slides"
        notes_dir = tmp_path / "notes"
        slides_dir.mkdir()
        notes_dir.mkdir()

        # Create test files
        (slides_dir / "01_intro.md").write_text("Intro content")
        (slides_dir / "02_memory.md").write_text("Memory content")
        (notes_dir / "note-01_intro-zh.md").write_text("Intro notes")
        (notes_dir / "note-02_memory-zh.md").write_text("Memory notes")

        result = _discover_slides(slides_dir, notes_dir)

        assert len(result) == 2
        assert result[0].slide_id == "01_intro"
        assert result[1].slide_id == "02_memory"

    def test_skips_slides_without_notes(self, tmp_path):
        """Should skip slides that have no matching notes."""
        slides_dir = tmp_path / "slides"
        notes_dir = tmp_path / "notes"
        slides_dir.mkdir()
        notes_dir.mkdir()

        (slides_dir / "01_intro.md").write_text("Content")
        (slides_dir / "02_orphan.md").write_text("Content")  # No note
        (notes_dir / "note-01_intro-zh.md").write_text("Notes")

        result = _discover_slides(slides_dir, notes_dir)

        assert len(result) == 1
        assert result[0].slide_id == "01_intro"

    def test_returns_empty_when_no_slides(self, tmp_path):
        """Should return empty list when no slides exist."""
        slides_dir = tmp_path / "slides"
        notes_dir = tmp_path / "notes"
        slides_dir.mkdir()
        notes_dir.mkdir()

        result = _discover_slides(slides_dir, notes_dir)

        assert len(result) == 0


class TestPipelineDisabled:
    """Tests for disabled pipeline scenarios."""

    def test_returns_none_when_disabled(self, tmp_path):
        """Should return None when video.enabled is False."""
        result = run_video_pipeline(
            project_root=tmp_path,
            config={"video": {"enabled": False}},
        )
        assert result is None

    def test_returns_none_when_config_missing(self, tmp_path):
        """Should return None when video config is missing."""
        result = run_video_pipeline(
            project_root=tmp_path,
            config={},
        )
        assert result is None

    def test_returns_none_when_slides_dir_missing(self, tmp_path):
        """Should return None when slides dir is missing."""
        result = run_video_pipeline(
            project_root=tmp_path,
            config={"video": {"enabled": True}},
        )
        assert result is None

    def test_returns_none_when_notes_dir_missing(self, tmp_path):
        """Should return None when notes dir is missing."""
        (tmp_path / "slides").mkdir()
        result = run_video_pipeline(
            project_root=tmp_path,
            config={"video": {"enabled": True}},
        )
        assert result is None


class TestSlideContext:
    """Tests for SlideContext dataclass."""

    def test_creates_context(self):
        """Should create SlideContext with all fields."""
        ctx = SlideContext(
            slide_id="01_test",
            content_path=Path("/slides/01_test.md"),
            notes_path=Path("/notes/note-01_test-zh.md"),
            clip_path=Path("/clips/01_test.mp4"),
        )
        assert ctx.slide_id == "01_test"
        assert ctx.content_path.name == "01_test.md"
        assert ctx.notes_path.name == "note-01_test-zh.md"
        assert ctx.clip_path.name == "01_test.mp4"


# Run with: pytest tests/video/test_pipeline_full.py -v
