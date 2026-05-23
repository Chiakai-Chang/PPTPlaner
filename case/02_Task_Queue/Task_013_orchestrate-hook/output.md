# Task_013 Output — Wire Video Pipeline into orchestrate.py

## Summary
Added video pipeline hook at the end of orchestrate.py, after all phases complete and before "Run Complete!".

## Changes
- `scripts/orchestrate.py` — added lazy import + try/except block for video pipeline
- Hook location: between `report_save()` and `print_header("Run Complete!")`
- Variables used: `cfg`, `ROOT`, `output_dir` (all existing in scope)

## Verification
- Lazy import of video.pipeline inside if block ✓
- try/except around entire block ✓
- video.enabled check before execution ✓
- No changes to existing behavior ✓

## Status
REVIEW
