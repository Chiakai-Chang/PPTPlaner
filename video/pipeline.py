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
    slides_dir: Path | None = None,
    notes_dir: Path | None = None,
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

    # Validate configuration
    from video.config_validation import validate_video_config
    try:
        validate_video_config(video_cfg)
    except Exception as e:
        print(f"[VIDEO] Configuration error: {e}", flush=True)
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
        print_step_start,
        print_step,
        print_eta,
    )

    actual_slides_dir = slides_dir or (project_root / "slides")
    actual_notes_dir = notes_dir or (project_root / "notes")

    if not actual_slides_dir.exists() or not actual_notes_dir.exists():
        return None

    # Discover slides
    slide_contexts = _discover_slides(actual_slides_dir, actual_notes_dir)
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
        print_step_start("generating intro bookend clip")
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
            print_step("generating intro bookend clip", "ok")
        except Exception as e:
            intro_path = None
            cp.mark_bookend("intro", "failed")
            print_step("generating intro bookend clip", "failed", str(e))

    # Process each slide
    from video.providers.base import ImageProviderError, TtsProviderError
    import time

    start_time = time.time()
    done_count = 0
    slide_clips: list[Path] = []
    total = len(slide_contexts)

    for idx, ctx in enumerate(slide_contexts):
        print_slide_start(ctx.slide_id, idx + 1, total)

        # Check if all steps for this slide are done
        slide_done = all(
            cp.is_done(ctx.slide_id, step)
            for step in ["tts", "image", "clip"]
        )
        if slide_done:
            print_skipped(ctx.slide_id)
            slide_clips.append(ctx.clip_path)
            done_count += 1
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
        finally:
            done_count += 1
            print_eta(time.time() - start_time, done_count, total)

    # Generate outro
    outro_cfg = video_cfg.get("outro", {})
    outro_path = clips_dir / "outro.mp4"
    if outro_cfg.get("enabled", True):
        from video.steps.step4_bookend import generate_bookend_clip
        print_step_start("generating outro bookend clip")
        try:
            generate_bookend_clip(
                text=outro_cfg.get("text", outro_cfg.get("cta_text", "")),
                title=outro_cfg.get("channel_name", outro_cfg.get("video_title", "")),
                output_mp4=outro_path,
                duration_sec=outro_cfg.get("duration_sec", 12),
                width=outro_cfg.get("width", VIDEO_DEFAULT_WIDTH),
                height=outro_cfg.get("height", VIDEO_DEFAULT_HEIGHT),
            )
            print_step("generating outro bookend clip", "ok")
        except Exception as e:
            outro_path = None
            print_step("generating outro bookend clip", "failed", str(e))

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


def extract_spoken_text(note_content: str) -> str:
    """Extract only the actual speech from the rich note markdown file, removing headers and markers."""
    import re
    # Find everything between #### 【逐字講稿】 and either #### 【講者提示 & 轉場】 or a divider ---
    pattern = r"####\s*【逐字講稿】(.*)(?:####\s*【講者提示 & 轉場】|---)"
    match = re.search(pattern, note_content, re.DOTALL)
    if match:
        text = match.group(1).strip()
    else:
        # Fallback to cleaning up headings if structure is slightly different
        text = note_content
        # Remove metadata headers
        text = re.sub(r"###.*?\n", "", text)
        text = re.sub(r"####\s*【本頁重點摘要】.*?(?=####\s*【逐字講稿】)", "", text, flags=re.DOTALL)
        text = re.sub(r"####\s*【逐字講稿】", "", text)
        text = re.sub(r"####\s*【講者提示 & 轉場】.*", "", text, flags=re.DOTALL)
        text = re.sub(r"---", "", text)
    
    # Strip markdown symbols like list dashes, bold markers, blockquotes
    text = re.sub(r"^[-\*\+]\s+", "", text, flags=re.MULTILINE)  # bullet points
    text = re.sub(r"^\s*>\s*", "", text, flags=re.MULTILINE)     # blockquotes
    text = re.sub(r"#{1,6}\s+.*?\n", "", text)                  # internal subheadings (e.g. ##### ①)
    text = re.sub(r"\*\*|\*", "", text)                         # bold and italics
    text = re.sub(r"__|_", "", text)
    text = re.sub(r"`", "", text)                               # inline code backticks
    
    # Clean up empty lines
    cleaned_lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " ".join(cleaned_lines)


def run_slide_steps(
    ctx: SlideContext,
    config: dict[str, Any],
    clips_dir: Path,
) -> None:
    """Run all steps for a single slide."""
    from video.constants import VIDEO_DEFAULT_FPS
    from video.progress import print_step_start, print_step

    tts_cfg = config.get("video", {}).get("tts", {})
    image_cfg = config.get("video", {}).get("image", {})

    # Step 1: TTS
    tts_provider = _create_tts_provider(tts_cfg)
    wav_path = clips_dir / f"{ctx.slide_id}.wav"
    print_step_start("generating speech (TTS)")
    try:
        raw_notes = ctx.notes_path.read_text(encoding="utf-8")
        spoken_text = extract_spoken_text(raw_notes)
        tts_provider.generate(spoken_text, wav_path)
        print_step("generating speech (TTS)", "ok")
    except Exception as e:
        print_step("generating speech (TTS)", "failed", str(e))
        raise

    # Step 2: Image
    img_provider = _create_image_provider(image_cfg)
    img_path = clips_dir / f"{ctx.slide_id}.png"
    print_step_start("generating visual frame (PIL)")
    try:
        img_provider.generate(
            title=ctx.content_path.read_text(),
            bullets=[],
            output_png=img_path,
        )
        print_step("generating visual frame (PIL)", "ok")
    except Exception as e:
        print_step("generating visual frame (PIL)", "failed", str(e))
        raise

    # Step 3: Clip
    from video.steps.step3_clip import compose_clip

    print_step_start("rendering video clip (FFmpeg)")
    try:
        compose_clip(
            image_path=img_path,
            wav_path=wav_path,
            output_mp4=ctx.clip_path,
            fps=VIDEO_DEFAULT_FPS,
        )
        print_step("rendering video clip (FFmpeg)", "ok")
    except Exception as e:
        print_step("rendering video clip (FFmpeg)", "failed", str(e))
        raise


def _create_tts_provider(tts_cfg: dict) -> "TtsProvider":
    """Create TTS provider based on config."""
    provider_name = tts_cfg.get("provider", "edge-tts")

    if provider_name == "edge-tts":
        from video.providers.tts_edge import EdgeTtsProvider
        return EdgeTtsProvider(
            voice=tts_cfg.get("edge_tts_voice", "zh-TW-HsiaoChenNeural"),
            speed=tts_cfg.get("edge_tts_speed", "+0%"),
        )
    elif provider_name == "fish-speech":
        from video.providers.tts_fish import FishSpeechProvider
        return FishSpeechProvider(
            url=tts_cfg.get("fish_speech_url", "http://localhost:8080"),
            model=tts_cfg.get("fish_speech_model", "fish-speech-1.4"),
            voice=tts_cfg.get("fish_speech_voice", "default"),
            speed=tts_cfg.get("fish_speech_speed", 1.0),
        )
    else:
        raise RuntimeError(f"Unknown TTS provider: {provider_name}")


def _create_image_provider(image_cfg: dict) -> "ImageProvider":
    """Create image provider based on config."""
    provider_name = image_cfg.get("provider", "none")
    width = image_cfg.get("width", 1920)
    height = image_cfg.get("height", 1080)

    if provider_name == "none":
        from video.providers.image_none import NoneImageProvider
        return NoneImageProvider()
    elif provider_name == "comfyui":
        from video.providers.image_comfyui import ComfyUIProvider
        return ComfyUIProvider(
            url=image_cfg.get("comfyui_url", "http://localhost:8188"),
            workflow_file=image_cfg.get("comfyui_workflow", "image_flux.json"),
        )
    elif provider_name == "runninghub":
        from video.providers.image_runninghub import RunningHubProvider
        api_key = image_cfg.get("runninghub_api_key", "")
        workflow_id = image_cfg.get("runninghub_workflow", "image_flux.json")
        return RunningHubProvider(api_key=api_key, workflow_id=workflow_id)
    else:
        raise RuntimeError(f"Unknown image provider: {provider_name}")
