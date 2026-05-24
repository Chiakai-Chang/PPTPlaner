"""Tests for Config Validation."""

from pathlib import Path
from unittest import mock
import pytest

from video.config_validation import (
    validate_video_config,
    VideoConfigError,
)


class TestValidateVideoConfig:
    """Test suite for validate_video_config."""

    def test_valid_minimal_config(self):
        """Test that minimal valid config passes."""
        config = {
            "enabled": True,
            "tts": {"provider": "edge-tts"},
            "image": {"provider": "none"},
        }

        result = validate_video_config(config)
        assert result is True  # Returns True on success

    def test_valid_fish_speech_config(self):
        """Test that Fish Speech config passes."""
        config = {
            "enabled": True,
            "tts": {
                "provider": "fish-speech",
                "fish_speech_url": "http://localhost:8080",
            },
            "image": {
                "provider": "comfyui",
                "comfyui_url": "http://localhost:8188",
            },
        }

        result = validate_video_config(config)
        assert result is True

    def test_invalid_provider(self):
        """Test that invalid provider raises error."""
        config = {
            "enabled": True,
            "tts": {"provider": "invalid-provider"},
            "image": {"provider": "none"},
        }

        with pytest.raises(VideoConfigError) as exc_info:
            validate_video_config(config)

        assert "invalid-provider" in str(exc_info.value)

    def test_missing_required_field(self):
        """Test that missing required field raises error."""
        config = {
            "enabled": True,
            # Missing tts
            "image": {"provider": "none"},
        }

        with pytest.raises(VideoConfigError):
            validate_video_config(config)

    def test_fish_speech_requires_url(self):
        """Test that Fish Speech requires URL."""
        config = {
            "enabled": True,
            "tts": {"provider": "fish-speech"},
            "image": {"provider": "none"},
        }

        with pytest.raises(VideoConfigError) as exc_info:
            validate_video_config(config)

        assert "fish_speech_url" in str(exc_info.value)

    def test_comfyui_requires_url(self):
        """Test that ComfyUI requires URL."""
        config = {
            "enabled": True,
            "tts": {"provider": "edge-tts"},
            "image": {"provider": "comfyui"},
        }

        with pytest.raises(VideoConfigError) as exc_info:
            validate_video_config(config)

        assert "comfyui_url" in str(exc_info.value)

    def test_runninghub_requires_api_key(self):
        """Test that RunningHub requires API key."""
        config = {
            "enabled": True,
            "tts": {"provider": "edge-tts"},
            "image": {
                "provider": "runninghub",
                "runninghub_workflow": "test",
            },
        }

        with pytest.raises(VideoConfigError) as exc_info:
            validate_video_config(config)

        assert "runninghub_api_key" in str(exc_info.value)
