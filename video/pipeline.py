"""Main video pipeline orchestrator."""

from __future__ import annotations

import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class SlideContext:
    """Context for a single slide in the video pipeline."""

    slide_id: str  # e.g. "01_intro"
    content_path: Path  # slides/01_intro.md
    notes_path: Path  # notes/note-01_intro-zh.md
    clip_path: Path  # output/<run_id>/clips/slide_01_intro.mp4


def _check_dependencies() -> None:
    """Check ffmpeg in PATH. Raise RuntimeError if missing."""
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg not found in PATH. Please install ffmpeg: "
            "https://ffmpeg.org/download.html"
        )


def _discover_slides(
    slides_dir: Path,
    notes_dir: Path,
) -> list[SlideContext]:
    """Return sorted list of SlideContext matching slides to notes by prefix."""
    from video.checkpoint import Checkpoint
    from video.constants import VIDEO_DEFAULT_WIDTH, VIDEO_DEFAULT_HEIGHT

    slides = sorted(slides_dir.glob("*.md"))
    result = []
    run_id = uuid.uuid4().hex[:8]
    clips_dir = Path("output") / run_id / "clips"

    for slide_file in slides:
        # Extract prefix (e.g., "01" from "01_intro.md")
        prefix = slide_file.stem.split("_")[0]
        slide_id = slide_file.stem

        # Find matching note
        note_pattern = f"note-{prefix}_*"
        note_files = list(notes_dir.glob(note_pattern))
        if not note_files:
            continue
        note_file = sorted(note_files)[0]

        clip_path = clips_dir / f"{slide_id}.mp4"

        result.append(SlideContext(
            slide_id=slide_id,
            content_path=slide_file,
            notes_path=note_file,
            clip_path=clip_path,
        ))

    return result


def run_video_pipeline(
    project_root: Path,
    config: dict[str, Any],
    output_dir: Path | None = None,
) -> Path | None:
    """
    Main pipeline entry point.

    Returns path to final mp4, or None if video.enabled is False
    or pipeline fails critically.

    Lazy imports: all step/provider imports happen inside this function
    to avoid startup cost when video is disabled.
    """
    video_cfg = config.get("video", {})
    if not video_cfg.get("enabled", False):
        return None

    # Check dependencies
    _check_dependencies()

    # Lazy imports
    from video.checkpoint import Checkpoint
    from video.constants import (
        VIDEO_DEFAULT_FPS,
        VIDEO_DEFAULT_HEIGHT,
        VIDEO_DEFAULT_WIDTH,
    )
    from video.progress import (
        print_slide_start,
        print_skipped,
        print_summary,
    )

    slides_dir = project_root / "slides"
    notes_dir = project_root / "notes"

    if not slides_dir.exists() or not notes_dir.exists():
        return None

    # Discover slides
    slide_contexts = _discover_slides(slides_dir, notes_dir)
    if not slide_contexts:
        return None

    # Setup output dirs
    run_id = uuid.uuid4().hex[:8]
    base_output = output_dir or (project_root / "output")
    clips_dir = base_output / run_id / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    # Create checkpoint for this run
    run_id = uuid.uuid4().hex[:8]
    cp = Checkpoint(clips_dir.parent, run_id)

    # Generate intro
    intro_cfg = video_cfg.get("intro", {})
    intro_path = clips_dir / "intro.mp4"
    if intro_cfg.get("enabled", True):
        from video.steps.step4_bookend import generate_bookend_clip
        try:
            generate_bookend_clip(
                text=intro_cfg.get("text", intro_cfg.get("channel_name", "")),
                title=intro_cfg.get("channel_name", intro_cfg.get("video_title", "")),
                output_mp4=intro_path,
                duration_sec=intro_cfg.get("duration_sec", 8),
                width=intro_cfg.get("width", VIDEO_DEFAULT_WIDTH),
                height=intro_cfg.get("height", VIDEO_DEFAULT_HEIGHT),
            )
            cp.mark_bookend("intro", "ok")
        except Exception:
            intro_path = None
            cp.mark_bookend("intro", "failed")

    # Process each slide
    from video.providers.base import ImageProviderError, TtsProviderError

    slide_clips: list[Path] = []
    total = len(slide_contexts)

    for idx, ctx in enumerate(slide_contexts):
        print_slide_start(idx + 1, total, ctx.slide_id)

        # Check if all steps for this slide are done
        slide_done = all(
            cp.is_done(ctx.slide_id, step)
            for step in ["tts", "image", "clip"]
        )
        if slide_done:
            print_skipped(ctx.slide_id)
            slide_clips.append(ctx.clip_path)
            continue

        try:
            run_slide_steps(ctx, config, clips_dir)
            cp.mark(ctx.slide_id, "tts", "ok")
            cp.mark(ctx.slide_id, "image", "ok")
            cp.mark(ctx.slide_id, "clip", "ok")
            slide_clips.append(ctx.clip_path)
        except TtsProviderError as e:
            cp.mark(ctx.slide_id, "tts", "failed", str(e))
            print(f"  ⚠ {ctx.slide_id} — TTS error: {e}", flush=True)
        except ImageProviderError as e:
            # Use fallback (text overlay)
            print(f"  ⚠ {ctx.slide_id} — Image error, using fallback: {e}", flush=True)
            cp.mark(ctx.slide_id, "image", "failed", str(e))
        except Exception as e:
            cp.mark(ctx.slide_id, "clip", "failed", str(e))
            print(f"  ⚠ {ctx.slide_id} — error: {e}", flush=True)

    # Generate outro
    outro_cfg = video_cfg.get("outro", {})
    outro_path = clips_dir / "outro.mp4"
    if outro_cfg.get("enabled", True):
        from video.steps.step4_bookend import generate_bookend_clip
        try:
            generate_bookend_clip(
                text=outro_cfg.get("text", outro_cfg.get("cta_text", "")),
                title=outro_cfg.get("channel_name", outro_cfg.get("video_title", "")),
                output_mp4=outro_path,
                duration_sec=outro_cfg.get("duration_sec", 12),
                width=outro_cfg.get("width", VIDEO_DEFAULT_WIDTH),
                height=outro_cfg.get("height", VIDEO_DEFAULT_HEIGHT),
            )
        except Exception:
            outro_path = None

    # Concat
    if not slide_clips:
        return None

    final_path = base_output / f"{run_id}_final.mp4"

    from video.steps.step5_concat import concat_clips, ConcatError

    intro_clip = intro_path if intro_path else slide_clips[0]
    outro_clip = outro_path if outro_path else slide_clips[-1]

    bgm_file = video_cfg.get("bgm_file")
    bgm_volume = video_cfg.get("bgm_volume", 0.15)

    try:
        concat_clips(
            intro_clip=intro_clip,
            slide_clips=slide_clips,
            outro_clip=outro_clip,
            output_mp4=final_path,
            bgm_file=Path(bgm_file) if bgm_file else None,
            bgm_volume=bgm_volume,
        )
    except ConcatError as e:
        print(f"[VIDEO] Concat failed: {e}")
        return None

    print_summary(len(slide_clips), 0, 0)
    return final_path


def run_slide_steps(
    ctx: SlideContext,
    config: dict[str, Any],
    clips_dir: Path,
) -> None:
    """Run all steps for a single slide."""
    from video.constants import VIDEO_DEFAULT_FPS

    tts_cfg = config.get("video", {}).get("tts", {})
    image_cfg = config.get("video", {}).get("image", {})

    # Step 1: TTS
    from video.providers.tts_edge import EdgeTtsProvider

    tts_provider = EdgeTtsProvider(
        voice=tts_cfg.get("edge_tts_voice", "zh-TW-HsiaoChenNeural"),
        speed=tts_cfg.get("edge_tts_speed", "+0%"),
    )
    wav_path = clips_dir / f"{ctx.slide_id}.wav"
    tts_provider.synthesize(ctx.notes_path.read_text(), wav_path)

    # Step 2: Image
    from video.providers.image_none import NoneImageProvider

    img_provider = NoneImageProvider(
        width=image_cfg.get("width", 1920),
        height=image_cfg.get("height", 1080),
    )
    img_path = clips_dir / f"{ctx.slide_id}.png"
    img_provider.render(
        text=ctx.content_path.read_text(),
        output=img_path,
    )

    # Step 3: Clip
    from video.steps.step3_clip import compose_clip

    compose_clip(
        image_path=img_path,
        wav_path=wav_path,
        output_mp4=ctx.clip_path,
        fps=VIDEO_DEFAULT_FPS,
    )
