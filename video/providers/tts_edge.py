"""Edge-TTS Provider — Text-to-Speech via Microsoft Edge."""
from __future__ import annotations

from pathlib import Path

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    edge_tts = None
    HAS_EDGE_TTS = False

from video.providers.base import TtsProvider, TtsProviderError


class EdgeTtsProvider(TtsProvider):
    """Edge-TTS provider implementing TtsProvider ABC."""

    def __init__(
        self,
        voice: str = "zh-TW-HsiaoChenNeural",
        speed: str = "+0%",
    ) -> None:
        if not HAS_EDGE_TTS:
            raise ImportError(
                "edge-tts not installed. Run: pip install edge-tts"
            )
        self.voice = voice
        self.speed = speed

    def name(self) -> str:
        return "edge-tts"

    def generate(
        self,
        text: str,
        output_wav: Path,
        language: str = "zh-TW",
    ) -> None:
        """Synthesize text to WAV using Edge-TTS."""
        if not text or not text.strip():
            raise ValueError("Text must not be empty or whitespace-only")

        output_wav.parent.mkdir(parents=True, exist_ok=True)

        try:
            import asyncio
            communicate = edge_tts.Communicate(
                text,
                voice=self.voice,
                rate=self.speed,
            )
            
            async def _stream_audio_and_subs():
                submaker = edge_tts.SubMaker()
                has_word_boundaries = False
                
                with open(output_wav, "wb") as f:
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            f.write(chunk["data"])
                        elif chunk["type"] == "WordBoundary":
                            has_word_boundaries = True
                            submaker.create_sub(
                                (chunk["start"], chunk["duration"]),
                                chunk["text"],
                            )
                
                if has_word_boundaries:
                    srt_path = output_wav.with_suffix(".srt")
                    srt_content = submaker.generate_subs()
                    srt_path.write_text(srt_content, encoding="utf-8")

            try:
                asyncio.run(_stream_audio_and_subs())
            except Exception:
                # Fallback to standard save if streaming fails
                asyncio.run(communicate.save(str(output_wav)))
        except Exception as e:
            raise TtsProviderError(
                f"Edge-TTS generation failed: {e}"
            ) from e

