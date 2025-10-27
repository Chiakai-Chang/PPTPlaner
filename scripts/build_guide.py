import os
import sys
import argparse
from pathlib import Path
from markdown_it import MarkdownIt

try:
    from jinja2 import Environment, FileSystemLoader
    JINJA_AVAILABLE = True
except ImportError:
    JINJA_AVAILABLE = False

def render_html(pages, templates_dir):
    if not JINJA_AVAILABLE:
        print("[Warning] Jinja2 not found. Using basic HTML rendering.", flush=True)
        html = "<html><head><title>Guide</title></head><body>"
        for page in pages:
            html += f"<h1>Slide {page['id']}</h1><pre>{page['slide_content']}</pre>"
            html += f"<h2>Notes</h2><pre>{page['note_content']['raw']}</pre><hr>"
        html += "</body></html>"
        return html

    env = Environment(loader=FileSystemLoader(templates_dir, encoding='utf-8'))
    template = env.get_template("guide.html.j2")
    return template.render(pages=pages)

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

        print(f"Building guide for directory: {output_dir}", flush=True)

        if not slides_dir.exists() or not notes_dir.exists():
            print(f"Build skipped: '{slides_dir.name}' or '{notes_dir.name}' directory not found in {output_dir}.", flush=True)
            sys.exit(0)

        slide_files = sorted([f for f in os.listdir(slides_dir) if f.endswith('.md')])
        md = MarkdownIt()
        
        pages = []
        for slide_file in slide_files:
            try:
                base_name = slide_file.rsplit('.', 1)[0]
                slide_id = base_name.split('_')[0]
                note_file_name = f"note-{base_name}-zh.md"
                
                slide_path = slides_dir / slide_file
                note_path = notes_dir / note_file_name

                slide_content = slide_path.read_text(encoding="utf-8") if slide_path.exists() else "[Slide not found]"
                raw_note_content = note_path.read_text(encoding="utf-8") if note_path.exists() else "[Note not found]"
                html_note_content = md.render(raw_note_content)

                pages.append({
                    "id": slide_id,
                    "slide_content": slide_content,
                    "note_content": {
                        "raw": raw_note_content,
                        "html": html_note_content
                    }
                })
            except IndexError:
                print(f"[Warning] Could not parse filename: {slide_file}", flush=True)

        if not pages:
            print("[Warning] No pages were processed to build the guide.", flush=True)
            return

        html_content = render_html(pages, templates_dir)
        output_path.write_text(html_content, encoding="utf-8")

    except Exception as e:
        print(f"[ERROR] An unexpected error occurred in build_guide.py: {e}", file=sys.stderr, flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
