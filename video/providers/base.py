from abc import ABC, abstractmethod
from pathlib import Path


class TtsProviderError(Exception):
    """Raised when a TTS provider fails to generate audio."""


class ImageProviderError(Exception):
    """Raised when an image provider fails to generate a frame."""


class TtsProvider(ABC):
    @abstractmethod
    def generate(self, text: str, output_wav: Path, language: str = "zh-TW") -> None:
        """Synthesize text to WAV. Raises TtsProviderError on failure."""

    @abstractmethod
    def name(self) -> str:
        """Return provider identifier string (e.g. 'edge-tts')."""


class ImageProvider(ABC):
    @abstractmethod
    def generate(
        self,
        title: str,
        bullets: list[str],
        output_png: Path,
        width: int = 1920,
        height: int = 1080,
    ) -> None:
        """Generate visual frame PNG. Raises ImageProviderError on failure."""

    @abstractmethod
    def name(self) -> str:
        """Return provider identifier string (e.g. 'none')."""

