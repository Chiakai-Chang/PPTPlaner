# Findings

## Project Structure
- PPTPlaner runs on Windows 11
- Uses `scripts/orchestrate.py` as main entry point
- Has `print_header`, `print_success`, `print_info`, `print_warning`, `print_error` utility functions
- Config loaded from `config.yaml` via `get_config()`
- Output goes to `output/<run_id>/`
- Slides: `slides/{page}_{topic}.md`
- Notes: `notes/note-{page}_{topic}-zh.md`

## Dependencies
- edge-tts, Pillow, Jinja2, playwright — Phase 1 Python deps
- ffmpeg — system dependency
- pytest — already in dev deps

## No slides/ or notes/ directories exist yet
- Integration test (T014) will need to handle this gracefully
- Pipeline must work with empty or missing directories

