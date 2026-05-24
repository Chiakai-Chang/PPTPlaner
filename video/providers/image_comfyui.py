"""ComfyUI Image Provider.

Local AI image generation using ComfyUI HTTP API.
Requires GPU with at least 8GB VRAM.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path

import httpx

from video.providers.base import ImageProvider, ImageProviderError

logger = logging.getLogger(__name__)


class ComfyUIProvider(ImageProvider):
    """ComfyUI image generation provider."""

    def __init__(
        self,
        url: str = "http://localhost:8188",
        workflow_file: str = "image_flux.json",
        client_id: str = "pptplaner-video",
        poll_interval: float = 2.0,
        max_poll_time: float = 300.0,
    ) -> None:
        """
        Initialize ComfyUI provider.

        Args:
            url: ComfyUI API URL
            workflow_file: Workflow JSON file path
            client_id: Client ID for API
            poll_interval: Seconds between status polls
            max_poll_time: Maximum time to wait for generation
        """
        self.url = url.rstrip("/")
        self.workflow_file = workflow_file
        self.client_id = client_id
        self.poll_interval = poll_interval
        self.max_poll_time = max_poll_time
        self._client = httpx.Client(timeout=300)
        self._workflow = None

    @property
    def name(self) -> str:
        return "comfyui"

    def _load_workflow(self) -> dict:
        """Load workflow from JSON file."""
        if self._workflow is not None:
            return self._workflow

        workflow_path = Path(self.workflow_file)
        if not workflow_path.exists():
            # Try relative to project root
            workflow_path = Path("video/workflows") / self.workflow_file

        if not workflow_path.exists():
            raise ImageProviderError(
                f"Workflow file not found: {self.workflow_file}. "
                f"Place it in video/workflows/ or provide absolute path."
            )

        self._workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        return self._workflow

    def _update_workflow_prompt(self, workflow: dict, text: str) -> dict:
        """
        Update workflow with generation prompt.

        This finds the CLIPTextEncode nodes and updates their text.
        The exact node IDs depend on your workflow structure.
        """
        # Common node types for text input in FLUX workflows
        for node_id, node in workflow.items():
            if node.get("class_type") in ("CLIPTextEncode", "ConditioningZeroOut"):
                if "inputs" in node and "text" in node["inputs"]:
                    node["inputs"]["text"] = text

        return workflow

    def _submit_prompt(self, workflow: dict) -> str:
        """Submit workflow to ComfyUI. Returns prompt_id."""
        payload = {
            "prompt": workflow,
            "client_id": self.client_id,
        }

        try:
            response = self._client.post(
                f"{self.url}/prompt",
                json=payload,
            )
            response.raise_for_status()
            result = response.json()
            return result["prompt_id"]

        except httpx.ConnectError as e:
            raise ImageProviderError(
                f"Cannot connect to ComfyUI at {self.url}. "
                f"Is ComfyUI running? Run: docker compose -f docker-compose.video.yml up -d"
            ) from e
        except httpx.HTTPStatusError as e:
            raise ImageProviderError(
                f"ComfyUI API error {e.response.status_code}: {e.response.text}"
            ) from e

    def _poll_for_completion(self, prompt_id: str) -> str | None:
        """
        Poll for generation completion.

        Returns:
            Path to generated image filename, or None if failed
        """
        start_time = time.time()

        while time.time() - start_time < self.max_poll_time:
            try:
                response = self._client.get(
                    f"{self.url}/history/{prompt_id}"
                )
                response.raise_for_status()

                history = response.json()
                if prompt_id in history:
                    outputs = history[prompt_id].get("outputs", {})

                    # Find image output
                    for node_id, output in outputs.items():
                        if "images" in output:
                            image_info = output["images"][0]
                            return image_info["filename"]

            except Exception as e:
                logger.warning(f"Poll error: {e}")

            time.sleep(self.poll_interval)

        return None

    def _download_image(self, filename: str, output_path: Path) -> None:
        """Download generated image from ComfyUI."""
        view_url = f"{self.url}/view?filename={filename}&subfolder=&type=output"

        try:
            response = self._client.get(view_url)
            response.raise_for_status()
            output_path.write_bytes(response.content)

        except Exception as e:
            raise ImageProviderError(f"Failed to download image: {e}") from e

    def render(
        self,
        text: str,
        output: Path,
        width: int = 1920,
        height: int = 1080,
    ) -> Path:
        """
        Generate image from text prompt.

        Args:
            text: Image generation prompt (Chinese)
            output: Output PNG path
            width: Image width
            height: Image height

        Returns:
            Path to generated image

        Raises:
            ImageProviderError: If generation fails
        """
        output.parent.mkdir(parents=True, exist_ok=True)

        # Load and update workflow
        workflow = self._load_workflow()
        workflow = self._update_workflow_prompt(workflow, text)

        # Submit prompt
        logger.info(f"Submitting image generation: {text[:50]}...")
        prompt_id = self._submit_prompt(workflow)

        # Poll for completion
        logger.info(f"Waiting for generation (prompt_id: {prompt_id[:8]}...)...")
        filename = self._poll_for_completion(prompt_id)

        if not filename:
            raise ImageProviderError(
                f"Generation timed out after {self.max_poll_time}s. "
                f"Check ComfyUI logs for errors."
            )

        # Download image
        logger.info(f"Downloading image: {filename}")
        self._download_image(filename, output)

        logger.info(f"Image generated: {output} ({output.stat().st_size} bytes)")
        return output

    def close(self) -> None:
        """Close HTTP client."""
        self._client.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass
