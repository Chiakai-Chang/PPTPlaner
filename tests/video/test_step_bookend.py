"""TDD tests for video/steps/step4_bookend.py."""

from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open, ANY

import pytest

from video.steps.step4_bookend import (
    generate_bookend_clip,
    BookendError,
)


class TestGenerateBookend:
    """Tests for bookend generation with TTS + PIL + FFmpeg."""

    @patch("video.steps.step4_bookend.compose_clip")
    @patch("video.steps.step4_bookend.NoneImageProvider")
    @patch("video.steps.step4_bookend.EdgeTtsProvider")
    def test_bookend_calls_tts(self, mock_tts_cls, mock_img_cls, mock_compose, tmp_path):
        """Verify TTS is called with correct text."""
        mock_tts = MagicMock()
        mock_tts_cls.return_value = mock_tts
        mock_img = MagicMock()
        mock_img_cls.return_value = mock_img

        output = tmp_path / "intro.mp4"
        output.parent.mkdir(parents=True, exist_ok=True)
        result = generate_bookend_clip(
            text="Hello world",
            title="My Channel",
            output_mp4=output,
            duration_sec=8,
        )

        mock_tts.synthesize.assert_called_once_with("Hello world", ANY)
        assert result == output

    @patch("video.steps.step4_bookend.compose_clip")
    @patch("video.steps.step4_bookend.NoneImageProvider")
    @patch("video.steps.step4_bookend.EdgeTtsProvider")
    def test_bookend_calls_image(self, mock_tts_cls, mock_img_cls, mock_compose, tmp_path):
        """Verify image provider is called with title."""
        mock_tts = MagicMock()
        mock_tts_cls.return_value = mock_tts
        mock_img = MagicMock()
        mock_img_cls.return_value = mock_img

        output = tmp_path / "outro.mp4"
        output.parent.mkdir(parents=True, exist_ok=True)
        generate_bookend_clip(
            text="Thanks for watching",
            title="My Channel",
            output_mp4=output,
            duration_sec=12,
        )

        mock_img.render.assert_called_once()

    @patch("video.steps.step4_bookend.compose_clip")
    @patch("video.steps.step4_bookend.NoneImageProvider")
    @patch("video.steps.step4_bookend.EdgeTtsProvider")
    def test_bookend_returns_output_path(self, mock_tts_cls, mock_img_cls, mock_compose, tmp_path):
        """Verify output path is returned."""
        mock_tts_cls.return_value = MagicMock()
        mock_img_cls.return_value = MagicMock()

        output = tmp_path / "intro.mp4"
        output.parent.mkdir(parents=True, exist_ok=True)
        result = generate_bookend_clip(
            text="Intro text",
            title="Title",
            output_mp4=output,
        )

        assert result == output


class TestBookendError:
    """Tests for error handling."""

    @patch("video.steps.step4_bookend.EdgeTtsProvider")
    def test_tts_failure_raises_bookend_error(self, mock_tts_cls, tmp_path):
        """TTS failure raises BookendError."""
        mock_tts = MagicMock()
        mock_tts.synthesize.side_effect = Exception("TTS failed")
        mock_tts_cls.return_value = mock_tts

        with pytest.raises(BookendError, match="TTS failed"):
            generate_bookend_clip(
                text="test",
                title="test",
                output_mp4=tmp_path / "test.mp4",
            )


# Run with: pytest tests/video/test_step_bookend.py -v
