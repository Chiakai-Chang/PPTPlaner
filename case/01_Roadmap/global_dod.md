# Global Definition of Done — Video Pipeline Phase 1

> Used by Global Aggregation (Layer 2) after all tasks reach DONE.  
> All items must be satisfied before Phase 1 is declared complete.

---

## Functional Acceptance

- [ ] `python scripts/orchestrate.py` completes a full run with `video.enabled: true` and `video.backend: basic`
- [ ] Output file `output/<run_id>/<source_name>_video.mp4` is produced and playable
- [ ] Video contains: intro clip → N slide clips → outro clip (in order)
- [ ] Each slide clip audio matches the notes markdown for that slide (spot check 2 slides)
- [ ] Text overlay on each slide clip shows the slide title clearly
- [ ] Intro shows channel_name and tagline from config
- [ ] Outro shows cta_text from config
- [ ] If pipeline is interrupted mid-run and restarted, completed clips are NOT regenerated

## Reliability

- [ ] Simulated image provider failure on slide 3 → pipeline skips slide 3 image (uses text overlay), logs error, continues
- [ ] `video_progress.json` is written after every completed step
- [ ] Pipeline prints human-readable progress (slide X/N, step name, ETA) to stdout

## Quality

- [ ] All tests in `tests/video/` pass: `pytest tests/video/ -v`
- [ ] Test coverage for `video/` modules >= 80%: `pytest --cov=video tests/video/`
- [ ] No SVG file is loaded or referenced anywhere in `video/`

## Code Standards

- [ ] All file paths use `pathlib.Path` (no raw string paths)
- [ ] All `subprocess` calls use `check=True` or handle `CalledProcessError` explicitly
- [ ] `ffmpeg` availability checked at pipeline startup with a friendly error message
- [ ] No hardcoded strings that belong in `config.yaml` or `video/constants.py`

## Integration

- [ ] `config.yaml` has `video:` section with all fields from VIDEO_PIPELINE_SPEC.md §5
- [ ] `video.enabled: false` (default) causes zero video-related code to execute in normal PPTPlaner runs
- [ ] Change to `scripts/orchestrate.py` is minimal: one conditional block at end calling `video/pipeline.py`
