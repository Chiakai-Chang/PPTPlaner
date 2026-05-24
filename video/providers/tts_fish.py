"""Fish Speech TTS Provider.

Local high-quality TTS using Fish Speech HTTP API.
Supports voice cloning and multiple languages.
"""

from __future__ import annotations

import logging
from pathlib import Path

import httpx

from video.providers.base import TtsProvider, TtsProviderError

logger = logging.getLogger(__name__)


class FishSpeechProvider(TtsProvider):
    """Fish Speech TTS provider."""

    def __init__(
        self,
        url: str = "http://localhost:8080",
        model: str = "fish-speech-1.4",
        voice: str = "default",
        speed: float = 1.0,
    ) -> None:
        """
        Initialize Fish Speech provider.

        Args:
            url: Fish Speech API URL
            model: Model name
            voice: Voice ID (use 'default' or custom voice ID)
            speed: Speech speed multiplier (0.5-2.0)
        """
        self.url = url.rstrip("/")
        self.model = model
        self.voice = voice
        self.speed = max(0.5, min(2.0, speed))
        self._client = httpx.Client(timeout=120)

    @property
    def name(self) -> str:
        return "fish-speech"

    def generate(self, text: str, output_wav: Path, language: str = "zh-TW") -> None:
        """
        Synthesize speech using Fish Speech.

        Args:
            text: Text to synthesize
            output_wav: Output WAV file path
            language: Language code (default: zh-TW)

        Raises:
            TtsProviderError: If synthesis fails
        """
        if not text or not text.strip():
            raise TtsProviderError("Empty text provided")

        output_wav.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "model": self.model,
            "input": text,
            "voice": self.voice,
            "response_format": "wav",
            "speed": self.speed,
        }

        try:
            response = self._client.post(
                f"{self.url}/v1/audio/speech",
                json=payload,
            )
            response.raise_for_status()

            # Write audio data
            output_wav.write_bytes(response.content)
            logger.info(f"Fish Speech generated: {output_wav} ({len(response.content)} bytes)")

        except httpx.ConnectError as e:
            raise TtsProviderError(
                f"Cannot connect to Fish Speech at {self.url}. "
                f"Is the server running? Run: docker compose -f docker-compose.video.yml up -d"
            ) from e
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response.content else ""
            raise TtsProviderError(
                f"Fish Speech API error {e.response.status_code}: {error_detail}"
            ) from e
        except Exception as e:
            raise TtsProviderError(f"Fish Speech synthesis failed: {e}") from e

    def close(self) -> None:
        """Close HTTP client."""
        self._client.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass
