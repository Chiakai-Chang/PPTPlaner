"""TDD tests for video/steps/step3_clip.py."""

import subprocess
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from video.steps.step3_clip import compose_clip, ClipCompositionError


class TestComposeClip:
    """Tests for compose_clip function."""

    @patch("video.steps.step3_clip.subprocess.run")
    def test_compose_calls_ffmpeg(self, mock_run):
        """Verify ffmpeg is called with correct arguments."""
        image = Path("/tmp/test.png")
        audio = Path("/tmp/test.wav")
        output = Path("/tmp/test.mp4")

        compose_clip(image, audio, output, fps=30)

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "-loop" in call_args
        assert "1" in call_args
        assert str(image) in call_args
        assert str(audio) in call_args
        assert "-c:v" in call_args
        assert "libx264" in call_args
        assert "-c:a" in call_args
        assert "aac" in call_args
        assert "-shortest" in call_args
        assert "-y" in call_args
        assert str(output) in call_args

    @patch("video.steps.step3_clip.subprocess.run")
    def test_output_path_returned(self, mock_run):
        """compose_clip returns the output path."""
        image = Path("/tmp/test.png")
        audio = Path("/tmp/test.wav")
        output = Path("/tmp/test.mp4")

        result = compose_clip(image, audio, output)

        assert result == output

    @patch("video.steps.step3_clip.shutil.which")
    def test_ffmpeg_not_found_raises_runtime_error(self, mock_which):
        """Raise RuntimeError if ffmpeg is not in PATH."""
        mock_which.return_value = None

        with pytest.raises(RuntimeError, match="ffmpeg not found"):
            compose_clip(Path("img.png"), Path("audio.wav"), Path("out.mp4"))

    @patch("video.steps.step3_clip.shutil.which")
    @patch("video.steps.step3_clip.subprocess.run")
    def test_ffmpeg_failure_raises(self, mock_run, mock_which):
        """Raise ClipCompositionError when ffmpeg fails."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        mock_run.side_effect = subprocess.CalledProcessError(1, "ffmpeg")

        with pytest.raises(ClipCompositionError):
            compose_clip(Path("img.png"), Path("audio.wav"), Path("out.mp4"))

    @patch("video.steps.step3_clip.shutil.which")
    @patch("video.steps.step3_clip.subprocess.run")
    def test_output_dir_created(self, mock_run, mock_which, tmp_path):
        """Output directory is created if it doesn't exist."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        output = tmp_path / "subdir" / "test.mp4"

        compose_clip(Path("img.png"), Path("audio.wav"), output)

        assert output.parent.exists()
        assert output.parent.is_dir()


# Run with: pytest tests/video/test_step_clip.py -v
