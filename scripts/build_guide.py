import os
import sys
import argparse
import re
import base64
import mimetypes
from pathlib import Path
from markdown_it import MarkdownIt

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    from jinja2 import Environment, FileSystemLoader
    JINJA_AVAILABLE = True
except ImportError:
    JINJA_AVAILABLE = False

def render_html(pages, templates_dir, project_info):
    if not JINJA_AVAILABLE:
        print("[Warning] Jinja2 not found. Using basic HTML rendering.", flush=True)
        html = f"<html><head><title>{project_info.get('title', 'Guide')}</title></head><body>"
        html += f"<h1>{project_info.get('title', 'Guide')}</h1>"
        html += f"<p>{project_info.get('summary', '')}</p>"
        html += f"<div>{project_info.get('overview_html', '')}</div>"
        for page in pages:
            html += f"<h1>Slide {page['id']}</h1><div>{page['slide_content_html']}</div>"
            html += f"<h2>Notes</h2><div>{page['note_content']['html']}</div><hr>"
        html += "</body></html>"
        return html

    env = Environment(loader=FileSystemLoader(templates_dir, encoding='utf-8'))
    template = env.get_template("guide.html.j2")
    return template.render(pages=pages, project_info=project_info)

def render_markdown(pages, project_info):
    md = f"# {project_info.get('title', 'Guide')}\n\n"
    if project_info.get('author_info_text'):
        md += f"{project_info.get('author_info_text')}\n"
    if project_info.get('source_url'):
        md += f"Source: [{project_info.get('source_url')}]({project_info.get('source_url')})\n"
    
    md += f"\n## Summary\n{project_info.get('summary', '')}\n"
    
    if project_info.get('overview_md'):
        md += f"\n## Overview\n{project_info.get('overview_md')}\n"
    
    md += "\n---\n"
    
    for page in pages:
        md += f"\n# Slide {page['id']}\n\n"
        md += f"## Slide Content\n\n{page['slide_content_raw']}\n\n"
        md += f"## Speaker Notes\n\n{page['note_content_raw']}\n\n"
        md += "---\n"
        
    return md

def main():
    parser = argparse.ArgumentParser(description="Build HTML and Markdown guide from slides and notes.")
    parser.add_argument("--output-dir", required=True, help="The unique output directory for the run.")
    parser.add_argument("--manual-source-url", help="Optional source URL to override or supplement overview.md")
    args = parser.parse_args()

    try:
        output_dir = Path(args.output_dir)
        slides_dir = output_dir / "slides"
        notes_dir = output_dir / "notes"
        output_path_html = output_dir / "guide.html"
        output_path_md = output_dir / "guide.md"
        templates_dir = Path(__file__).resolve().parents[1] / "templates"
        md_parser = MarkdownIt('commonmark', {'html': True})

        print(f"Building guides for directory: {output_dir}", flush=True)

        # --- Project Info ---
        overview_path = output_dir / "overview.md"
        project_info = {
            "title": output_dir.name.split('_', 1)[-1].replace('_', ' '),
            "summary": "This guide displays the generated slides and notes.",
            "overview_html": "",
            "overview_md": ""
        }
        
        if overview_path.exists():
            overview_content = overview_path.read_text(encoding="utf-8")
            
            # 1. Parse Title (First H1)
            title_match = re.search(r"^#\s+(.+)$", overview_content, re.MULTILINE)
            if title_match:
                project_info["title"] = title_match.group(1).strip()

            # 2. Parse Author
            author_match = re.search(r"\*\*Author:\*\*\s*(.+)$", overview_content, re.MULTILINE)
            authors = author_match.group(1).strip() if author_match else None

            # 3. Parse Source URL (Priority: Argument > File)
            source_url = args.manual_source_url
            if not source_url:
                source_match = re.search(r"\*\*Source:\*\*\s*(.+)$", overview_content, re.MULTILINE)
                source_url = source_match.group(1).strip() if source_match else None
            
            project_info["source_url"] = source_url

            # 4. Parse Summary (Flexible Header)
            summary_match = re.search(r"##\s+(?:Summary|摘要).*?\n(.*?)(?=\n##|\Z)", overview_content, re.DOTALL | re.IGNORECASE)
            if summary_match:
                project_info["summary"] = summary_match.group(1).strip()

            # 5. Parse Overview (Flexible Header)
            overview_match = re.search(r"##\s+(?:Overview|總覽).*?\n(.*?)(?=\n##|\Z)", overview_content, re.DOTALL | re.IGNORECASE)
            if overview_match:
                overview_md_content = overview_match.group(1).strip()
                project_info["overview_md"] = overview_md_content
                project_info["overview_html"] = md_parser.render(overview_md_content)

            # Construct Author Text
            author_text = f"By {authors}" if authors and authors != 'N/A' else ""
            project_info["author_info_text"] = author_text

        if not slides_dir.exists():
            print(f"Build skipped: '{slides_dir.name}' directory not found in {output_dir}.", flush=True)
            if overview_path.exists():
                html_content = render_html([], templates_dir, project_info)
                output_path_html.write_text(html_content, encoding="utf-8")
                md_content = render_markdown([], project_info)
                output_path_md.write_text(md_content, encoding="utf-8")
            sys.exit(0)

        slide_files = sorted([f for f in os.listdir(slides_dir) if f.endswith('.md')])
        
        pages = []
        for slide_file in slide_files:
            try:
                base_name = slide_file.rsplit('.', 1)[0]
                slide_id = base_name.split('_')[0]
                
                slide_path = slides_dir / slide_file
                note_file_name = f"note-{base_name}-zh.md"
                note_path = notes_dir / note_file_name

                # Find SVGs or Raster Images
                slide_svg_file = slides_dir / f"slide_{slide_id}.svg"
                conceptual_svg_file = slides_dir / f"conceptual_{slide_id}.svg"

                slide_visual_content = None
                
                if slide_svg_file.exists():
                    svg_text = slide_svg_file.read_text(encoding="utf-8")
                    svg_text = re.sub(r'\s(width|height)="[^"]*"', '', svg_text)
                    slide_visual_content = svg_text
                else:
                    for ext in ['.png', '.jpg', '.jpeg', '.webp']:
                        img_file = slides_dir / f"slide_{slide_id}{ext}"
                        if img_file.exists():
                            mime_type, _ = mimetypes.guess_type(img_file)
                            if not mime_type: mime_type = f"image/{ext.replace('.', '')}"
                            with open(img_file, "rb") as f:
                                b64_data = base64.b64encode(f.read()).decode('utf-8')
                                slide_visual_content = f'<img src="data:{mime_type};base64,{b64_data}" style="width:100%; height:auto;" alt="Slide {slide_id}">'
                            break

                conceptual_svg_content = None
                if conceptual_svg_file.exists():
                    conceptual_svg_content = conceptual_svg_file.read_text(encoding="utf-8")

                slide_content_raw = slide_path.read_text(encoding="utf-8") if slide_path.exists() else "[Slide not found]"
                slide_content_html = md_parser.render(slide_content_raw)

                raw_note_content = note_path.read_text(encoding="utf-8") if note_path.exists() else "[Note not found]"
                
                # Sanitize Note Content for HTML
                clean_note_content = re.sub(r"^```(?:markdown)?\s*", "", raw_note_content, flags=re.IGNORECASE)
                clean_note_content = re.sub(r"\s*```\s*$", "", clean_note_content)
                html_note_content = md_parser.render(clean_note_content)

                pages.append({
                    "id": slide_id,
                    "slide_content_raw": slide_content_raw,
                    "slide_content_html": slide_content_html,
                    "note_content_raw": clean_note_content,
                    "note_content_html": html_note_content,
                    "slide_svg_content": slide_visual_content,
                    "conceptual_svg_content": conceptual_svg_content,
                })
            except IndexError:
                print(f"[Warning] Could not parse filename: {slide_file}", flush=True)

        if not pages and not overview_path.exists():
            print("[Warning] No pages or overview were processed to build the guide.", flush=True)
            return

        # Render HTML
        html_content = render_html(pages, templates_dir, project_info)
        output_path_html.write_text(html_content, encoding="utf-8")
        
        # Render Markdown
        md_content = render_markdown(pages, project_info)
        output_path_md.write_text(md_content, encoding="utf-8")

    except Exception as e:
        print(f"[ERROR] An unexpected error occurred in build_guide.py: {e}", file=sys.stderr, flush=True)
        sys.exit(1)

    except Exception as e:
        print(f"[ERROR] An unexpected error occurred in build_guide.py: {e}", file=sys.stderr, flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()