# Recipe: Task_011 — TDD: pipeline.py (Main Orchestrator)

## 1. Objective
Implement video/pipeline.py: the main entry point that reads config, discovers slides/notes, runs all steps sequentially per slide with checkpoint support, generates bookends, and calls concat.

## 2. Input Sources
- case/00_Constitution/core.md
- case/01_Roadmap/roadmap.md
- video/checkpoint.py (Task_003)
- video/progress.py (Task_004)
- video/steps/step3_clip.py (Task_007)
- video/steps/step4_bookend.py (Task_008)
- video/steps/step5_concat.py (Task_009)
- docs/research/VIDEO_PIPELINE_SPEC.md — Section 2 (full pipeline diagram), Section 5 (config schema)

## 3. Output Specification

Write tests/video/test_pipeline.py FIRST:
- test_discovers_slides_in_order: given slides/ with 3 files, pipeline processes them in sorted order
- test_skips_completed_slide: slide with checkpoint clip=ok is skipped (step functions not called)
- test_failed_tts_skips_slide: if tts step raises TtsProviderError, slide is marked failed and pipeline continues to next
- test_failed_image_uses_fallback: if image step raises ImageProviderError, slide continues with text overlay (image_none)
- test_bookends_generated: intro and outro generation functions called once each
- test_concat_called_last: concat called after all slide clips, with correct ordered list
- test_ffmpeg_not_found_exits_early: RuntimeError from ffmpeg check → pipeline prints friendly error and returns without processing

Then implement video/pipeline.py:

def run_video_pipeline(
    project_root: Path,
    config: dict,
    output_dir: Path,
) -> Path | None:
    """
    Main pipeline entry point.
    Returns path to final mp4, or None if video.enabled is False or pipeline fails critically.
    """

def _check_dependencies() -> None:
    """Check ffmpeg in PATH. Raise RuntimeError if missing."""

def _discover_slides(slides_dir: Path, notes_dir: Path) -> list[SlideContext]:
    """Return sorted list of SlideContext (slide_id, content_md, notes_md)."""

Dataclass:
@dataclass
class SlideContext:
    slide_id: str          # e.g. "slide_01"
    content_path: Path     # slides/01_intro.md
    notes_path: Path       # notes/note-01_intro-zh.md
    clip_path: Path        # output/<run_id>/clips/slide_01.mp4

## 4. Local Definition of Done
- [ ] tests/video/test_pipeline.py with all 7 tests passing
- [ ] run_video_pipeline() returns None (not exception) when video.enabled is False
- [ ] All step imports are lazy (only imported when video.enabled is True)
- [ ] SlideContext dataclass defined in pipeline.py
- [ ] Pipeline prints progress for each slide using video.progress functions

## 5. Constraints
- Do NOT import any step or provider at module level — lazy imports only (to avoid startup cost)
- Config access always via config.get() with defaults — never assume key exists
- Slide discovery: match notes to slides by page number prefix (e.g. "01" matches "note-01_*")

## 6. Escalation Trigger
Escalate if notes/ and slides/ file naming conventions differ from VIDEO_PIPELINE_SPEC.md expectations.
