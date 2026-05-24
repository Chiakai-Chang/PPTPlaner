"""Tests for ComfyUI Image Provider."""

from pathlib import Path
from unittest import mock
import pytest
import httpx

from video.providers.image_comfyui import ComfyUIProvider
from video.providers.base import ImageProviderError


class TestComfyUIProvider:
    """Test suite for ComfyUIProvider."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider = ComfyUIProvider(url="http://test:8188", workflow_file="test_workflow.json")
        self.provider._workflow = {"node1": {"class_type": "CLIPTextEncode", "inputs": {"text": ""}}}

    def test_implements_abc(self):
        """Test that ComfyUIProvider implements ImageProvider interface."""
        from video.providers.base import ImageProvider
        assert isinstance(self.provider, ImageProvider)

    def test_name_returns_comfyui(self):
        """Test that name property returns correct value."""
        assert self.provider.name == "comfyui"

    def test_update_workflow_prompt(self):
        """Test that workflow prompt is updated correctly."""
        workflow = {"node1": {"class_type": "CLIPTextEncode", "inputs": {"text": ""}}}
        updated = self.provider._update_workflow_prompt(workflow, "Test prompt")

        assert updated["node1"]["inputs"]["text"] == "Test prompt"

    def test_submit_prompt_calls_api(self):
        """Test that prompt submission makes correct API call."""
        mock_response = mock.Mock()
        mock_response.json.return_value = {"prompt_id": "test_123"}
        mock_response.raise_for_status = mock.Mock()

        with mock.patch.object(self.provider, '_client') as mock_client:
            mock_client.post.return_value = mock_response
            result = self.provider._submit_prompt({})

            mock_client.post.assert_called_once()
            assert result == "test_123"

    def test_poll_for_completion(self):
        """Test that polling waits for completion."""
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            "test_123": {
                "outputs": {
                    "node1": {
                        "images": [{"filename": "test.png", "subfolder": "", "type": "output"}]
                    }
                }
            }
        }
        mock_response.raise_for_status = mock.Mock()

        with mock.patch.object(self.provider, '_client') as mock_client:
            mock_client.get.return_value = mock_response
            result = self.provider._poll_for_completion("test_123")

        assert result == "test.png"

    def test_generate_calls_submit_and_poll(self, tmp_path):
        """Test that generate calls submit and poll methods."""
        # Setup mocks
        self.provider._load_workflow = mock.Mock(return_value={"node1": {"class_type": "CLIPTextEncode", "inputs": {"text": ""}}})
        self.provider._submit_prompt = mock.Mock(return_value="test_123")
        self.provider._poll_for_completion = mock.Mock(return_value="test.png")
        self.provider._download_image = mock.Mock()

        output_path = tmp_path / "output.png"
        output_path.touch()  # Create the file so stat works

        with mock.patch.object(self.provider, '_client'):
            self.provider.generate("Test prompt", [], output_path)

        self.provider._submit_prompt.assert_called_once()
        self.provider._poll_for_completion.assert_called_once_with("test_123")

    def test_workflow_not_found(self):
        """Test that missing workflow file raises error."""
        provider = ComfyUIProvider(workflow_file="nonexistent.json")

        with pytest.raises(ImageProviderError) as exc_info:
            provider._load_workflow()

        assert "Workflow file not found" in str(exc_info.value)
