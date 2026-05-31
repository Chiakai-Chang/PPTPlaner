# PPTPlaner Cross-Platform Support & Architecture Documentation

This document records the architectural structure of the **PPTPlaner** project and details the cross-platform and agent optimization decisions implemented to align the system with the **OmniHeal** philosophy.

---

## 1. Project Directory & File Architecture

The following tree represents the clean, refactored directory layout of the PPTPlaner project:

```
PPTPlaner/
├── agents/                       # AI Agent Adapter Abstraction Layer
│   ├── __init__.py               # Package initializer & exports
│   ├── antigravity.py            # Antigravity CLI (agy) Adapter (Cross-platform PTY)
│   ├── base.py                   # Unified AgentInterface base class
│   ├── claude.py                 # Claude CLI adapter
│   ├── error_parser.py           # Standardized error mapping
│   ├── exceptions.py             # Domain-specific agent errors
│   ├── factory.py                # AgentFactory (creates agents dynamically)
│   ├── logging_config.py         # Advanced ResearchLogger & Timers
│   ├── model_detector.py         # Automated API/Server endpoint scan
│   ├── openai_compatible.py      # OpenAI-Compatible adapter (local LLMs)
│   ├── openai_direct.py          # Direct OpenAI API adapter
│   ├── performance.py            # Execution timing & metrics
│   ├── registry.py               # Singleton Agent Registry
│   └── retry.py                  # Intelligent backoff & retry loops
│
├── archive/                      # Archived Legacy Files
│   └── orchestrate_old.py        # Old orchestrator script (kept for audit history)
│
├── audit/                        # Comprehensive Audit Logs
│   ├── AUDIT_REPORT.md           # Comprehensive scan findings (v3.9.1)
│   ├── FINDINGS_AGY_AGENT.md     # Agy CLI error diagnostic report
│   └── PROGRESS.md               # Audit remediation progress log (100% Completed)
│
├── docs/                         # Specifications & Developer Manuals
│   ├── AGENT_MIGRATION_BDD.md    # BDD feature specs for agent adapters
│   ├── AGENT_MIGRATION_PLAN.md   # Initial migration strategy
│   ├── AGENT_MIGRATION_SDD.md    # System design specs for agent factory
│   ├── AGENT_MIGRATION_TDD.md    # TDD test plans
│   ├── CROSS_PLATFORM_SUPPORT.md # This architecture & cross-platform guide
│   └── HEALTH_CHECK_REPORT.md    # Older scanner results (v3.9.0)
│
├── scripts/                      # Core Executables & GUI Tools
│   ├── prompts/                  # 15+ System & QA Validation Prompts (.md)
│   ├── build_guide.py            # HTML presentation compilation script
│   ├── orchestrate.py            # Primary CLI coordinator (Phase 1-5 loop)
│   ├── run_combiner_ui.py        # Slide Combiner Tkinter UI (Cross-platform)
│   └── config_migrator.py        # Automated config version migrator
│
├── video/                        # Video Generation Pipeline (Phase 6)
│   ├── providers/                # Audio & Image generation services
│   │   ├── base.py               # ABC interfaces for TTS/Images
│   │   ├── tts_edge.py           # Edge-TTS provider (Safe lazy imports)
│   │   └── image_none.py         # Text-based PIL image generator
│   ├── steps/                    # Modular ffmpeg composition steps
│   └── pipeline.py               # Core orchestrator for mp4 generation
│
├── tests/                        # Full TDD/BDD Unit & Integration Test Suites
│   ├── conftest.py               # Shared pytest fixtures & mocks
│   ├── test_agent_factory.py     # Adapter factory verification
│   └── video/                    # Pipeline & step level TDD tests (100% Mocked)
│
├── config.yaml                   # Core configuration file
├── launcher.py                   # Pre-flight checklist & launcher (Python 3.12+)
├── pyproject.toml                # Unified PEP 621 package metadata
└── requirements.txt              # Standard pip dependencies file
```

---

## 2. Key Cross-Platform Optimization Decisions

### A. PEP 508 Platform Dependency Markers
- **Problem**: `pywinpty` is a native Windows C-extension that fails to install on macOS/Linux. Previously, this blocked non-Windows environments from completing the setup stage.
- **Solution**: Reconfigured `pyproject.toml` and `requirements.txt` to isolate `pywinpty` with environment markers:
  `"pywinpty>=3.0.0; sys_platform == 'win32'"`
  This installs `pywinpty` automatically on Windows, but lets non-Windows platforms skip it cleanly.

### B. Dual-Engine Pseudo-Terminal (PTY) Abstraction
- **Problem**: The successor CLI agent `agy` requires a TTY to output answers, which standard `subprocess.PIPE` redirects fail to support.
- **Solution**: Developed a dual-engine execution model inside `agents/antigravity.py`:
  1. **Windows**: Uses `winpty.PtyProcess` to create a Windows console session.
  2. **macOS/Linux**: Uses Python's standard library `pty` module to spawn native Unix pseudo-terminals (`pty.openpty()`), yielding a TTY session without any external dependencies.

### C. Safe Subprocess creationflags
- **Problem**: Passing `creationflags=subprocess.CREATE_NO_WINDOW` directly in `subprocess.Popen` is a Windows-only feature and throws a fatal `TypeError` on macOS/Linux.
- **Solution**: Extracted popen arguments to a dynamic dictionary in `scripts/run_combiner_ui.py`:
  ```python
  popen_kwargs = {
      "stdout": subprocess.PIPE,
      "stderr": subprocess.STDOUT,
      "text": True,
      "encoding": "utf-8",
  }
  if sys.platform == "win32":
      popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
  process = subprocess.Popen(command, **popen_kwargs)
  ```

### D. Lazy Imports and Test Collection Resilience
- **Problem**: Pytest test collection was completely broken in environments lacking `edge-tts` due to module-level imports raising immediate `ImportError`.
- **Solution**:
  1. Updated `video/providers/tts_edge.py` to catch `ImportError` gracefully at module-level:
     ```python
     try:
         import edge_tts
         HAS_EDGE_TTS = True
     except ImportError:
         edge_tts = None
         HAS_EDGE_TTS = False
     ```
     The exception is deferred until `EdgeTtsProvider` is instantiated, allowing safe imports.
  2. Integrated `pytest.importorskip("edge_tts")` at the beginning of `tests/video/test_tts_edge.py` and wrapped integration tests with `pytest.mark.skipif(not HAS_EDGE_TTS, ...)` to skip gracefully instead of crashing during tests collection.

---

## 3. Retro-Alignment against OmniHeal Philosophy

Through these improvements, the PPTPlaner project achieves strong alignment with the 4 pillars of the **OmniHeal** philosophy:
1. **Zero Install**: Clean git clone works natively on all 3 major OS platforms without compiler errors.
2. **Never Interrupt**: Dynamic platform adjustments prevent fatal Python type-check errors at runtime.
3. **Precision First**: Duplicate except clauses, dead code variables, and deprecated/legacy root executables have been cleared.
4. **Task Recovery**: Integrated checks safeguard files from invalid empty inputs.
