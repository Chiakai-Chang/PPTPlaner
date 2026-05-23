# Recipe: Task_013 — Integration: Wire Video Pipeline into orchestrate.py

## 1. Objective
Add a minimal hook at the end of scripts/orchestrate.py that calls the video pipeline when video.enabled is True. Must not change any existing behavior.

## 2. Input Sources
- case/00_Constitution/core.md
- scripts/orchestrate.py — read full file to understand structure
- video/pipeline.py (Task_011) — run_video_pipeline() signature

## 3. Output Specification
Find the section in orchestrate.py where the main run completes (after ZIP packaging).
Add this block immediately after:

```python
# --- Optional: Video Pipeline ---
if cfg.get("video", {}).get("enabled", False):
    print_header("VIDEO PIPELINE")
    try:
        from video.pipeline import run_video_pipeline
        video_out = run_video_pipeline(
            project_root=ROOT,
            config=cfg,
            output_dir=OUTPUT_ROOT / run_id,
        )
        if video_out:
            print_success(f"Video produced: {video_out}")
        else:
            print(f"  ⚠ Video pipeline returned no output.", flush=True)
    except Exception as e:
        print(f"  ✗ Video pipeline error: {e}", flush=True)
        rlog(f"VIDEO PIPELINE ERROR: {e}")
```

Where `cfg` is the loaded config dict and `run_id` is the current run identifier. Adjust variable names to match actual orchestrate.py variable names found by reading the file.

## 4. Local Definition of Done
- [ ] orchestrate.py modified with the hook block
- [ ] python scripts/orchestrate.py runs successfully with video.enabled: false (no video code executed)
- [ ] python -c "import scripts.orchestrate" succeeds (no import errors)
- [ ] The addition is the ONLY change to orchestrate.py (verified by git diff)
- [ ] Import of video.pipeline is inside the if block (lazy import)

## 5. Constraints
- Lazy import of video.pipeline — MUST be inside the if block
- Use try/except around the entire block — video failure must not crash the main pipeline
- Do NOT call print_header or any other function that doesn't already exist in orchestrate.py

## 6. Escalation Trigger
Escalate if scripts/orchestrate.py structure does not have a clear "end of main run" location after ZIP packaging.
