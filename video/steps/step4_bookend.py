"""Step 4: Render bookend clips from Jinja2 HTML templates."""

import subprocess
import tempfile
from pathlib import Path

from jinja2 import Environment as Jinja2Environment
from jinja2 import FileSystemLoader
from playwright.sync_api import sync_playwright


class BookendError(Exception):
    """Raised when bookend generation fails."""
    pass


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

    1. Load and render Jinja2 template with template_vars
    2. Use Playwright (headless Chromium) to take a screenshot
    3. Use ffmpeg to create a static mp4 clip of duration_sec

    Returns output_mp4 path.

    Raises:
        FileNotFoundError: If template_path does not exist.
        BookendError: If screenshot or ffmpeg fails.
    """
    # Check template exists
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    # Render template
    template_text = template_path.read_text(encoding="utf-8")
    env = Jinja2Environment(loader=FileSystemLoader(str(template_path.parent)))
    template = env.from_string(template_text)
    html_content = template.render(**template_vars)

    # Write temporary HTML file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    ) as html_file:
        html_file.write(html_content)
        html_file_path = html_file.name

    # Take screenshot with Playwright
    png_path = html_file_path.replace(".html", ".png")
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": height})
            page.goto(f"file://{html_file_path}")
            page.screenshot(path=png_path, full_page=False)
            browser.close()
    except Exception as e:
        raise BookendError(f"Playwright screenshot failed: {e}") from e

    # Generate mp4 from PNG using ffmpeg
    output_mp4.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-loop", "1",
        "-i", png_path,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-t", str(duration_sec),
        "-pix_fmt", "yuv420p",
        "-y",
        str(output_mp4),
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=300)
    except subprocess.CalledProcessError as e:
        stderr_msg = ""
        if e.stderr:
            stderr_msg = e.stderr.decode("utf-8", errors="replace")
        raise BookendError(
            f"ffmpeg failed with code {e.returncode}: {stderr_msg}"
        ) from e

    # Cleanup temp files
    Path(html_file_path).unlink(missing_ok=True)
    Path(png_path).unlink(missing_ok=True)

    return output_mp4
