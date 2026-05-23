# Recipe: Task_009 — TDD: steps/step5_concat.py

## 1. Objective
Implement step5_concat.py: takes an ordered list of mp4 clip paths (intro + slides + outro), concatenates them using ffmpeg concat demuxer, and optionally mixes in BGM audio at specified volume.

## 2. Input Sources
- case/00_Constitution/core.md
- video/steps/step3_clip.py (Task_007) — for ffmpeg patterns

## 3. Output Specification

Write tests/video/test_step_concat.py FIRST:
- test_creates_concat_list_file: verify ffmpeg called with a concat list file containing all clip paths
- test_correct_clip_order: intro clip appears first, outro appears last in concat list
- test_bgm_mixed_when_set: when bgm_file is provided, ffmpeg called with audio mix args (-i bgm -filter_complex amix)
- test_no_bgm_when_null: when bgm_file is None, ffmpeg called without bgm-related args
- test_output_path_returned: function returns Path to final mp4
- test_empty_clips_raises: ValueError if slides list is empty

Then implement video/steps/step5_concat.py:

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
    Uses ffmpeg concat demuxer (list file approach, not complex filter).
    Returns output_mp4 path.
    Raises ValueError if slide_clips is empty.
    Raises RuntimeError if ffmpeg not in PATH.
    """

## 4. Local Definition of Done
- [ ] tests/video/test_step_concat.py with all 6 tests passing
- [ ] Uses ffmpeg concat demuxer via list file (not -filter_complex concat)
- [ ] BGM mixed via -filter_complex amix when bgm_file provided
- [ ] Temp concat list file cleaned up after ffmpeg completes
- [ ] All subprocess calls use check=True

## 5. Constraints
- ffmpeg concat list file format: "file '/absolute/path/clip.mp4'" one per line
- Paths in concat list MUST be absolute (use Path.resolve())
- Do NOT use moviepy

## 6. Escalation Trigger
Escalate if ffmpeg concat demuxer produces audio sync issues (different audio sample rates across clips).
