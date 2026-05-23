"""Step 5: Concatenate clips and optionally mix BGM."""

import shutil
import subprocess
import tempfile
from pathlib import Path


class ConcatError(Exception):
    """Raised when ffmpeg concatenation fails."""
    pass


def concat_clips(
    intro_clip: Path,
    slide_clips: list[Path],
    outro_clip: Path,
    output_mp4: Path,
    bgm_file: Path | None = None,
    bgm_volume: float = 0.15,
) -> Path:
    """
    Concatenate intro + slide_clips + outro into output_mp4.

    If bgm_file is set, mix BGM at bgm_volume (0.0-1.0) into final audio.
    Uses ffmpeg concat demuxer (list file approach).

    Returns output_mp4 path.

    Raises:
        ValueError: If slide_clips is empty.
        RuntimeError: If ffmpeg is not in PATH.
        ConcatError: If ffmpeg returns a non-zero exit code.
    """
    if not slide_clips:
        raise ValueError("slide_clips must not be empty")

    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        raise RuntimeError("ffmpeg not found in PATH")

    all_clips = [intro_clip] + list(slide_clips) + [outro_clip]
    output_mp4.parent.mkdir(parents=True, exist_ok=True)

    # Create concat list file
    concat_list = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False
    )
    for clip in all_clips:
        concat_list.write(f"file '{clip.resolve()}'\n")
    concat_list.close()

    try:
        if bgm_file is not None:
            # Two-pass: concat first, then mix BGM
            tmp_concat = output_mp4.with_suffix(".tmp.mp4")
            cmd = [
                ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", concat_list.name,
                "-c", "copy",
                "-y",
                str(tmp_concat),
            ]
            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=300)
            except subprocess.CalledProcessError as e:
                stderr_msg = ""
                if e.stderr:
                    stderr_msg = e.stderr.decode("utf-8", errors="replace")
                raise ConcatError(
                    f"ffmpeg concat failed: {stderr_msg}"
                ) from e

            # Mix BGM
            cmd = [
                ffmpeg_path,
                "-i", str(tmp_concat),
                "-i", str(bgm_file),
                "-filter_complex",
                f"[1:a]volume={bgm_volume}[bgm];[0:a][bgm]amix=inputs=2:duration=first[a]",
                "-map", "0:v",
                "-map", "[a]",
                "-c:v", "copy",
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
                raise ConcatError(
                    f"ffmpeg BGM mix failed: {stderr_msg}"
                ) from e

            tmp_concat.unlink(missing_ok=True)
        else:
            # Simple concat
            cmd = [
                ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", concat_list.name,
                "-c", "copy",
                "-y",
                str(output_mp4),
            ]
            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=300)
            except subprocess.CalledProcessError as e:
                stderr_msg = ""
                if e.stderr:
                    stderr_msg = e.stderr.decode("utf-8", errors="replace")
                raise ConcatError(
                    f"ffmpeg concat failed: {stderr_msg}"
                ) from e

    finally:
        Path(concat_list.name).unlink(missing_ok=True)

    return output_mp4
