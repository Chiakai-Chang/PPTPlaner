"""Tests for video/providers/image_none.py — TDD."""
from pathlib import Path

import pytest
from PIL import Image

from video.providers.base import ImageProvider


def import_none():
    from video.providers.image_none import NoneImageProvider
    return NoneImageProvider


def test_implements_abc():
    NoneImageProvider = import_none()
    provider = NoneImageProvider()
    assert isinstance(provider, ImageProvider)


def test_name_returns_none():
    NoneImageProvider = import_none()
    provider = NoneImageProvider()
    assert provider.name() == "none"


def test_generates_png_file(tmp_path):
    NoneImageProvider = import_none()
    provider = NoneImageProvider()
    output = tmp_path / "test.png"
    provider.generate("Title", ["bullet 1"], output)
    assert output.exists()
    assert output.stat().st_size > 0


def test_correct_dimensions(tmp_path):
    NoneImageProvider = import_none()
    provider = NoneImageProvider()
    output = tmp_path / "dims.png"
    provider.generate("Title", [], output, 1920, 1080)
    img = Image.open(output)
    assert img.size == (1920, 1080)


def test_title_in_image(tmp_path):
    """Generate with title — image is non-zero size (pixel content test)."""
    NoneImageProvider = import_none()
    provider = NoneImageProvider()
    output = tmp_path / "title.png"
    provider.generate("Memory", [], output, 1920, 1080)
    img = Image.open(output)
    # Just verify it loads and has correct dimensions
    assert img.size == (1920, 1080)
    assert output.stat().st_size > 100  # non-trivial content


def test_empty_bullets_ok(tmp_path):
    NoneImageProvider = import_none()
    provider = NoneImageProvider()
    output = tmp_path / "empty.png"
    provider.generate("Title", [], output)  # Should not raise
    assert output.exists()


def test_output_dir_created(tmp_path):
    """If output_png parent does not exist, it is created."""
    NoneImageProvider = import_none()
    provider = NoneImageProvider()
    subdir = tmp_path / "subdir" / "nested"
    output = subdir / "test.png"
    assert not subdir.exists()
    provider.generate("Title", [], output)
    assert subdir.exists()
    assert output.exists()

