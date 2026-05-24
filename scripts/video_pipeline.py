#!/usr/bin/env python
"""Standalone Video Pipeline Generator.

This script generates videos from existing presentation output.
It can run independently without regenerating slides.

Usage:
    # Basic usage (uses config.yaml defaults)
    python scripts/video_pipeline.py

    # Specify project root
    python scripts/video_pipeline.py --project-root /path/to/PPTPlaner

    # Override output directory
    python scripts/video_pipeline.py --output-dir ./my_video_output

    # Override config file
    python scripts/video_pipeline.py --config ./my_config.yaml

    # Force regeneration (ignore checkpoints)
    python scripts/video_pipeline.py --force

    # Dry run (show what would be done)
    python scripts/video_pipeline.py --dry-run
"""

import argparse
import sys
from pathlib import Path

import yaml


# Ensure project root is in Python path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(
        description="Generate video from PPTPlaner presentation output"
    )
    parser.add_argument(
        "--project-root", "-p",
        type=Path, default=ROOT,
        help="Path to PPTPlaner project root"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path, default=None,
        help="Output directory for video files"
    )
    parser.add_argument(
        "--config", "-c",
        type=Path, default=None,
        help="Config file path (default: project root config.yaml)"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force regeneration, ignoring checkpoints"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing"
    )
    parser.add_argument(
        "--enable-video",
        action="store_true",
        help="Force enable video generation (bypass config.yaml check)"
    )
    parser.add_argument(
        "--slides-dir",
        type=Path, default=None,
        help="Override slides directory path"
    )
    parser.add_argument(
        "--notes-dir",
        type=Path, default=None,
        help="Override notes directory path"
    )

    args = parser.parse_args()

    # Debug output
    print(f"DEBUG: argv = {sys.argv}")
    print(f"DEBUG: ALL ARGS = {vars(args)}")
    print(f"DEBUG: args.output_dir type = {type(args.output_dir)}")
    print(f"DEBUG: args.output_dir value = {args.output_dir}")

    # Ensure output_dir is properly set (already Path from argparse, but ensure)
    if args.output_dir:
        args.output_dir = Path(str(args.output_dir))
        print(f"DEBUG: output_dir converted to {args.output_dir}")

    # Load config
    config_path = args.config or (args.project_root / "config.yaml")
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        print("Please create config.yaml with video section enabled.")
        sys.exit(1)

    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    # Check if video is enabled (unless --enable-video flag is used)
    if not args.enable_video and not config.get("video", {}).get("enabled", False):
        print("Video generation is disabled.")
        print("Enable it by setting video.enabled: true in config.yaml")
        print("Or use --enable-video flag to bypass this check.")
        sys.exit(1)

    # Validate required directories
    # If output-dir is specified, look for slides/ and notes/ inside it
    if args.output_dir:
        slides_dir = args.slides_dir or (args.output_dir / "slides")
        notes_dir = args.notes_dir or (args.output_dir / "notes")
    else:
        # Default: look in output/slides and output/notes
        slides_dir = args.slides_dir or (args.project_root / "output" / "slides")
        notes_dir = args.notes_dir or (args.project_root / "output" / "notes")
    
    # Debug: print what we're looking for
    print(f"DEBUG: output_dir = {args.output_dir}")
    print(f"DEBUG: slides_dir = {slides_dir}")
    print(f"DEBUG: notes_dir = {notes_dir}")

    if not slides_dir.exists():
        print(f"Error: Slides directory not found: {slides_dir}")
        print(f"  Looking for: {slides_dir}")
        print(f"  Output dir: {args.output_dir}")
        print(f"  Project root: {args.project_root}")
        print(f"  Slides dir arg: {args.slides_dir}")
        print("Please run orchestrate.py first to generate slides.")
        sys.exit(1)

    if not notes_dir.exists():
        print(f"Error: Notes directory not found: {notes_dir}")
        print("Please run orchestrate.py first to generate notes.")
        sys.exit(1)

    # Count available content
    slide_files = list(slides_dir.glob("*.md"))
    note_files = list(notes_dir.glob("*.md"))

    print(f"\n📊 Found {len(slide_files)} slides and {len(note_files)} notes")

    if not slide_files:
        print("No slide files found. Cannot generate video.")
        sys.exit(1)

    if args.dry_run:
        print("\n🔍 DRY RUN MODE - Showing what would be generated:")
        print("-" * 60)
        for slide in sorted(slide_files):
            print(f"  📄 {slide.name}")
        print("-" * 60)
        print("\nUse --no-dry-run to actually generate the video.")
        sys.exit(0)

    # Run video pipeline
    print("\n🎬 Starting video generation...")
    print("-" * 60)

    from video.pipeline import run_video_pipeline

    try:
        output = run_video_pipeline(
            project_root=args.project_root,
            config=config,
            output_dir=args.output_dir,
        )

        if output:
            print(f"\n✅ Video generated: {output}")
            print(f"   Size: {output.stat().st_size:,} bytes")
            return 0
        else:
            print("\n⚠️  Video generation returned no output.")
            print("   Check config.yaml and try again.")
            return 1

    except Exception as e:
        print(f"\n❌ Video generation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
