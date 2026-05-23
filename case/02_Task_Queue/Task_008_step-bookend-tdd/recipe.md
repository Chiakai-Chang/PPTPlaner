# Recipe: Task_008 — TDD: steps/step4_bookend.py

## 1. Objective
Implement step4_bookend.py: renders Jinja2 HTML templates using playwright (headless chromium screenshot), produces PNG frames, then uses ffmpeg to compose a static mp4 clip of specified duration.

## 2. Input Sources
- case/00_Constitution/core.md
- video/steps/step3_clip.py (Task_007) — reuse compose_clip or ffmpeg patterns
- docs/research/VIDEO_PIPELINE_SPEC.md — Section 7 (template Jinja2 variables)

## 3. Output Specification

Write tests/video/test_step_bookend.py FIRST:
- test_render_intro_calls_jinja: mock Jinja2 environment, verify template rendered with correct vars (channel_name, tagline, video_title)
- test_render_outro_calls_jinja: same for outro vars (cta_text, subscribe_hint, next_video_text)
- test_playwright_screenshot_called: mock playwright sync_api, verify page.screenshot() called
- test_output_clip_produced: with mocked playwright+ffmpeg, verify output mp4 path returned
- test_missing_template_raises: FileNotFoundError if template file does not exist

Then implement video/steps/step4_bookend.py:

def generate_bookend_clip(
    template_path: Path,
    template_vars: dict,
    output_mp4: Path,
    duration_sec: int,
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
) -> Path:
    """
    Render HTML template → playwright screenshot → ffmpeg still-image clip.
    template_vars dict passed to Jinja2 render.
    Duration controlled via ffmpeg -t flag.
    Returns output_mp4 path.
    """

## 4. Local Definition of Done
- [ ] tests/video/test_step_bookend.py with all 5 tests passing
- [ ] Uses Jinja2 for template rendering (not f-strings)
- [ ] Uses playwright sync_api for screenshot (not subprocess)
- [ ] Uses ffmpeg (subprocess) for PNG → mp4
- [ ] All mocks isolate unit from real playwright/ffmpeg

## 5. Constraints
- playwright screenshot must set viewport to {width: 1920, height: 1080}
- Temp PNG file written to system temp dir, deleted after ffmpeg completes
- Template file must exist; raise FileNotFoundError if missing

## 6. Escalation Trigger
Escalate if playwright chromium is not installed (check: playwright install chromium --dry-run).
