"""Translation Module for Video Pipeline.

Provides Chinese to English translation for AI image generation prompts.
Supports multiple translation modes: heuristic, llm, or none.
"""

from __future__ import annotations

import logging
from enum import Enum

from video.providers.base import ImageProviderError

logger = logging.getLogger(__name__)


class TranslationMode(Enum):
    """Translation mode options."""
    NONE = "none"
    HEURISTIC = "heuristic"
    LLM = "llm"


def translate_prompt(
    text: str,
    mode: str = "heuristic",
    llm_api_key: str | None = None,
    llm_model: str | None = None,
) -> str:
    """
    Translate text to English for AI image generation.

    Args:
        text: Input text (Chinese or English)
        mode: Translation mode (none, heuristic, llm)
        llm_api_key: API key for LLM translation (if mode=llm)
        llm_model: Model name for LLM translation

    Returns:
        Translated text in English

    Raises:
        ImageProviderError: If LLM translation fails
    """
    if not text:
        return text

    mode = TranslationMode(mode.lower() if isinstance(mode, str) else mode.value)

    if mode == TranslationMode.NONE:
        return text

    if mode == TranslationMode.HEURISTIC:
        return _translate_heuristic(text)

    if mode == TranslationMode.LLM:
        if not llm_api_key:
            raise ImageProviderError(
                "LLM API key required for llm translation mode. "
                "Set llm_api_key in config.yaml."
            )
        return _translate_llm(text, llm_api_key, llm_model)

    raise ImageProviderError(f"Unknown translation mode: {mode}")


def _translate_heuristic(text: str) -> str:
    """
    Heuristic translation (placeholder).

    This is a simple heuristic approach that doesn't actually translate.
    For production, use LLM mode or integrate with a translation API.

    Returns the original text with a warning.
    """
    # Check if text contains Chinese characters
    has_chinese = any(ord(c) > 127 for c in text)

    if has_chinese:
        logger.warning(
            "Heuristic translation mode cannot translate Chinese. "
            "Use 'llm' mode with API key for accurate translation."
        )
        # Return original text (will still work, just not optimal)
        return text

    return text


def _translate_llm(
    text: str,
    api_key: str,
    model: str = "gemini-1.5-pro",
) -> str:
    """
    LLM-based translation.

    Args:
        text: Input text
        api_key: API key for LLM
        model: Model name

    Returns:
        Translated text

    Raises:
        ImageProviderError: If translation fails
    """
    try:
        import google.generativeai as genai  # type: ignore
    except ImportError:
        raise ImageProviderError(
            "google-generativeai package required for LLM translation. "
            "Run: pip install google-generativeai"
        )

    genai.configure(api_key=api_key)

    prompt = f"""
    Translate the following text to English for AI image generation.
    Keep it concise and descriptive. Only return the translation.

    Input: {text}
    Translation:
    """

    try:
        model = genai.GenerativeModel(model)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        raise ImageProviderError(
            f"LLM translation failed: {e}"
        ) from e
