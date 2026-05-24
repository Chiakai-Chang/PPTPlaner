"""Tests for RunningHub Image Provider."""

from pathlib import Path
from unittest import mock
import pytest
import httpx

from video.providers.image_runninghub import RunningHubProvider
from video.providers.base import ImageProviderError


class TestRunningHubProvider:
    """Test suite for RunningHubProvider."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider = RunningHubProvider(api_key="test_key", workflow_id="test_workflow")

    def test_implements_abc(self):
        """Test that RunningHubProvider implements ImageProvider interface."""
        from video.providers.base import ImageProvider
        assert isinstance(self.provider, ImageProvider)

    def test_name_returns_runninghub(self):
        """Test that name property returns correct value."""
        assert self.provider.name == "runninghub"

    def test_init_requires_api_key(self):
        """Test that initialization requires API key."""
        with pytest.raises(ImageProviderError) as exc_info:
            RunningHubProvider(api_key="", workflow_id="test")

        assert "RunningHub API key required" in str(exc_info.value)

    def test_generate_submits_task(self, tmp_path):
        """Test that generate submits task correctly."""
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            "task_id": "test_123",
            "download_url": "http://example.com/image.png"
        }
        mock_response.raise_for_status = mock.Mock()

        with mock.patch.object(self.provider, '_client') as mock_client:
            mock_client.post.return_value = mock_response
            mock_client.get.return_value = mock.Mock()
            mock_client.get.return_value.raise_for_status = mock.Mock()
            mock_client.get.return_value.content = b"fake_image_data"
            
            self.provider._wait_for_task = mock.Mock()
            self.provider.generate("Test prompt", [], tmp_path / "output.png")

            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[1]["json"]["inputs"]["prompt"] == "Test prompt"

    def test_wait_for_task_completed(self):
        """Test that wait_for_task handles completion."""
        mock_response = mock.Mock()
        mock_response.json.return_value = {"status": "completed"}
        mock_response.raise_for_status = mock.Mock()

        with mock.patch.object(self.provider, '_client') as mock_client:
            mock_client.get.return_value = mock_response
            self.provider._wait_for_task("test_123")  # Should not raise

    def test_wait_for_task_failed(self):
        """Test that wait_for_task raises on failure."""
        mock_response = mock.Mock()
        mock_response.json.return_value = {"status": "failed", "error": "Test error"}
        mock_response.raise_for_status = mock.Mock()

        with mock.patch.object(self.provider, '_client') as mock_client:
            mock_client.get.return_value = mock_response
            with pytest.raises(ImageProviderError) as exc_info:
                self.provider._wait_for_task("test_123")

        assert "Task test_123 failed" in str(exc_info.value)

    def test_api_error_handling(self, tmp_path):
        """Test that API errors are properly handled."""
        mock_response = mock.Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status = mock.Mock(side_effect=httpx.HTTPStatusError(
            "Error",
            request=mock.Mock(),
            response=mock_response
        ))

        with mock.patch.object(self.provider, '_client') as mock_client:
            mock_client.post.return_value = mock_response
            with pytest.raises(ImageProviderError) as exc_info:
                self.provider.generate("Test", [], tmp_path / "output.png")

        assert "Invalid RunningHub API key" in str(exc_info.value)
