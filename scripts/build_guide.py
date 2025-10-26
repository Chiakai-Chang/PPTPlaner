import os
import sys
import argparse
from pathlib import Path

# Add a simple way to use Jinja2 if available, otherwise use basic string formatting
try:
    from jinja2 import Environment, FileSystemLoader
    JINJA_AVAILABLE = True
except ImportError:
    JINJA_AVAILABLE = False

def render_html(pages):
    if not JINJA_AVAILABLE:
        print("[Warning] Jinja2 not found. Using basic HTML rendering.")
        html = "<html><head><title>Guide</title></head><body>"
        for page in pages:
            html += f"<h1>Slide {page['id']}</h1><pre>{page['slide_content']}</pre>"
            html += f"<h2>Notes</h2><pre>{page['note_content']}</pre><hr>"
        html += "</body></html>"
        return html

    env = Environment(loader=FileSystemLoader('templates', encoding='utf-8'))
    template = env.get_template("guide.html.j2")
    return template.render(pages=pages)

def main():
    parser = argparse.ArgumentParser(description="Build HTML guide from slides and notes.")
    parser.add_argument("--output-dir", required=True, help="The unique output directory for the run.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    slides_dir = output_dir / "slides"
    notes_dir = output_dir / "notes"
    output_path = output_dir / "guide.html"

    print(f"Building guide for directory: {output_dir}")

    slide_files = sorted([f for f in os.listdir(slides_dir) if f.endswith('.md')])
    
    pages = []
    for slide_file in slide_files:
        try:
            base_name = slide_file.rsplit('.', 1)[0]
            slide_id = base_name.split('_')[0]
            # Correctly construct the note file name including the language suffix
            note_file_name = f"note-{base_name}-zh.md"
            
            slide_path = slides_dir / slide_file
            note_path = notes_dir / note_file_name

            slide_content = slide_path.read_text(encoding="utf-8") if slide_path.exists() else "[Slide not found]"
            note_content = note_path.read_text(encoding="utf-8") if note_path.exists() else "[Note not found]"

            pages.append({
                "id": slide_id,
                "slide_content": slide_content,
                "note_content": note_content
            })
        except IndexError:
            print(f"[Warning] Could not parse filename: {slide_file}")

    html_content = render_html(pages)
    output_path = Path("guide.html")
    output_path.write_text(html_content, encoding="utf-8")
    print(f"Successfully created {output_path}")

if __name__ == "__main__":
    main()