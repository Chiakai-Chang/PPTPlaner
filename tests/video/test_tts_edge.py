"""Tests for video/providers/tts_edge.py — TDD."""
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from video.providers.base import TtsProvider, TtsProviderError


def import_edge():
    from video.providers.tts_edge import EdgeTtsProvider
    return EdgeTtsProvider


def test_implements_abc():
    EdgeTtsProvider = import_edge()
    provider = EdgeTtsProvider()
    assert isinstance(provider, TtsProvider)


def test_name_returns_edge_tts():
    EdgeTtsProvider = import_edge()
    provider = EdgeTtsProvider()
    assert provider.name() == "edge-tts"


def test_generate_calls_edge_tts(tmp_path):
    EdgeTtsProvider = import_edge()
    provider = EdgeTtsProvider(voice="zh-TW-HsiaoChenNeural")
    output = tmp_path / "test.wav"

    with patch("video.providers.tts_edge.edge_tts") as mock_edge:
        mock_communicate = mock_edge.Communicate
        mock_communicate.return_value.save.return_value = None
        provider.generate("你好世界", output, "zh-TW")
        mock_communicate.assert_called_once_with(
            "你好世界", voice="zh-TW-HsiaoChenNeural", rate="+0%"
        )


def test_generate_writes_wav(tmp_path):
    EdgeTtsProvider = import_edge()
    provider = EdgeTtsProvider()
    output = tmp_path / "output.wav"

    with patch("video.providers.tts_edge.edge_tts") as mock_edge:
        mock_communicate = mock_edge.Communicate
        mock_instance = mock_communicate.return_value

        def fake_save(path):
            Path(path).write_bytes(b"fake wav data")

        mock_instance.save.side_effect = fake_save
        provider.generate("test", output, "zh-TW")
        assert output.exists()


def test_generate_failure_raises(tmp_path):
    EdgeTtsProvider = import_edge()
    provider = EdgeTtsProvider()
    output = tmp_path / "fail.wav"

    with patch("video.providers.tts_edge.edge_tts") as mock_edge:
        mock_edge.Communicate.return_value.save.side_effect = RuntimeError("network error")
        with pytest.raises(TtsProviderError):
            provider.generate("test", output, "zh-TW")


def test_empty_text_raises(tmp_path):
    EdgeTtsProvider = import_edge()
    provider = EdgeTtsProvider()
    output = tmp_path / "empty.wav"
    with pytest.raises(ValueError):
        provider.generate("", output, "zh-TW")


def test_whitespace_text_raises(tmp_path):
    EdgeTtsProvider = import_edge()
    provider = EdgeTtsProvider()
    output = tmp_path / "ws.wav"
    with pytest.raises(ValueError):
        provider.generate("   ", output, "zh-TW")

