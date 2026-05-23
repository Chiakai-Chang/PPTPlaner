# Recipe: Task_006 — TDD: providers/image_none.py

## 1. Objective
Implement the "none" image provider: generates a 1920x1080 PNG with a dark gradient background, slide title text, and bullet points as text overlay using Pillow. No AI, no network, no GPU.

## 2. Input Sources
- case/00_Constitution/core.md
- video/providers/base.py (Task_001) — ImageProvider ABC

## 3. Output Specification

Write tests/video/test_image_none.py FIRST:
- test_implements_abc: NoneImageProvider() isinstance of ImageProvider
- test_name_returns_none: provider.name() == "none"
- test_generates_png_file: after generate(), output_png exists (tmp_path)
- test_correct_dimensions: PIL.Image.open(output_png).size == (1920, 1080)
- test_title_in_image: generate with title="Memory" — verify image is non-zero size (pixel content test)
- test_empty_bullets_ok: generate with bullets=[] does not raise
- test_output_dir_created: if output_png parent does not exist, it is created

Then implement video/providers/image_none.py:

class NoneImageProvider(ImageProvider):
    def __init__(self, bg_color=(20, 25, 40), title_color=(255,255,255), bullet_color=(200,210,230)) -> None
    def name(self) -> str  # returns "none"
    def generate(self, title: str, bullets: list[str], output_png: Path, width=1920, height=1080) -> None
        # Creates dark background image
        # Draws title in large font (top third of image)
        # Draws bullets below title (middle section)
        # Saves as PNG
        # Creates parent directories if needed

Font fallback: try to load a system font; if not found, use PIL default font (ImageFont.load_default()).

## 4. Local Definition of Done
- [ ] tests/video/test_image_none.py with all 7 tests passing
- [ ] NoneImageProvider passes isinstance check against ImageProvider
- [ ] Output PNG is valid (PIL.Image.open succeeds) and correct size
- [ ] Works without any font file — PIL default font fallback guaranteed

## 5. Constraints
- Only Pillow for image generation — no cairo, no playwright, no ffmpeg
- No external font files required (must work with PIL default)
- Output directory created automatically if missing

## 6. Escalation Trigger
Escalate if Pillow is not installed (check: import PIL; PIL.__version__).
