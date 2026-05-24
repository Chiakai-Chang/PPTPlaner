"""RunningHub Image Provider.

Cloud-based AI image generation via RunningHub API.
No GPU required - uses FLUX on RunningHub servers.
"""

from __future__ import annotations

import logging
from pathlib import Path

import httpx

from video.providers.base import ImageProvider, ImageProviderError

logger = logging.getLogger(__name__)


class RunningHubProvider(ImageProvider):
    """RunningHub API image generation provider."""

    API_BASE = "https://www.runninghub.cn/api"

    def __init__(
        self,
        api_key: str,
        workflow_id: str,
        timeout: float = 120.0,
    ) -> None:
        """
        Initialize RunningHub provider.

        Args:
            api_key: RunningHub API key
            workflow_id: Workflow ID on RunningHub
            timeout: Request timeout in seconds
        """
        if not api_key:
            raise ImageProviderError(
                "RunningHub API key required. "
                "Get one at: https://www.runninghub.cn/"
            )

        self.api_key = api_key
        self.workflow_id = workflow_id
        self._client = httpx.Client(
            base_url=self.API_BASE,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )

    @property
    def name(self) -> str:
        return "runninghub"

    def _translate_prompt(self, text: str) -> str:
        """
        Translate Chinese prompt to English.

        RunningHub/FLUX works better with English prompts.
        Uses a simple heuristic for now; replace with LLM call if needed.
        """
        # Simple approach: use the text as-is if it contains English
        # For production, integrate an LLM translation step
        if any(ord(c) > 127 for c in text):
            logger.warning(
                "Chinese prompt detected. Consider adding LLM translation "
                "for better image quality with RunningHub."
            )
        return text

    def render(
        self,
        text: str,
        output: Path,
        width: int = 1920,
        height: int = 1080,
    ) -> Path:
        """
        Generate image from text via RunningHub API.

        Args:
            text: Image description (Chinese or English)
            output: Output PNG path
            width: Image width
            height: Image height

        Returns:
            Path to generated image

        Raises:
            ImageProviderError: If generation fails
        """
        output.parent.mkdir(parents=True, exist_ok=True)

        prompt = self._translate_prompt(text)

        payload = {
            "workflow_id": self.workflow_id,
            "inputs": {
                "prompt": prompt,
                "width": width,
                "height": height,
            },
        }

        try:
            # Submit generation task
            response = self._client.post("/v1/generate", json=payload)
            response.raise_for_status()
            task_info = response.json()

            task_id = task_info.get("task_id")
            if not task_id:
                raise ImageProviderError(
                    f"No task_id in response: {task_info}"
                )

            # Poll for completion
            logger.info(f"RunningHub task submitted: {task_id}")
            self._wait_for_task(task_id)

            # Download result
            download_url = task_info.get("download_url")
            if not download_url:
                raise ImageProviderError(
                    f"No download URL in task info: {task_info}"
                )

            # Download image
            dl_response = self._client.get(download_url)
            dl_response.raise_for_status()
            output.write_bytes(dl_response.content)

            logger.info(
                f"Image generated: {output} ({output.stat().st_size} bytes)"
            )
            return output

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ImageProviderError(
                    "Invalid RunningHub API key. "
                    "Check your config.yaml settings."
                ) from e
            raise ImageProviderError(
                f"RunningHub API error {e.response.status_code}: "
                f"{e.response.text}"
            ) from e
        except Exception as e:
            raise ImageProviderError(f"RunningHub generation failed: {e}") from e

    def _wait_for_task(self, task_id: str) -> None:
        """Wait for task to complete."""
        import time

        max_wait = 300  # 5 minutes
        start = time.time()

        while time.time() - start < max_wait:
            response = self._client.get(f"/v1/tasks/{task_id}")
            response.raise_for_status()
            status = response.json().get("status")

            if status == "completed":
                return
            elif status in ("failed", "error"):
                raise ImageProviderError(
                    f"Task {task_id} failed: {response.json()}"
                )

            time.sleep(5)

        raise ImageProviderError(
            f"Task {task_id} timed out after {max_wait}s"
        )

    def close(self) -> None:
        """Close HTTP client."""
        self._client.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass
