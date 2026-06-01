"""None Image Provider — PIL Text Overlay & Structured Slide Renderer.

Generates gorgeous 1920x1080 PNG slides from raw Markdown files.
Uses modern dark HSL gradient backgrounds, glowing glassmorphic cards,
structured section layout, wrapped text, and high-quality Chinese system fonts.
"""
from __future__ import annotations

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from video.providers.base import ImageProvider, ImageProviderError


class NoneImageProvider(ImageProvider):
    """PIL-based text overlay and structured presentation slide provider."""

    def __init__(
        self,
        bg_start: tuple[int, int, int] = (10, 15, 30),     # Slate 950
        bg_end: tuple[int, int, int] = (25, 32, 52),       # Slate 900
        accent_color: tuple[int, int, int] = (45, 212, 191), # Teal 400
        text_color: tuple[int, int, int] = (255, 255, 255),  # Pure White
        muted_color: tuple[int, int, int] = (200, 210, 230), # Muted Blue-Gray
    ) -> None:
        self.bg_start = bg_start
        self.bg_end = bg_end
        self.accent_color = accent_color
        self.text_color = text_color
        self.muted_color = muted_color

    def name(self) -> str:
        return "none"

    def _parse_markdown(self, content: str) -> dict:
        """Parse raw markdown slide into structured main title and card sections."""
        lines = content.splitlines()
        main_title = ""
        sections = []
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("# "):
                main_title = line[2:].strip()
            elif line.startswith("## "):
                section_title = line[3:].strip()
                current_section = {"title": section_title, "bullets": []}
                sections.append(current_section)
            elif line.startswith("- ") or line.startswith("* "):
                bullet_text = line[2:].strip()
                if current_section is None:
                    current_section = {"title": "", "bullets": []}
                    sections.append(current_section)
                current_section["bullets"].append(bullet_text)
            else:
                # Treat paragraphs as bullets under the current section
                if current_section is None:
                    current_section = {"title": "", "bullets": []}
                    sections.append(current_section)
                current_section["bullets"].append(line)

        return {"main_title": main_title, "sections": sections}

    def _get_font(self, font_type: str, size: int) -> ImageFont.FreeTypeFont:
        """Attempt to load Microsoft JhengHei on Windows, or fall back to default."""
        font_paths = []
        if os.name == "nt":  # Windows
            if font_type == "bold":
                font_paths.append("C:\\Windows\\Fonts\\msjhbd.ttc")
            font_paths.append("C:\\Windows\\Fonts\\msjh.ttc")
        
        # Fallbacks
        font_paths.append("msjh.ttc")
        if font_type == "bold":
            font_paths.append("arialbd.ttf")
        font_paths.append("arial.ttf")

        for path in font_paths:
            try:
                # For .ttc/.ttf files
                return ImageFont.truetype(path, size)
            except OSError:
                continue

        return ImageFont.load_default()

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
        """Wrap text into lines that fit the max width, supporting Chinese characters."""
        chars = list(text)
        lines = []
        current_line = []
        
        for char in chars:
            current_line.append(char)
            line_text = "".join(current_line)
            bbox = draw.textbbox((0, 0), line_text, font=font)
            w = bbox[2] - bbox[0]
            if w > max_width:
                current_line.pop()
                if current_line:
                    lines.append("".join(current_line))
                current_line = [char]
        
        if current_line:
            lines.append("".join(current_line))
        return lines

    def generate(
        self,
        title: str,
        bullets: list[str],
        output_png: Path,
        width: int = 1920,
        height: int = 1080,
    ) -> None:
        """Generate visual frame PNG with premium gradient, cards and structured layout."""
        try:
            # Create premium background gradient
            img = Image.new("RGB", (width, height), self.bg_start)
            draw = ImageDraw.Draw(img)

            # Draw linear gradient from bg_start to bg_end
            for y in range(height):
                ratio = y / height
                r = int(self.bg_start[0] * (1 - ratio) + self.bg_end[0] * ratio)
                g = int(self.bg_start[1] * (1 - ratio) + self.bg_end[1] * ratio)
                b = int(self.bg_start[2] * (1 - ratio) + self.bg_end[2] * ratio)
                draw.line([(0, y), (width, y)], fill=(r, g, b))

            # Parse markdown slide content
            parsed = self._parse_markdown(title)
            main_title = parsed["main_title"] or "Presentation Slide"
            sections = parsed["sections"]

            # Load fonts
            title_font = self._get_font("bold", 54)
            section_font = self._get_font("bold", 34)
            body_font = self._get_font("regular", 26)

            # Draw Main Title (Upper Top Section)
            title_bbox = draw.textbbox((0, 0), main_title, font=title_font)
            title_w = title_bbox[2] - title_bbox[0]
            title_x = (width - title_w) // 2
            title_y = 60
            
            # Subtle title drop shadow
            draw.text((title_x + 2, title_y + 2), main_title, fill=(5, 8, 15), font=title_font)
            # Main title text
            draw.text((title_x, title_y), main_title, fill=self.text_color, font=title_font)

            # Beautiful gradient accent divider bar under title
            bar_w = min(title_w + 120, width - 200)
            bar_h = 6
            bar_x = (width - bar_w) // 2
            bar_y = title_y + 85
            draw.rounded_rectangle(
                [bar_x, bar_y, bar_x + bar_w, bar_y + bar_h],
                radius=3,
                fill=self.accent_color,
            )

            # Draw Structured Card Grid
            num_sections = len(sections)
            if num_sections == 0:
                # Fallback if no sections exist
                sections = [{"title": "", "bullets": ["No content available"]}]
                num_sections = 1

            # Grid calculation parameters
            grid_y = bar_y + 50
            grid_h = height - grid_y - 80
            padding = 40

            if num_sections == 1:
                col_widths = [width - 200]
                col_xs = [100]
            elif num_sections == 2:
                w_col = (width - 200 - padding) // 2
                col_widths = [w_col, w_col]
                col_xs = [100, 100 + w_col + padding]
            else:
                # 3 columns limit side-by-side, overflow goes down if large, but fit first 3
                cols = min(num_sections, 3)
                w_col = (width - 200 - (cols - 1) * padding) // cols
                col_widths = [w_col] * cols
                col_xs = [100 + i * (w_col + padding) for i in range(cols)]

            # Draw each section inside a glassmorphic container card
            for i, sec in enumerate(sections[:3]):  # Limit to 3 columns to avoid overlap
                col_w = col_widths[i]
                col_x = col_xs[i]

                card_box = [col_x, grid_y, col_x + col_w, grid_y + grid_h]

                # Draw glowing container card background
                # Rich dark card background with glowing border
                draw.rounded_rectangle(
                    card_box,
                    radius=16,
                    fill=(20, 28, 48),  # Slate 800-like
                    outline=(60, 75, 100),  # Glow color
                    width=2,
                )

                # Draw Card Header (Section Title)
                sec_title = sec["title"]
                text_y = grid_y + 35
                
                if sec_title:
                    # Draw a nice colored indicator bar on the left of section title
                    indicator_w = 6
                    indicator_h = 30
                    draw.rounded_rectangle(
                        [col_x + 30, text_y + 2, col_x + 30 + indicator_w, text_y + 2 + indicator_h],
                        radius=2,
                        fill=self.accent_color,
                    )
                    
                    draw.text(
                        (col_x + 48, text_y),
                        sec_title,
                        fill=self.text_color,
                        font=section_font,
                    )
                    text_y += 65
                else:
                    text_y += 10

                # Draw Bullet Points inside the card
                bullet_start_x = col_x + 35
                for bullet in sec["bullets"]:
                    # Draw custom bullet point icon (colored elegant dot)
                    bullet_radius = 5
                    bullet_center_y = text_y + 16
                    draw.ellipse(
                        [
                            bullet_start_x,
                            bullet_center_y - bullet_radius,
                            bullet_start_x + bullet_radius * 2,
                            bullet_center_y + bullet_radius,
                        ],
                        fill=self.accent_color,
                    )

                    # Wrap text to fit card column width safely
                    max_text_w = col_w - 85
                    wrapped_lines = self._wrap_text(bullet, body_font, max_text_w, draw)
                    
                    for line in wrapped_lines:
                        draw.text(
                            (bullet_start_x + 25, text_y),
                            line,
                            fill=self.muted_color,
                            font=body_font,
                        )
                        text_y += 42
                    
                    # Space between bullets
                    text_y += 12

            output_png.parent.mkdir(parents=True, exist_ok=True)
            img.save(str(output_png), "PNG")

        except Exception as e:
            raise ImageProviderError(f"Image generation failed: {e}") from e
