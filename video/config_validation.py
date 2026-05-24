"""Config Validation for Video Pipeline.

Validates config.yaml settings before running the video pipeline.
Raises VideoConfigError with helpful messages for invalid configurations.
"""

from __future__ import annotations

from video.providers.base import TtsProviderError


class VideoConfigError(Exception):
    """Raised when video configuration is invalid."""


# Valid provider names
VALID_TTS_PROVIDERS = ["edge-tts", "fish-speech"]
VALID_IMAGE_PROVIDERS = ["none", "comfyui", "runninghub"]

# Required fields per provider
PROVIDER_REQUIREMENTS = {
    "tts": {
        "fish-speech": ["fish_speech_url"],
    },
    "image": {
        "comfyui": ["comfyui_url"],
        "runninghub": ["runninghub_api_key", "runninghub_workflow"],
    },
}


def validate_video_config(config: dict) -> bool:
    """
    Validate video configuration.

    Args:
        config: Video section of config.yaml

    Returns:
        True if valid

    Raises:
        VideoConfigError: If configuration is invalid
    """
    if not config:
        raise VideoConfigError("Video configuration is empty")

    # Check required sections
    if "tts" not in config:
        raise VideoConfigError(
            "Missing 'tts' section in video config. "
            "Example: video.tts.provider: 'edge-tts'"
        )

    if "image" not in config:
        raise VideoConfigError(
            "Missing 'image' section in video config. "
            "Example: video.image.provider: 'none'"
        )

    # Validate TTS provider
    tts_config = config["tts"]
    tts_provider = tts_config.get("provider", "edge-tts")

    if tts_provider not in VALID_TTS_PROVIDERS:
        raise VideoConfigError(
            f"Invalid TTS provider: '{tts_provider}'. "
            f"Valid options: {VALID_TTS_PROVIDERS}"
        )

    # Validate TTS provider requirements
    _validate_provider_requirements(
        "tts", tts_provider, tts_config
    )

    # Validate image provider
    image_config = config["image"]
    image_provider = image_config.get("provider", "none")

    if image_provider not in VALID_IMAGE_PROVIDERS:
        raise VideoConfigError(
            f"Invalid image provider: '{image_provider}'. "
            f"Valid options: {VALID_IMAGE_PROVIDERS}"
        )

    # Validate image provider requirements
    _validate_provider_requirements(
        "image", image_provider, image_config
    )

    return True


def _validate_provider_requirements(
    section: str,
    provider: str,
    config: dict,
) -> None:
    """
    Validate provider-specific requirements.

    Args:
        section: Config section ('tts' or 'image')
        provider: Provider name
        config: Section configuration

    Raises:
        VideoConfigError: If requirements not met
    """
    requirements = PROVIDER_REQUIREMENTS.get(section, {}).get(provider, [])

    for field in requirements:
        if field not in config:
            raise VideoConfigError(
                f"Missing required field '{field}' for {section} provider '{provider}'. "
                f"Add to config.yaml: video.{section}.{field}: '<value>'"
            )
