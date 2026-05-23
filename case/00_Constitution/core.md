# PPTPlaner Video Pipeline — Constitution
> Authority: Layer 1 (Human). READ-ONLY for all agents.  
> Last updated: 2026-05-23 by cloud AI (claude-sonnet-4-6) on human instruction.

---

## Mission Objective

Build the **Video Pipeline (Phase 1 MVP)** for PPTPlaner: a sequential, checkpoint-enabled pipeline that converts PPTPlaner's existing `notes/` (逐字稿) into a YouTube-ready `.mp4` explanation video with customizable intro/outro branding.

---

## Non-Negotiable Constraints

1. **No parallel processing.** Every slide is processed fully (TTS → image → clip) before the next begins. Reliability over speed.

2. **Checkpoint-first.** Every completed step writes to `video_progress.json` immediately. If interrupted, the pipeline resumes from the last checkpoint without reprocessing completed slides.

3. **Fail-skip-continue.** If one slide's image generation fails, log the failure, fall back to text overlay, and continue. Never halt the entire pipeline for a non-critical failure. TTS failure IS critical (halt that slide, skip it entirely, continue next slide).

4. **Optional by default.** The video pipeline is gated by `video.enabled: false` in `config.yaml`. Core PPTPlaner pipeline (slides + notes) MUST NOT be modified.

5. **No SVG.** SVG output was abandoned. Video visuals come from AI-generated images OR text overlay (PIL). Never attempt to load or render `.svg` files.

6. **Provider abstraction.** TTS, image generation, and HTML rendering are behind provider interfaces (ABCs). Hardcoding any specific provider's API call inside a step file is forbidden. Steps call providers via the interface only.

7. **FFmpeg is the video compositor.** All video operations (clip assembly, concat, BGM mixing) use `ffmpeg` subprocess calls. No Python video library (moviepy, etc.) is used.

8. **Config drives behavior.** All tunable parameters live in `config.yaml > video:`. No magic constants in code. Constants go into a `video/constants.py` module.

9. **Tests before implementation (TDD).** For every module: write failing tests first, then implement until tests pass. The task is NOT done until tests pass.

10. **Windows-compatible.** PPTPlaner runs on Windows 11. All file paths, subprocess calls, and encoding handling must be Windows-safe. Use `pathlib.Path` throughout.

---

## Authorized External Dependencies (Phase 1 only)

| Dependency | Purpose | Install |
|-----------|---------|---------|
| `edge-tts` | TTS provider (Phase 1) | `pip install edge-tts` |
| `Pillow` | Text overlay image generation | `pip install Pillow` |
| `Jinja2` | HTML template rendering | `pip install Jinja2` |
| `playwright` | HTML → PNG screenshot (bookend) | `pip install playwright && playwright install chromium` |
| `httpx` | HTTP client (future providers) | `pip install httpx` |
| `pytest` | Test runner | already in dev deps |
| `ffmpeg` | Video composition | System install, must be in PATH |

**Not authorized for Phase 1:** moviepy, cairosvg, fish-speech, ComfyUI, RunningHub, any GPU-dependent library.

---

## Authorized Read Paths for All Agents

| Path | Description |
|------|-------------|
| `docs/research/VIDEO_PIPELINE_SPEC.md` | Full technical specification |
| `config.yaml` | Project config (read for reference) |
| `scripts/orchestrate.py` | Main orchestrator (read for reference) |
| `case/00_Constitution/core.md` | This file |
| `case/01_Roadmap/roadmap.md` | Phase breakdown |
| `case/01_Roadmap/global_dod.md` | Global acceptance criteria |
| Own task folder only | `case/02_Task_Queue/Task_<NNN>_<slug>/` |
