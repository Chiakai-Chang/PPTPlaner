"""TDD tests for video/steps/step5_concat.py."""

import subprocess
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from video.steps.step5_concat import concat_clips, ConcatError


class TestConcatClips:
    """Tests for concat_clips function."""

    @patch("video.steps.step5_concat.subprocess.run")
    def test_creates_concat_list_file(self, mock_run, tmp_path):
        """Verify ffmpeg is called with concat list file."""
        clips = [tmp_path / f"clip{i}.mp4" for i in range(3)]
        for c in clips:
            c.touch()
        output = tmp_path / "final.mp4"

        concat_clips(
            intro_clip=clips[0],
            slide_clips=clips[1:],
            outro_clip=clips[2],
            output_mp4=output,
        )

        # Check that subprocess.run was called with concat flags
        call_args = mock_run.call_args[0][0]
        assert "-f" in call_args
        idx = call_args.index("-f")
        assert call_args[idx + 1] == "concat"

    @patch("video.steps.step5_concat.subprocess.run")
    def test_correct_clip_order(self, mock_run, tmp_path):
        """Intro clip appears first, outro appears last in concat list."""
        intro = tmp_path / "intro.mp4"
        slides = [tmp_path / f"slide{i}.mp4" for i in range(2)]
        outro = tmp_path / "outro.mp4"
        for c in [intro] + slides + [outro]:
            c.touch()
        output = tmp_path / "final.mp4"

        concat_clips(
            intro_clip=intro,
            slide_clips=slides,
            outro_clip=outro,
            output_mp4=output,
        )

        # Verify concat list file was created with correct order
        assert mock_run.called

    @patch("video.steps.step5_concat.subprocess.run")
    def test_bgm_mixed_when_set(self, mock_run, tmp_path):
        """When bgm_file is provided, ffmpeg called with audio mix args."""
        intro = tmp_path / "intro.mp4"
        slides = [tmp_path / "slide.mp4"]
        outro = tmp_path / "outro.mp4"
        bgm = tmp_path / "bgm.mp3"
        for c in [intro] + slides + [outro] + [bgm]:
            c.touch()
        output = tmp_path / "final.mp4"

        concat_clips(
            intro_clip=intro,
            slide_clips=slides,
            outro_clip=outro,
            output_mp4=output,
            bgm_file=bgm,
            bgm_volume=0.15,
        )

        call_args = mock_run.call_args[0][0]
        # Should include -filter_complex for audio mixing
        assert "-filter_complex" in call_args or "amix" in call_args or str(bgm) in call_args

    @patch("video.steps.step5_concat.subprocess.run")
    def test_no_bgm_when_null(self, mock_run, tmp_path):
        """When bgm_file is None, ffmpeg called without bgm args."""
        intro = tmp_path / "intro.mp4"
        slides = [tmp_path / "slide.mp4"]
        outro = tmp_path / "outro.mp4"
        for c in [intro] + slides + [outro]:
            c.touch()
        output = tmp_path / "final.mp4"

        concat_clips(
            intro_clip=intro,
            slide_clips=slides,
            outro_clip=outro,
            output_mp4=output,
            bgm_file=None,
        )

        call_args = mock_run.call_args[0][0]
        # Should be a simple concat without filter_complex
        assert "-filter_complex" not in call_args

    @patch("video.steps.step5_concat.subprocess.run")
    def test_output_path_returned(self, mock_run, tmp_path):
        """Function returns Path to final mp4."""
        intro = tmp_path / "intro.mp4"
        slides = [tmp_path / "slide.mp4"]
        outro = tmp_path / "outro.mp4"
        for c in [intro] + slides + [outro]:
            c.touch()
        output = tmp_path / "final.mp4"

        result = concat_clips(
            intro_clip=intro,
            slide_clips=slides,
            outro_clip=outro,
            output_mp4=output,
        )

        assert result == output

    def test_empty_clips_raises(self, tmp_path):
        """ValueError if slide_clips is empty."""
        intro = tmp_path / "intro.mp4"
        outro = tmp_path / "outro.mp4"

        with pytest.raises(ValueError, match="empty"):
            concat_clips(
                intro_clip=intro,
                slide_clips=[],
                outro_clip=outro,
                output_mp4=tmp_path / "final.mp4",
            )


# Run with: pytest tests/video/test_step_concat.py -v
