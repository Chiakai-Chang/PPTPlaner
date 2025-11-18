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

            # Get Title from YAML
            project_info["title"] = metadata.get("document_title", project_info["title"])

            # Get Summary from YAML or Body
            summary = metadata.get("summary")
            if not summary:
                summary_match = re.search(r"##\s摘要\s\(Summary\)\n\n(.*?)(?=\n\n##|\Z)", body_content, re.DOTALL)
                if summary_match:
                    summary = summary_match.group(1).strip()
            project_info["summary"] = summary or "This guide displays the generated slides and notes side-by-side."

            # Get Overview HTML from YAML or Body
            overview_parts = []
            authors = metadata.get("document_authors")
            pub_info = metadata.get("publication_info")
            if authors and pub_info and authors != 'N/A' and pub_info != 'N/A':
                overview_parts.append(f"<p><em>By {authors}, {pub_info}</em></p>")
            
            overview_md = metadata.get("overview")
            if not overview_md:
                overview_match = re.search(r"##\s總覽\s\(Overview\)\n\n(.*?)(?=\n\n##|\Z)", body_content, re.DOTALL)
                if overview_match:
                    overview_md = overview_match.group(1).strip()

            if overview_md:
                overview_parts.append(md.render(overview_md))
            
            project_info["overview_html"] = "\n".join(overview_parts)

        if not slides_dir.exists() or not notes_dir.exists():
            print(f"Build skipped: '{slides_dir.name}' or '{notes_dir.name}' directory not found in {output_dir}.", flush=True)
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
                note_file_name = f"note-{base_name}-zh.md"
                
                slide_path = slides_dir / slide_file
                note_path = notes_dir / note_file_name

                slide_content_raw = slide_path.read_text(encoding="utf-8") if slide_path.exists() else "[Slide not found]"
                slide_match = re.search(r'^```(?:markdown)?\n(.*?)\n```$', slide_content_raw, re.DOTALL | re.IGNORECASE)
                slide_content_to_render = slide_match.group(1).strip() if slide_match else slide_content_raw
                slide_content_html = md.render(slide_content_to_render)

                raw_note_content = note_path.read_text(encoding="utf-8") if note_path.exists() else "[Note not found]"
                match = re.search(r'^```(?:markdown)?\n(.*?)\n```$', raw_note_content, re.DOTALL | re.IGNORECASE)
                content_to_render = match.group(1).strip() if match else raw_note_content
                html_note_content = md.render(content_to_render)

                pages.append({
                    "id": slide_id,
                    "slide_content_html": slide_content_html,
                    "note_content": {
                        "raw": raw_note_content,
                        "html": html_note_content
                    }
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