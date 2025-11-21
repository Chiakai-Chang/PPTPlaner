import os
import sys
import argparse
import re
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

def main():
    parser = argparse.ArgumentParser(description="Build HTML guide from slides and notes.")
    parser.add_argument("--output-dir", required=True, help="The unique output directory for the run.")
    args = parser.parse_args()

    try:
        output_dir = Path(args.output_dir)
        slides_dir = output_dir / "slides"
        notes_dir = output_dir / "notes"
        output_path = output_dir / "guide.html"
        templates_dir = Path(__file__).resolve().parents[1] / "templates"
        md = MarkdownIt('commonmark', {'html': True})

        print(f"Building guide for directory: {output_dir}", flush=True)

        # --- Project Info ---
        overview_path = output_dir / "overview.md"
        project_info = {
            "title": output_dir.name.split('_', 1)[-1].replace('_', ' '),
            "summary": "This guide displays the generated slides and notes side-by-side.",
            "overview_html": ""
        }
        
        if overview_path.exists():
            overview_content = overview_path.read_text(encoding="utf-8")
            metadata = {}
            body_content = overview_content

            if YAML_AVAILABLE and overview_content.startswith('---'):
                try:
                    _, front_matter_str, body_content = overview_content.split('---', 2)
                    metadata = yaml.safe_load(front_matter_str)
                except (ValueError, yaml.YAMLError) as e:
                    print(f"[Warning] Could not parse YAML front matter from overview.md: {e}", flush=True)

            project_info["title"] = metadata.get("document_title", project_info["title"])
            summary = metadata.get("summary")
            if not summary:
                summary_match = re.search(r"##\s摘要\s\(Summary\)\n\n(.*?)(?=\n\n##|\Z)", body_content, re.DOTALL)
                if summary_match:
                    summary = summary_match.group(1).strip()
            project_info["summary"] = summary or "This guide displays the generated slides and notes side-by-side."

            authors = metadata.get("document_authors")
            pub_info = metadata.get("publication_info")
            project_info["author_info_text"] = f"By {authors}, {pub_info}" if authors and pub_info and authors != 'N/A' and pub_info != 'N/A' else ""

            overview_md = metadata.get("overview")
            if not overview_md:
                overview_match = re.search(r"##\s總覽\s\(Overview\)\n\n(.*?)(?=\n\n##|\Z)", body_content, re.DOTALL)
                if overview_match:
                    overview_md = overview_match.group(1).strip()
            project_info["overview_html"] = md.render(overview_md) if overview_md else ""

        if not slides_dir.exists():
            print(f"Build skipped: '{slides_dir.name}' directory not found in {output_dir}.", flush=True)
            if overview_path.exists():
                html_content = render_html([], templates_dir, project_info)
                output_path.write_text(html_content, encoding="utf-8")
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

                # Find SVGs
                slide_svg_file = slides_dir / f"slide_{slide_id}.svg"
                conceptual_svg_file = slides_dir / f"conceptual_{slide_id}.svg"

                slide_svg_content = None
                if slide_svg_file.exists():
                    svg_text = slide_svg_file.read_text(encoding="utf-8")
                    # Remove width and height attributes to make it responsive
                    svg_text = re.sub(r'\s(width|height)="[^"]*"', '', svg_text)
                    slide_svg_content = svg_text
                
                conceptual_svg_content = None
                if conceptual_svg_file.exists():
                    # For conceptual SVGs, we preserve the attributes so they can render with their natural aspect ratio.
                    conceptual_svg_content = conceptual_svg_file.read_text(encoding="utf-8")

                slide_content_raw = slide_path.read_text(encoding="utf-8") if slide_path.exists() else "[Slide not found]"
                slide_content_html = md.render(slide_content_raw)

                raw_note_content = note_path.read_text(encoding="utf-8") if note_path.exists() else "[Note not found]"
                html_note_content = md.render(raw_note_content)

                pages.append({
                    "id": slide_id,
                    "slide_content_html": slide_content_html,
                    "note_content_html": html_note_content,
                    "slide_svg_content": slide_svg_content,
                    "conceptual_svg_content": conceptual_svg_content,
                })
            except IndexError:
                print(f"[Warning] Could not parse filename: {slide_file}", flush=True)

        if not pages and not overview_path.exists():
            print("[Warning] No pages or overview were processed to build the guide.", flush=True)
            return

        html_content = render_html(pages, templates_dir, project_info)
        output_path.write_text(html_content, encoding="utf-8")

    except Exception as e:
        print(f"[ERROR] An unexpected error occurred in build_guide.py: {e}", file=sys.stderr, flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()