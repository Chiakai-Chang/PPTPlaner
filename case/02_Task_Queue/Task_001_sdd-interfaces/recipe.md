# Recipe: Task_001 — SDD: Provider Interfaces

## 1. Objective
Write Python Abstract Base Classes (ABCs) defining contracts for TTS and Image providers. All other implementation tasks depend on these interfaces.

## 2. Input Sources
- `case/00_Constitution/core.md`
- `docs/research/VIDEO_PIPELINE_SPEC.md` — Section 3 (provider modes), Section 6 (directory structure)

## 3. Output Specification
Write to `video/providers/base.py`:

```python
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
```

Also create:
- `video/__init__.py` — empty
- `video/providers/__init__.py` — exports `TtsProvider, ImageProvider, TtsProviderError, ImageProviderError`
- `video/constants.py` — placeholder with `VIDEO_DEFAULT_WIDTH = 1920`, `VIDEO_DEFAULT_HEIGHT = 1080`, `VIDEO_DEFAULT_FPS = 30`

## 4. Local Definition of Done
- [ ] `video/providers/base.py` exists with all 4 symbols
- [ ] `from video.providers.base import TtsProvider, ImageProvider` succeeds
- [ ] `TtsProvider` has abstract methods `generate` and `name`
- [ ] `ImageProvider` has abstract methods `generate` and `name`
- [ ] `video/constants.py` exists with the 3 default constants
- [ ] All `__init__.py` files created

## 5. Constraints
- ABCs only in `base.py` — no implementation code
- No external imports beyond `abc` and `pathlib`
- No files outside `video/` directory

## 6. Escalation Trigger
Escalate if the interface signatures conflict with VIDEO_PIPELINE_SPEC.md Section 3.
