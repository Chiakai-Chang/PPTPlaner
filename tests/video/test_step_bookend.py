"""TDD tests for video/steps/step4_bookend.py."""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from video.steps.step4_bookend import (
    generate_bookend_clip,
    BookendError,
)


class TestRenderIntro:
    """Tests for intro/outro template rendering."""

    @patch("video.steps.step4_bookend.Jinja2Environment")
    def test_render_intro_calls_jinja(self, mock_env_cls, tmp_path):
        """Verify Jinja2 template rendered with intro vars."""
        tmpl = tmp_path / "intro.html"
        tmpl.write_text("{{ channel_name }}")
        mock_env = MagicMock()
        mock_template = MagicMock()
        mock_env_cls.return_value = mock_env
        mock_env.from_string.return_value = mock_template
        mock_template.render.return_value = "<html>...</html>"

        with patch("video.steps.step4_bookend.sync_playwright"), \
             patch("video.steps.step4_bookend.subprocess.run"):
            generate_bookend_clip(
                template_path=tmpl,
                template_vars={"channel_name": "TestChannel"},
                output_mp4=tmp_path / "outro.mp4",
                duration_sec=8,
            )

        mock_template.render.assert_called_once()
        assert "channel_name" in mock_template.render.call_args[1]


    @patch("video.steps.step4_bookend.Jinja2Environment")
    def test_render_outro_calls_jinja(self, mock_env_cls, tmp_path):
        """Verify Jinja2 template rendered with outro vars."""
        tmpl = tmp_path / "outro.html"
        tmpl.write_text("{{ cta_text }}")
        mock_env = MagicMock()
        mock_template = MagicMock()
        mock_env_cls.return_value = mock_env
        mock_env.from_string.return_value = mock_template
        mock_template.render.return_value = "<html>...</html>"

        with patch("video.steps.step4_bookend.sync_playwright"), \
             patch("video.steps.step4_bookend.subprocess.run"):
            generate_bookend_clip(
                template_path=tmpl,
                template_vars={"cta_text": "Subscribe!"},
                output_mp4=tmp_path / "outro.mp4",
                duration_sec=12,
            )

        mock_template.render.assert_called_once()


class TestPlaywrightScreenshot:
    """Tests for playwright screenshot generation."""

    @patch("video.steps.step4_bookend.sync_playwright")
    @patch("video.steps.step4_bookend.Jinja2Environment")
    def test_playwright_screenshot_called(self, mock_env, mock_pw, tmp_path):
        """Verify page.screenshot() is called."""
        tmpl = tmp_path / "test.html"
        tmpl.write_text("<html></html>")
        mock_env.return_value.from_string.return_value.render.return_value = "<html></html>"
        mock_pw_instance = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_pw.return_value.__enter__.return_value = mock_pw_instance
        mock_pw_instance.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        with patch("video.steps.step4_bookend.subprocess.run"):
            generate_bookend_clip(
                template_path=tmpl,
                template_vars={},
                output_mp4=Path("/tmp/test.mp4"),
                duration_sec=5,
            )

        mock_page.goto.assert_called_once()
        mock_page.screenshot.assert_called_once()


class TestOutputClip:
    """Tests for output clip generation."""

    @patch("video.steps.step4_bookend.sync_playwright")
    @patch("video.steps.step4_bookend.subprocess.run")
    @patch("video.steps.step4_bookend.Jinja2Environment")
    def test_output_clip_produced(self, mock_env, mock_run, mock_pw, tmp_path):
        """With mocked playwright+ffmpeg, verify output mp4 path returned."""
        tmpl = tmp_path / "test.html"
        tmpl.write_text("<html></html>")
        mock_env.return_value.from_string.return_value.render.return_value = "<html></html>"
        mock_pw_instance = MagicMock()
        mock_browser = MagicMock()
        mock_pw.return_value.__enter__.return_value = mock_pw_instance
        mock_pw_instance.chromium.launch.return_value = mock_browser

        output = tmp_path / "output.mp4"
        result = generate_bookend_clip(
            template_path=tmpl,
            template_vars={},
            output_mp4=output,
            duration_sec=5,
        )

        assert result == output


class TestMissingTemplate:
    """Tests for error handling."""

    def test_missing_template_raises(self, tmp_path):
        """FileNotFoundError if template file does not exist."""
        missing = tmp_path / "nonexistent.html"

        with pytest.raises(FileNotFoundError):
            generate_bookend_clip(
                template_path=missing,
                template_vars={},
                output_mp4=Path("/tmp/out.mp4"),
                duration_sec=5,
            )


# Run with: pytest tests/video/test_step_bookend.py -v
