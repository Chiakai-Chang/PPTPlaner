"""Step 4: Generate bookend clips (intro/outro) using TTS + PIL + FFmpeg."""

from pathlib import Path

from video.providers.tts_edge import EdgeTtsProvider
from video.providers.image_none import NoneImageProvider
from video.steps.step3_clip import compose_clip


class BookendError(Exception):
    """Raised when bookend generation fails."""
    pass


def generate_bookend_clip(
    text: str,
    title: str,
    output_mp4: Path,
    duration_sec: int = 8,
    width: int = 1920,
    height: int = 1080,
) -> Path:
    """
    Generate intro or outro clip from text.

    Steps:
    1. TTS: Generate speech audio from text
    2. PIL: Generate title image
    3. FFmpeg: Combine into mp4

    Returns path to generated mp4.

    Raises:
        BookendError: If generation fails.
    """
    output_mp4.parent.mkdir(parents=True, exist_ok=True)

    # Step 1: TTS
    wav_path = output_mp4.parent / f"{output_mp4.stem}.wav"
    try:
        tts = EdgeTtsProvider(voice="zh-TW-HsiaoChenNeural")
        tts.synthesize(text, wav_path)
    except Exception as e:
        raise BookendError(f"TTS failed for bookend: {e}") from e

    # Step 2: PIL image with title
    img_path = output_mp4.parent / f"{output_mp4.stem}.png"
    try:
        img = NoneImageProvider(width=width, height=height)
        img.render(text=title, output=img_path)
    except Exception as e:
        raise BookendError(f"Image generation failed for bookend: {e}") from e

    # Step 3: FFmpeg clip
    try:
        compose_clip(
            image_path=img_path,
            wav_path=wav_path,
            output_mp4=output_mp4,
            fps=30,
        )
    except Exception as e:
        raise BookendError(f"FFmpeg failed for bookend: {e}") from e

    # Cleanup temp files
    wav_path.unlink(missing_ok=True)
    img_path.unlink(missing_ok=True)

    return output_mp4
