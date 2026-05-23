"""Step 3: Compose a per-slide clip from image + audio using ffmpeg."""

import subprocess
import shutil
from pathlib import Path


class ClipCompositionError(Exception):
    """Raised when ffmpeg clip composition fails."""
    pass


def compose_clip(
    image_path: Path,
    wav_path: Path,
    output_mp4: Path,
    fps: int = 30,
) -> Path:
    """
    Combine a static image + audio into an mp4 clip.

    Uses ffmpeg:
        -loop 1 -i <image> -i <audio> -c:v libx264 -tune stillimage
        -c:a aac -b:a 192k -shortest -y <output>

    Returns the output_mp4 path.

    Raises:
        RuntimeError: If ffmpeg is not found in PATH.
        ClipCompositionError: If ffmpeg returns a non-zero exit code.
    """
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        raise RuntimeError("ffmpeg not found in PATH")

    # Ensure output directory exists
    output_mp4.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        ffmpeg_path,
        "-loop", "1",
        "-i", str(image_path),
        "-i", str(wav_path),
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-y",
        str(output_mp4),
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=300)
    except subprocess.CalledProcessError as e:
        stderr_msg = ""
        if e.stderr:
            stderr_msg = e.stderr.decode("utf-8", errors="replace")
        raise ClipCompositionError(
            f"ffmpeg failed with code {e.returncode}: {stderr_msg}"
        ) from e

    return output_mp4
