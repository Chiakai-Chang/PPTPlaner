# QUICKSTART — Local Model Agent Entry Point

> For: Layer 3 local model agents on GPU machine.
> Read this file first. Read nothing else until instructed below.

---

## 1. First-Time Machine Setup

### Clone the repo (if not done)

```bash
git clone <your-remote-url> PPTPlaner
cd PPTPlaner
```

### Install Python dependencies

```bash
uv sync
# or, if uv not available:
pip install -r requirements.txt
```

Phase 1 extra deps (if not already in pyproject.toml):

```bash
uv add edge-tts Pillow Jinja2 playwright
playwright install chromium
```

### Install ffmpeg (system dependency)

Windows (winget):

```powershell
winget install Gyan.FFmpeg
```

Verify: `ffmpeg -version` should print version info. If not found, add to PATH.

---

## 2. Critical: `research/` Is Gitignored

The directory `research/` at the repo root is excluded from git (`.gitignore` rule: `/research/`).

This means:

| Phase | research/ needed? | Action |
|-------|------------------|--------|
| Phase 1 (Tasks 001–014) | **NO** | Nothing to do |
| Phase 2 (Fish Speech, ComfyUI) | **YES** | Clone manually: |

```bash
# Phase 2 only — do NOT run for Phase 1 tasks
git clone https://github.com/fishaudio/fish-speech research/fish-speech
git clone https://github.com/AIDC-AI/Pixelle-Video research/Pixelle-Video
```

`docs/research/` (committed docs) is different — already in the repo.

---

## 3. Check Task Queue

All tasks live in `case/02_Task_Queue/`. Each task folder has `status.txt`.

Valid statuses: `PENDING` | `IN_PROGRESS` | `REVIEW` | `DONE` | `ESCALATED`

```bash
# Quick status overview (Windows PowerShell)
Get-ChildItem case\02_Task_Queue -Recurse -Filter status.txt |
  ForEach-Object { "$($_.Directory.Name): $(Get-Content $_)" }
```

**Pick rule**: lowest batch number with status `PENDING`. Never start a task whose dependencies are not `DONE`.

Dependency order (see `case/01_Roadmap/roadmap.md` for full graph):

```
Batch 0: Task_001, Task_002   (no deps — start here)
Batch 1: Task_003–006, 012    (needs Task_001 DONE)
Batch 2: Task_007–010         (needs Batch 1 DONE)
Batch 3: Task_011             (needs Batch 2 DONE)
Batch 4: Task_013, Task_014   (needs Task_011 DONE)
```

---

## 4. Execute a Task

### Step 1 — Claim the task

Write `IN_PROGRESS` to the task's `status.txt`:

```bash
echo IN_PROGRESS > case\02_Task_Queue\Task_001_sdd-interfaces\status.txt
```

Append to `action_log.jsonl`:

```json
{"ts": "2026-05-23T22:00:00Z", "agent": "your-model-name", "action": "start", "task": "Task_001"}
```

### Step 2 — Read your instructions

1. `case/00_Constitution/core.md` — hard constraints, read once
2. `case/02_Task_Queue/<task>/role.md` — your persona/scope for this task
3. `case/02_Task_Queue/<task>/recipe.md` — exact inputs, outputs, DoD

### Step 3 — Execute

Follow recipe.md exactly. Produce the files listed under **Output Specification**.

Constraints from `core.md` apply to every task:
- No parallel execution within a task
- Use `pathlib.Path` for all file paths
- No hardcoded strings (use config or constants)
- TDD: write tests first (RED), then implement (GREEN)
- No SVG anywhere in `video/`

### Step 4 — Verify Definition of Done

Check every checkbox in recipe.md > **Local Definition of Done** section.

Run tests:

```bash
pytest tests/video/ -v
pytest --cov=video tests/video/ --cov-report=term-missing
```

Coverage must be ≥ 80% for the module you implemented.

### Step 5 — Write output summary

Create/update `case/02_Task_Queue/<task>/output.md`:

```markdown
# Output: Task_XXX

## Files Created
- path/to/file.py — description

## Tests
- tests/video/test_xxx.py — N tests, all pass

## Coverage
- video/xxx.py: 87%

## DoD Checklist
- [x] item 1
- [x] item 2
```

### Step 6 — Set status to REVIEW

```bash
echo REVIEW > case\02_Task_Queue\Task_001_sdd-interfaces\status.txt
```

Append to `action_log.jsonl`:

```json
{"ts": "2026-05-23T23:00:00Z", "agent": "your-model-name", "action": "complete", "task": "Task_001"}
```

### Step 7 — Commit and push

```bash
git add .
git commit -m "feat(video): Task_001 — SDD provider interfaces"
git push
```

Human reviewer will then move status to `DONE` or send back as `ESCALATED`.

---

## 5. Escalation Protocol

If you cannot complete a task (ambiguous spec, conflicting constraint, dependency missing):

1. Set `status.txt` → `ESCALATED`
2. Write `case/02_Task_Queue/<task>/feedback.md`:

```markdown
# Escalation: Task_XXX

## Blocker
<one sentence>

## Details
<what you tried, what failed, what's ambiguous>

## Proposed Resolution
<your best guess at the fix — human decides>
```

3. Commit and push.
4. Move to next PENDING task if one exists in a lower or equal batch.

---

## 6. `action_log.jsonl` Format

One JSON object per line, appended (never overwrite):

```json
{"ts": "ISO8601", "agent": "model-id", "action": "start|complete|escalate|skip", "task": "Task_NNN", "note": "optional"}
```

---

## 7. Quick Reference

| File | Purpose |
|------|---------|
| `case/00_Constitution/core.md` | Hard constraints (read once) |
| `case/01_Roadmap/roadmap.md` | Task dependency graph |
| `case/01_Roadmap/global_dod.md` | Phase 1 acceptance criteria |
| `case/02_Task_Queue/Task_NNN/role.md` | Agent persona for this task |
| `case/02_Task_Queue/Task_NNN/recipe.md` | Inputs, outputs, DoD |
| `case/02_Task_Queue/Task_NNN/status.txt` | Current state |
| `case/02_Task_Queue/Task_NNN/output.md` | Write here when done |
| `docs/research/VIDEO_PIPELINE_SPEC.md` | Full pipeline architecture |
| `docs/research/RATIONALE.md` | Decision log (why we chose X) |
