import os
import sys
from pathlib import Path

def main():
    print("Running validation...")
    # This is a placeholder for a more robust validation script.
    # For now, it just checks for basic file existence.
    slides_dir = Path("slides")
    notes_dir = Path("notes")

    if not slides_dir.exists() or not notes_dir.exists():
        print("Validation skipped: slides or notes directory not found.")
        return

    slide_files = sorted(os.listdir(slides_dir))
    note_files = sorted(os.listdir(notes_dir))

    if len(slide_files) != len(note_files):
        print(f"[WARNING] Mismatch in file count: {len(slide_files)} slides vs {len(note_files)} notes.")
    
    print("Validation finished.")

if __name__ == "__main__":
    main()