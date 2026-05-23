# FOR_HUMAN — Human Operator Guide

> For: the human (you) who reviews task output, merges, and manages the GPU machine.

---

## Context

PPTPlaner Phase 1 planning is complete. All 14 task packages exist in `case/02_Task_Queue/`.
Local model agents on a GPU machine will execute the tasks sequentially, commit, and push.
Your job is to review `REVIEW` tasks, approve or send back, and handle anything that needs human judgment.

---

## Reading Order (one-time setup)

To get full context, read in this order:

1. `docs/research/RATIONALE.md` — why all key decisions were made
2. `docs/research/VIDEO_PIPELINE_SPEC.md` — architecture and config spec
3. `case/00_Constitution/core.md` — hard constraints agents must follow
4. `case/01_Roadmap/roadmap.md` — dependency graph and file output map
5. `case/01_Roadmap/global_dod.md` — what Phase 1 done means
6. `docs/VIDEO_PIPELINE_INDEX.md` — full doc index

---

## Daily Workflow

### 1. Pull latest

```bash
git pull
```

### 2. Check task statuses

```powershell
Get-ChildItem case\02_Task_Queue -Recurse -Filter status.txt |
  ForEach-Object { "$($_.Directory.Name): $(Get-Content $_)" }
```

### 3. Review REVIEW tasks

For each task in `REVIEW` state:

a. Read `case/02_Task_Queue/<task>/output.md`
b. Check files the agent created
c. Run tests: `pytest tests/video/ -v`
d. Check coverage: `pytest --cov=video tests/video/ --cov-report=term-missing`

**If approved** → `echo DONE > case\02_Task_Queue\<task>\status.txt`, commit+push.

**If needs rework** → Write feedback in `feedback.md`, set status to `ESCALATED`, commit+push.

### 4. Handle ESCALATED tasks

Read `case/02_Task_Queue/<task>/feedback.md`. Either:
- Fix the recipe.md ambiguity, set status back to `PENDING`, push
- Fix the code yourself, set status to `DONE`, push
- Ask cloud AI for spec clarification, update recipe.md, set back to `PENDING`

---

## Switching to GPU Machine

On your development machine:

```bash
git push
```

On the GPU machine (first time):

```bash
git clone <remote-url> PPTPlaner
cd PPTPlaner
uv sync
uv add edge-tts Pillow Jinja2 playwright
playwright install chromium
winget install Gyan.FFmpeg   # or equivalent for the OS
```

**Critical**: `research/` is gitignored. If Phase 2 is needed:

```bash
git clone https://github.com/fishaudio/fish-speech research/fish-speech
git clone https://github.com/AIDC-AI/Pixelle-Video research/Pixelle-Video
```

Phase 1 tasks (001–014) do NOT need `research/`.

---

## Phase Checkpoints

| Milestone | What to verify |
|-----------|---------------|
| Batch 0 done | `video/providers/base.py` imports cleanly; `tests/video/features/*.feature` exist |
| Batch 1 done | `pytest tests/video/` green; checkpoint.py round-trip works |
| Batch 2 done | `pytest tests/video/` green for step tests; templates render in browser |
| Batch 3 done | `python -c "from video.pipeline import run_video_pipeline"` works |
| Phase 1 done | All items in `case/01_Roadmap/global_dod.md` checked |

---

## When Something Breaks

- Build error → agent should handle with recipe.md guidance; if stuck, set `ESCALATED`
- Spec conflict → update recipe.md (mark version), reset task to `PENDING`
- Dependency missing → update `pyproject.toml`, commit, inform agent via recipe.md note
- ffmpeg not found → install system-wide, add to PATH

---

## Key Decisions Already Made

See `docs/research/RATIONALE.md` for full log. Summary:

| Decision | Chosen |
|----------|--------|
| Video paradigm | Narration + supporting visuals (not animated PPT) |
| Image generation Phase 1 | PIL text overlay (no AI image) |
| TTS Phase 1 | edge-tts (Microsoft cloud, free) |
| TTS Phase 2 | Fish Speech (local, 16GB+ VRAM) — proprietary license |
| Pixelle-Video | WO strategy: extract concepts, no code embed |
| SVG | Abandoned completely |
| Parallelism | Sequential only, no parallel processing |
| Checkpoint | `video_progress.json` atomic JSON, resume on restart |

---

## Files to Never Touch Without Understanding First

- `case/00_Constitution/core.md` — changing constraints breaks all tasks
- `case/02_Task_Queue/Task_NNN/recipe.md` — agents read this literally; vagueness = escalation
- `docs/research/VIDEO_PIPELINE_SPEC.md` — single source of truth for architecture
