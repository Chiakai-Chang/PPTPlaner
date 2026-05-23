# PPTPlaner Video Pipeline — Roadmap
> READ-ONLY for Layer 3 agents.

---

## Phase 1 MVP — Sequential Tasks

Tasks MUST be executed in dependency order. Parallel execution within a batch is permitted.

### Batch 0: Design (no dependencies)
| Task | Slug | Description |
|------|------|-------------|
| Task_001 | sdd-interfaces | Write Python ABCs for TTS, Image providers |
| Task_002 | bdd-feature-specs | Write Gherkin feature specs for all major behaviors |

### Batch 1: Core infrastructure (depends on Task_001)
| Task | Slug | Description |
|------|------|-------------|
| Task_003 | checkpoint-tdd | TDD: checkpoint.py — state persistence |
| Task_004 | progress-tdd | TDD: progress.py — CLI progress display |
| Task_005 | tts-edge-tdd | TDD: providers/tts_edge.py — Edge-TTS wrapper |
| Task_006 | image-none-tdd | TDD: providers/image_none.py — PIL text overlay |
| Task_012 | config-update | Add video: section to config.yaml |

### Batch 2: Pipeline steps (depends on Batch 1)
| Task | Slug | Description |
|------|------|-------------|
| Task_007 | step-clip-tdd | TDD: steps/step3_clip.py — per-slide ffmpeg compositor |
| Task_008 | step-bookend-tdd | TDD: steps/step4_bookend.py — playwright HTML→clip |
| Task_009 | step-concat-tdd | TDD: steps/step5_concat.py — final concat + BGM |
| Task_010 | templates | HTML intro/outro template design + implementation |

### Batch 3: Main pipeline (depends on Batch 2)
| Task | Slug | Description |
|------|------|-------------|
| Task_011 | pipeline-main-tdd | TDD: pipeline.py — main sequential loop |

### Batch 4: Integration (depends on Batch 3)
| Task | Slug | Description |
|------|------|-------------|
| Task_013 | orchestrate-hook | Wire video pipeline into scripts/orchestrate.py |
| Task_014 | integration-test | End-to-end integration test with sample data |

---

## Dependency Graph

```
T001 ─┬─► T003 ─┬─► T007 ─┬─► T011 ─► T013 ─► T014
      │         ├─► T008 ─┤
      │         ├─► T009 ─┘
      ├─► T004 ─┘
      ├─► T005 ─► T007
      └─► T006 ─► T007

T002  (parallel, no blocking dependency)
T010  (parallel with T007-T009, feeds T008 template expectations)
T012  (parallel with Batch 1)
```

---

## Output File Map

At completion of all tasks, these files MUST exist:

```
video/
├── __init__.py
├── constants.py
├── pipeline.py
├── checkpoint.py
├── progress.py
├── steps/
│   ├── __init__.py
│   ├── step1_tts.py
│   ├── step2_image.py
│   ├── step3_clip.py
│   ├── step4_bookend.py
│   └── step5_concat.py
├── providers/
│   ├── __init__.py
│   ├── base.py              ← ABCs (Task_001)
│   ├── tts_edge.py
│   └── image_none.py
└── templates/
    ├── yt_intro_default.html
    └── yt_outro_default.html

tests/video/
├── __init__.py
├── features/                ← BDD .feature files (Task_002)
├── test_checkpoint.py
├── test_progress.py
├── test_tts_edge.py
├── test_image_none.py
├── test_step_clip.py
├── test_step_bookend.py
├── test_step_concat.py
└── test_pipeline.py
```
