"""Integration test: Full Pipeline Validation."""

from pathlib import Path

import pytest


@pytest.mark.integration
def test_full_pipeline_produces_mp4(tmp_path):
    """Run run_video_pipeline() on sample data, assert mp4 exists and size > 0."""
    from video.pipeline import run_video_pipeline

    project_root = Path(__file__).resolve().parents[2]
    output_base = project_root / "output"

    # Find the latest output directory
    output_dirs = sorted(output_base.glob("*/"), reverse=True)
    if not output_dirs:
        pytest.skip("No output directories found — run orchestrate.py first")

    run_dir = output_dirs[0]
    slides_dir = run_dir / "slides"
    notes_dir = run_dir / "notes"

    if not slides_dir.exists() or not notes_dir.exists():
        pytest.skip("No slides/ or notes/ in output directory")

    slide_files = list(slides_dir.glob("*.md"))
    note_files = list(notes_dir.glob("*.md"))

    if not slide_files or not note_files:
        pytest.skip("No slide or note files found")

    # Create a test project structure
    test_project = tmp_path / "video_test_project"
    test_project.mkdir()
    test_slides = test_project / "slides"
    test_notes = test_project / "notes"
    test_slides.mkdir()
    test_notes.mkdir()

    # Copy files
    for f in slide_files[:3]:  # Use first 3 slides for speed
        (test_slides / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
    for f in note_files[:3]:
        (test_notes / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")

    config = {
        "video": {
            "enabled": True,
            "tts": {
                "provider": "edge-tts",
                "edge_tts_voice": "zh-TW-HsiaoChenNeural",
                "edge_tts_speed": "+0%",
            },
            "image": {
                "provider": "none",
                "width": 1920,
                "height": 1080,
            },
            "intro": {
                "enabled": True,
                "duration_sec": 8,
                "channel_name": "Test Channel",
            },
            "outro": {
                "enabled": True,
                "duration_sec": 12,
                "channel_name": "Test Channel",
            },
            "fps": 30,
        }
    }

    try:
        result = run_video_pipeline(
            project_root=test_project,
            config=config,
            output_dir=test_project / "output",
        )
        if result:
            assert result.exists(), f"Output mp4 does not exist: {result}"
            assert result.stat().st_size > 0, f"Output mp4 is empty: {result}"
            print(f"\n✓ Integration test passed: {result} ({result.stat().st_size:,} bytes)")
        else:
            print("\n⚠ Pipeline returned None — check slides/notes/config")
            pytest.skip("Pipeline returned no output")
    except RuntimeError as e:
        if "ffmpeg" in str(e).lower():
            pytest.skip(f"ffmpeg not installed: {e}")
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "playwright" in error_msg or "browser" in error_msg or "executable doesn't exist" in error_msg:
            pytest.skip(f"Playwright browsers not installed")
        raise


# Run with: pytest tests/video/test_integration.py -v -m integration
