# Video Pipeline — Master Document Index

> Entry point for navigating all planning and execution documents for the PPTPlaner video pipeline.

---

## Architecture & Decisions

| Document | Purpose |
|----------|---------|
| `docs/research/VIDEO_PIPELINE_SPEC.md` | Full pipeline architecture: modes, config schema, directory structure, checkpoint format, Phase 1/2/3 roadmap |
| `docs/research/PIXELLE_VIDEO_SWOT.md` | SWOT analysis of Pixelle-Video; why we chose WO strategy (extract concepts, don't embed code) |
| `docs/research/RATIONALE.md` | Decision log: every key choice, why it was made, what was rejected |
| `reference/DISTILLATION_GUIDE.md` | Methodology for evaluating and integrating external projects into PPTPlaner |

---

## Planning & Task Management

| Document | Purpose |
|----------|---------|
| `case/00_Constitution/core.md` | 10 non-negotiable constraints for all agents |
| `case/01_Roadmap/roadmap.md` | Batch ordering, dependency graph, output file map |
| `case/01_Roadmap/global_dod.md` | Phase 1 acceptance criteria (15 items) |
| `case/QUICKSTART.md` | Local model agent entry point: setup, task picking, execution protocol |
| `case/FOR_HUMAN.md` | Human operator guide: review workflow, machine switching, phase checkpoints |

---

## Task Queue (14 tasks, all PENDING)

| Task | Batch | Slug | Implements |
|------|-------|------|-----------|
| Task_001 | 0 | sdd-interfaces | `video/providers/base.py` — TtsProvider, ImageProvider ABCs |
| Task_002 | 0 | bdd-feature-specs | `tests/video/features/*.feature` — 7 Gherkin specs |
| Task_003 | 1 | checkpoint-tdd | `video/checkpoint.py` — atomic JSON state persistence |
| Task_004 | 1 | progress-tdd | `video/progress.py` — CLI progress display |
| Task_005 | 1 | tts-edge-tdd | `video/providers/tts_edge.py` — Edge-TTS wrapper |
| Task_006 | 1 | image-none-tdd | `video/providers/image_none.py` — PIL text overlay |
| Task_007 | 2 | step-clip-tdd | `video/steps/step3_clip.py` — per-slide ffmpeg compositor |
| Task_008 | 2 | step-bookend-tdd | `video/steps/step4_bookend.py` — playwright HTML→clip |
| Task_009 | 2 | step-concat-tdd | `video/steps/step5_concat.py` — final concat + BGM |
| Task_010 | 2 | templates | `video/templates/*.html` — intro/outro HTML templates |
| Task_011 | 3 | pipeline-main-tdd | `video/pipeline.py` — main sequential loop |
| Task_012 | 1 | config-update | `config.yaml` video: section |
| Task_013 | 4 | orchestrate-hook | Wire video into `scripts/orchestrate.py` |
| Task_014 | 4 | integration-test | End-to-end test against real data |

Each task folder contains: `role.md`, `recipe.md`, `status.txt`, `output.md`, `action_log.jsonl`, `feedback.md`

---

## Pipeline Architecture Summary

```
Source MD
  └─► scripts/orchestrate.py
        └─► [if video.enabled: true]
              └─► video/pipeline.py
                    ├─► Step 1: TTS (edge-tts → WAV per slide)
                    ├─► Step 2: Image (PIL text overlay → PNG per slide)
                    ├─► Step 3: Clip (ffmpeg: PNG + WAV → MP4 per slide)
                    ├─► Step 4: Bookend (playwright: HTML → intro.mp4 + outro.mp4)
                    └─► Step 5: Concat (ffmpeg: all clips → final.mp4 + optional BGM)
```

State persisted to `output/<run_id>/video_progress.json` after every step.
Resume on restart skips completed clips.

---

## Provider Abstraction (Phase 1 → Phase 2 upgrade path)

| Provider type | Phase 1 | Phase 2 |
|--------------|---------|---------|
| TTS | `EdgeTtsProvider` (cloud, free) | `FishSpeechProvider` (local, 16GB VRAM) |
| Image | `NoneImageProvider` (PIL overlay) | `ComfyUIImageProvider` (AI generated) |

Switch via `config.yaml`:

```yaml
video:
  tts:
    backend: edge-tts   # → fish-speech in Phase 2
  image:
    backend: none       # → comfyui in Phase 2
```

---

## Config Schema (video: section)

Full spec in `docs/research/VIDEO_PIPELINE_SPEC.md` §5. Key fields:

```yaml
video:
  enabled: false          # default off — zero overhead when false
  backend: basic          # basic | local-hq | cloud-image
  channel_name: ""
  tagline: ""
  cta_text: ""
  tts:
    backend: edge-tts
    language: zh-TW
  image:
    backend: none
  ffmpeg:
    fps: 30
    width: 1920
    height: 1080
  bgm:
    enabled: false
    file: ""
    volume: 0.15
```

---

## Reading Order (new contributor)

1. `docs/research/RATIONALE.md` — understand why
2. `docs/research/VIDEO_PIPELINE_SPEC.md` — understand what
3. `case/00_Constitution/core.md` — understand constraints
4. `case/01_Roadmap/roadmap.md` — understand order
5. `case/QUICKSTART.md` (agent) or `case/FOR_HUMAN.md` (human) — understand how to work
