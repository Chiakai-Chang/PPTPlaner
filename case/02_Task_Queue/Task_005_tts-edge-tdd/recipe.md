# Recipe: Task_005 — TDD: providers/tts_edge.py

## 1. Objective
Implement Edge-TTS provider that implements TtsProvider ABC. Edge-TTS calls Microsoft's cloud TTS service. Must be mocked in tests.

## 2. Input Sources
- case/00_Constitution/core.md
- video/providers/base.py (Task_001) — TtsProvider ABC
- docs/research/VIDEO_PIPELINE_SPEC.md — Section 5 (tts config schema)

## 3. Output Specification

Write tests/video/test_tts_edge.py FIRST:
- test_implements_abc: EdgeTtsProvider() isinstance of TtsProvider
- test_name_returns_edge_tts: provider.name() == "edge-tts"
- test_generate_calls_edge_tts: mock edge_tts.Communicate, verify called with correct text and voice
- test_generate_writes_wav: after mocked generate, output_wav path exists (use tmp_path fixture)
- test_generate_failure_raises: if edge_tts raises, TtsProviderError is raised instead
- test_empty_text_raises: provider.generate("", ...) raises ValueError

Then implement video/providers/tts_edge.py:

class EdgeTtsProvider(TtsProvider):
    def __init__(self, voice: str = "zh-TW-HsiaoChenNeural", speed: str = "+0%") -> None
    def name(self) -> str  # returns "edge-tts"
    def generate(self, text: str, output_wav: Path, language: str = "zh-TW") -> None
        # Uses edge_tts.Communicate(text, voice=self.voice, rate=self.speed).save(str(output_wav))
        # Wraps exceptions in TtsProviderError
        # Raises ValueError if text is empty or whitespace-only

## 4. Local Definition of Done
- [ ] tests/video/test_tts_edge.py with all 6 tests passing
- [ ] EdgeTtsProvider passes isinstance check against TtsProvider
- [ ] Tests use unittest.mock.patch or pytest-mock to mock edge_tts — no real network calls
- [ ] TtsProviderError raised (not raw edge_tts exception) on failure

## 5. Constraints
- Do NOT call real edge-tts API in tests
- Do NOT hardcode voice or speed — must come from constructor
- edge_tts import wrapped in try/except ImportError with friendly message

## 6. Escalation Trigger
Escalate if edge-tts package API changes (check: import edge_tts; hasattr(edge_tts, 'Communicate')).
