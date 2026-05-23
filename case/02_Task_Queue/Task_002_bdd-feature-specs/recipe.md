# Recipe: Task_002 — BDD: Feature Specifications

## 1. Objective
Write Gherkin .feature files covering all major behaviors of the video pipeline. These serve as living documentation and test blueprints for TDD tasks.

## 2. Input Sources
- case/00_Constitution/core.md
- case/01_Roadmap/roadmap.md
- docs/research/VIDEO_PIPELINE_SPEC.md — Sections 4, 5

## 3. Output Specification
Create directory tests/video/features/ and write these 7 files:

**tests/video/features/checkpoint.feature** — scenarios: initial state creation, mark step done, mark step failed, resume skips completed slides, concurrent session isolation.

**tests/video/features/tts_generation.feature** — scenarios: generate WAV from plain text, WAV file written to correct path, TTS failure raises TtsProviderError, empty text raises ValueError.

**tests/video/features/image_generation.feature** — scenarios: generate PNG with title and bullets, dimensions match config (1920x1080), image failure raises ImageProviderError, output path parent created if missing.

**tests/video/features/clip_composition.feature** — scenarios: PNG+WAV produces mp4 clip, clip duration matches WAV duration, ffmpeg not in PATH raises RuntimeError with friendly message.

**tests/video/features/bookend_generation.feature** — scenarios: intro clip generated from template+config, outro clip generated from template+config, missing logo path handled gracefully.

**tests/video/features/pipeline_sequential.feature** — scenarios: slides processed in order 01→02→N, completed clips skipped on restart, failed slide logged and pipeline continues to next, progress line printed per slide.

**tests/video/features/final_concat.feature** — scenarios: clips concatenated as intro+slides+outro, BGM mixed when bgm_file is set, no BGM when bgm_file is null, output mp4 exists and is non-zero size.

Each .feature file must have Feature: header and at least 3 Scenario: blocks in Given-When-Then format.
Also create tests/video/__init__.py (empty).

## 4. Local Definition of Done
- [ ] tests/video/features/ directory created with all 7 .feature files
- [ ] Each file has Feature: header and >= 3 Scenario: blocks
- [ ] All scenarios use Given/When/Then keywords
- [ ] No Python code in .feature files
- [ ] tests/video/__init__.py exists

## 5. Constraints
- Gherkin syntax only in .feature files
- Scenarios must be self-contained (no cross-scenario state)
- Do NOT write step definition Python files — that is done in TDD tasks

## 6. Escalation Trigger
Escalate if a behavior in VIDEO_PIPELINE_SPEC.md cannot be expressed as a testable Given-When-Then scenario.
