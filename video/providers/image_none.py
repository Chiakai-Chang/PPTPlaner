"""None Image Provider — PIL Text Overlay.

Generates 1920x1080 PNG with dark gradient background, title, and bullet points.
No AI, no network, no GPU required.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from video.providers.base import ImageProvider, ImageProviderError


class NoneImageProvider(ImageProvider):
    """PIL-based text overlay image provider."""

    def __init__(
        self,
        bg_color: tuple[int, int, int] = (20, 25, 40),
        title_color: tuple[int, int, int] = (255, 255, 255),
        bullet_color: tuple[int, int, int] = (200, 210, 230),
    ) -> None:
        self.bg_color = bg_color
        self.title_color = title_color
        self.bullet_color = bullet_color

    def name(self) -> str:
        return "none"

    def generate(
        self,
        title: str,
        bullets: list[str],
        output_png: Path,
        width: int = 1920,
        height: int = 1080,
    ) -> None:
        """Generate visual frame PNG with title and bullet points."""
        try:
            img = Image.new("RGB", (width, height), self.bg_color)
            draw = ImageDraw.Draw(img)

            # Try to load a system font; fall back to default
            try:
                title_font = ImageFont.truetype("arial.ttf", 72)
                bullet_font = ImageFont.truetype("arial.ttf", 40)
            except OSError:
                title_font = ImageFont.load_default()
                bullet_font = ImageFont.load_default()

            # Draw title (centered in upper third)
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_w = title_bbox[2] - title_bbox[0]
            title_x = (width - title_w) // 2
            title_y = height // 6
            draw.text((title_x, title_y), title, fill=self.title_color, font=title_font)

            # Draw bullets (below title, middle section)
            bullet_y = title_y + 100
            bullet_x = width // 4
            for bullet in bullets:
                text = f"• {bullet}"
                draw.text((bullet_x, bullet_y), text, fill=self.bullet_color, font=bullet_font)
                bullet_y += 60

            output_png.parent.mkdir(parents=True, exist_ok=True)
            img.save(str(output_png), "PNG")

        except Exception as e:
            raise ImageProviderError(f"Image generation failed: {e}") from e

