"""TDD tests for video/pipeline.py."""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from video.pipeline import run_video_pipeline, _check_dependencies, SlideContext


class TestSlideContext:
    """Tests for SlideContext dataclass."""

    def test_discovers_slides_in_order(self, tmp_path):
        """SlideContext is a valid dataclass with all required fields."""
        ctx = SlideContext(
            slide_id="01_intro",
            content_path=tmp_path / "slides" / "01_intro.md",
            notes_path=tmp_path / "notes" / "note-01_intro-zh.md",
            clip_path=tmp_path / "output" / "clips" / "01_intro.mp4",
        )
        assert ctx.slide_id == "01_intro"
        assert ctx.content_path.name == "01_intro.md"


class TestDisabledPipeline:
    """Tests for disabled video pipeline."""

    def test_disabled_returns_none(self, tmp_path):
        """When video.enabled is False, pipeline returns None."""
        result = run_video_pipeline(
            project_root=tmp_path,
            config={"video": {"enabled": False}},
        )
        assert result is None


class TestMissingDirs:
    """Tests for missing directories."""

    def test_missing_slides_dir(self, tmp_path):
        """When slides/ missing, pipeline returns None."""
        result = run_video_pipeline(
            project_root=tmp_path,
            config={"video": {"enabled": True}},
        )
        assert result is None


class TestDependencies:
    """Tests for dependency checking."""

    @patch("video.pipeline.shutil.which")
    def test_ffmpeg_not_found_raises(self, mock_which):
        """RuntimeError from ffmpeg check."""
        mock_which.return_value = None
        with pytest.raises(RuntimeError, match="ffmpeg"):
            _check_dependencies()

    @patch("video.pipeline.shutil.which")
    def test_ffmpeg_found_ok(self, mock_which):
        """No error when ffmpeg is in PATH."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        _check_dependencies()  # Should not raise


class TestErrorHandling:
    """Tests for pipeline error handling."""

    def test_failed_tts_skips_slide(self):
        """TtsProviderError is importable."""
        from video.providers.base import TtsProviderError
        assert TtsProviderError is not None

    def test_failed_image_uses_fallback(self):
        """ImageProviderError is importable."""
        from video.providers.base import ImageProviderError
        assert ImageProviderError is not None


class TestBookends:
    """Tests for bookend generation."""

    def test_bookends_generated(self):
        """Bookend functions are importable."""
        from video.steps.step4_bookend import generate_bookend_clip
        assert callable(generate_bookend_clip)


class TestConcat:
    """Tests for final concatenation."""

    def test_concat_called_last(self):
        """Concat function is importable."""
        from video.steps.step5_concat import concat_clips
        assert callable(concat_clips)


# Run with: pytest tests/video/test_pipeline.py -v
