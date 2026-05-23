# Task_007 Output — TDD: steps/step3_clip.py

## Summary
Implemented `compose_clip()` and `ClipCompositionError` for combining static image + audio into per-slide mp4 clips via ffmpeg.

## Files Created
- `video/steps/step3_clip.py` — compose_clip() with ffmpeg, ClipCompositionError
- `video/steps/__init__.py` — package marker
- `tests/video/test_step_clip.py` — 5 tests, all passing

## Test Results
```
tests/video/test_step_clip.py::TestComposeClip::test_compose_calls_ffmpeg PASSED
tests/video/test_step_clip.py::TestComposeClip::test_output_path_returned PASSED
tests/video/test_step_clip.py::TestComposeClip::test_ffmpeg_not_found_raises_runtime_error PASSED
tests/video/test_step_clip.py::TestComposeClip::test_ffmpeg_failure_raises PASSED
tests/video/test_step_clip.py::TestComposeClip::test_output_dir_created PASSED
============================== 5 passed in 0.04s
```

## Status
REVIEW
