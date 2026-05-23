"""Edge-TTS Provider — Text-to-Speech via Microsoft Edge."""
from __future__ import annotations

from pathlib import Path

try:
    import edge_tts
except ImportError as e:
    raise ImportError(
        "edge-tts not installed. Run: pip install edge-tts"
    ) from e

from video.providers.base import TtsProvider, TtsProviderError


class EdgeTtsProvider(TtsProvider):
    """Edge-TTS provider implementing TtsProvider ABC."""

    def __init__(
        self,
        voice: str = "zh-TW-HsiaoChenNeural",
        speed: str = "+0%",
    ) -> None:
        self.voice = voice
        self.speed = speed

    def name(self) -> str:
        return "edge-tts"

    def generate(
        self,
        text: str,
        output_wav: Path,
        language: str = "zh-TW",
    ) -> None:
        """Synthesize text to WAV using Edge-TTS."""
        if not text or not text.strip():
            raise ValueError("Text must not be empty or whitespace-only")

        output_wav.parent.mkdir(parents=True, exist_ok=True)

        try:
            communicate = edge_tts.Communicate(
                text,
                voice=self.voice,
                rate=self.speed,
            )
            communicate.save(str(output_wav))
        except Exception as e:
            raise TtsProviderError(
                f"Edge-TTS generation failed: {e}"
            ) from e

