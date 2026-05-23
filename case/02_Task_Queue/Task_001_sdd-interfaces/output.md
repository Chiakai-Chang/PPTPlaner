# Output: Task_001

## Files Created
- `video/providers/base.py` — ABCs: TtsProvider, ImageProvider + exception classes
- `video/__init__.py` — empty package marker
- `video/providers/__init__.py` — re-exports TtsProvider, ImageProvider, TtsProviderError, ImageProviderError
- `video/constants.py` — VIDEO_DEFAULT_WIDTH, VIDEO_DEFAULT_HEIGHT, VIDEO_DEFAULT_FPS

## Tests
- Inline import verification via python -c — all assertions pass

## Coverage
- N/A (interfaces only, no implementation to cover)

## DoD Checklist
- [x] `video/providers/base.py` exists with all 4 symbols
- [x] `from video.providers.base import TtsProvider, ImageProvider` succeeds
- [x] `TtsProvider` has abstract methods `generate` and `name`
- [x] `ImageProvider` has abstract methods `generate` and `name`
- [x] `video/constants.py` exists with the 3 default constants
- [x] All `__init__.py` files created

