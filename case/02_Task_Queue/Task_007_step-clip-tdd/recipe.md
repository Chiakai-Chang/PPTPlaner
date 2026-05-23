# Recipe: Task_007 — TDD: steps/step3_clip.py

## 1. Objective
Implement step3_clip.py: takes a PNG image and WAV audio file, uses ffmpeg to produce a per-slide mp4 clip. Duration equals WAV audio length.

## 2. Input Sources
- case/00_Constitution/core.md
- video/providers/base.py (Task_001)
- video/checkpoint.py (Task_003)

## 3. Output Specification

Write tests/video/test_step_clip.py FIRST:
- test_compose_calls_ffmpeg: mock subprocess.run, verify ffmpeg called with correct args (loop image, audio input, map streams)
- test_output_path_returned: compose_clip() returns Path to output mp4
- test_ffmpeg_not_found_raises_runtime_error: mock shutil.which returning None → RuntimeError with message "ffmpeg not found in PATH"
- test_ffmpeg_failure_raises: mock subprocess.run raising CalledProcessError → ClipCompositionError raised
- test_output_dir_created: output dir created if missing (mock filesystem)

Then implement video/steps/step3_clip.py:

def compose_clip(
    image_path: Path,
    wav_path: Path,
    output_mp4: Path,
    fps: int = 30,
) -> Path:
    """
    Combine a static image + audio into an mp4 clip.
    Uses ffmpeg: -loop 1 -i image -i audio -c:v libx264 -tune stillimage -c:a aac -shortest
    Returns output_mp4 path.
    Raises ClipCompositionError on ffmpeg failure.
    Raises RuntimeError if ffmpeg not in PATH.
    """

class ClipCompositionError(Exception): pass

Also create video/steps/__init__.py (empty).

## 4. Local Definition of Done
- [ ] tests/video/test_step_clip.py with all 5 tests passing
- [ ] compose_clip() uses subprocess.run with check=True
- [ ] ffmpeg PATH check done at function call time (not import time)
- [ ] ClipCompositionError defined in step3_clip.py
- [ ] video/steps/__init__.py created

## 5. Constraints
- ffmpeg args: -loop 1 -i <image> -i <audio> -c:v libx264 -tune stillimage -c:a aac -b:a 192k -shortest -y <output>
- Use pathlib.Path for all paths; convert to str only for subprocess args
- Do NOT use moviepy or any Python video library

## 6. Escalation Trigger
Escalate if the ffmpeg command produces non-standard output on Windows that requires different flags.
