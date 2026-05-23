# Recipe: Task_014 — Integration Test: Full Pipeline Validation

## 1. Objective
Validate the complete Phase 1 video pipeline end-to-end against real PPTPlaner output data. Report pass/fail for every item in global_dod.md.

## 2. Input Sources
- case/00_Constitution/core.md
- case/01_Roadmap/global_dod.md — the acceptance checklist
- notes/ directory — real speaker notes from PPTPlaner output
- slides/ directory — real slide content from PPTPlaner output
- config.yaml — set video.enabled: true for test run
- video/pipeline.py (Task_011 output)

## 3. Output Specification
Write output.md with:

# Integration Test Report
Date: <ISO date>
Run ID: <actual run_id>

## Global DoD Results
| # | Item | Result | Notes |
|---|------|--------|-------|
| 1 | pipeline produces mp4 | PASS/FAIL | path or error |
...one row per global_dod.md item...

## Issues Found
<list any failures with details>

## Recommendation
PASS / FAIL — ready/not ready for Phase 2

Also write tests/video/test_integration.py with a single integration test:
- test_full_pipeline_produces_mp4: runs run_video_pipeline() on sample data, asserts mp4 exists and size > 0

## 4. Local Definition of Done
- [ ] output.md written with all Global DoD items evaluated
- [ ] tests/video/test_integration.py written and runnable
- [ ] All PASS items verified with actual file existence or command output
- [ ] Any FAIL item has specific error message recorded
- [ ] Overall recommendation (PASS/FAIL) stated

## 5. Constraints
- Must use REAL data from notes/ and slides/ — no mocks in integration test
- Set config video.enabled: true only for this test run; restore to false after
- If ffmpeg is not installed, mark all video composition items as BLOCKED (not FAIL) and note installation requirement

## 6. Escalation Trigger
Escalate if notes/ or slides/ directories are empty (no PPTPlaner output to test against). Run orchestrate.py first to generate them.
