"""Tests for Fish Speech TTS Provider."""

from pathlib import Path
from unittest import mock
import pytest
import httpx

from video.providers.tts_fish import FishSpeechProvider
from video.providers.base import TtsProviderError


class TestFishSpeechProvider:
    """Test suite for FishSpeechProvider."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider = FishSpeechProvider(url="http://test:8080")

    def test_implements_abc(self):
        """Test that FishSpeechProvider implements TtsProvider interface."""
        from video.providers.base import TtsProvider
        assert isinstance(self.provider, TtsProvider)

    def test_name_returns_fish_speech(self):
        """Test that name property returns correct value."""
        assert self.provider.name == "fish-speech"

    def test_generate_calls_api(self, tmp_path):
        """Test that generate makes correct API call."""
        mock_response = mock.Mock()
        mock_response.content = b"fake_wav_data"
        mock_response.raise_for_status = mock.Mock()

        output_path = tmp_path / "output.wav"

        with mock.patch.object(self.provider, '_client') as mock_client:
            mock_client.post.return_value = mock_response
            self.provider.generate("Test text", output_path)

            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "http://test:8080/v1/audio/speech"
            assert call_args[1]["json"]["input"] == "Test text"
            assert call_args[1]["json"]["response_format"] == "wav"

    def test_generate_writes_wav(self, tmp_path):
        """Test that generate writes WAV file correctly."""
        mock_response = mock.Mock()
        mock_response.content = b"fake_wav_data"
        mock_response.raise_for_status = mock.Mock()

        output_path = tmp_path / "output.wav"

        with mock.patch.object(self.provider, '_client') as mock_client:
            mock_client.post.return_value = mock_response
            self.provider.generate("Test text", output_path)

        assert output_path.exists()
        assert output_path.read_bytes() == b"fake_wav_data"

    def test_generate_failure_raises(self, tmp_path):
        """Test that API errors are properly handled."""
        mock_response = mock.Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.content = b"error"
        mock_response.raise_for_status = mock.Mock(side_effect=httpx.HTTPStatusError(
            "Error",
            request=mock.Mock(),
            response=mock_response
        ))

        with mock.patch.object(self.provider, '_client') as mock_client:
            mock_client.post.return_value = mock_response
            with pytest.raises(TtsProviderError) as exc_info:
                self.provider.generate("Test text", tmp_path / "output.wav")

        assert "Fish Speech API error" in str(exc_info.value)

    def test_empty_text_raises(self, tmp_path):
        """Test that empty text raises an error."""
        with pytest.raises(TtsProviderError) as exc_info:
            self.provider.generate("", tmp_path / "output.wav")

        assert "Empty text provided" in str(exc_info.value)

    def test_whitespace_text_raises(self, tmp_path):
        """Test that whitespace-only text raises an error."""
        with pytest.raises(TtsProviderError) as exc_info:
            self.provider.generate("   ", tmp_path / "output.wav")

        assert "Empty text provided" in str(exc_info.value)

    def test_connect_error_message(self, tmp_path):
        """Test that connection errors provide helpful message."""
        with mock.patch.object(self.provider, '_client') as mock_client:
            mock_client.post.side_effect = httpx.ConnectError("Connection failed")
            with pytest.raises(TtsProviderError) as exc_info:
                self.provider.generate("Test", tmp_path / "output.wav")

        assert "Cannot connect to Fish Speech" in str(exc_info.value)
