# Agent Migration Plan: Gemini CLI to Antigravity CLI

## Executive Summary

**Critical Issue**: PPTPlaner is currently tightly coupled to Gemini CLI (`gemini` command), which Google announced will be deprecated on **June 18, 2026** in favor of Antigravity CLI (`agy` command).

This document outlines the migration strategy and implementation plan to ensure PPTPlaner remains functional and can support multiple AI backends.

---

## Current Architecture

```
┌─────────────────┐
│    UI (run_ui)  │
└────────┬────────┘
         ▼
┌─────────────────┐
│  orchestrate.py │ ──► gemini CLI (hardcoded)
└────────┬────────┘
         ▼
┌─────────────────┐
│   Gemini API    │
└─────────────────┘
```

**Problem Areas:**
1. `config.yaml`: `agent: "gemini"` - hardcoded reference
2. `scripts/orchestrate.py:189`: `run_agent()` invokes `agent_cmd` directly
3. `START_HERE.bat`: Installs `@google/gemini-cli`
4. `README.md`: Documentation references Gemini CLI exclusively

---

## Target Architecture

```
┌─────────────────┐
│    UI (run_ui)  │ ──► Agent Selection Dropdown
└────────┬────────┘
         ▼
┌─────────────────┐
│  orchestrate.py │ ──► Agent Adapter Layer (NEW)
└────────┬────────┘
         ▼
┌─────────────────┐
│  Agent Registry │ ──► Supports multiple backends:
│  & Adapters     │     • Antigravity CLI (agy)
│                 │     • Claude Code
│                 │     • Codex CLI
│                 │     • Ollama (local)
│                 │     • OpenAI-compatible APIs
└────────┬────────┘
         ▼
┌─────────────────┐
│   Various APIs  │
└─────────────────┘
```

---

## Implementation Phases

### Phase 1: Emergency Migration (Week 1)
**Deadline: Before June 18, 2026**

- [ ] Update `START_HERE.bat` to install `antigravity-cli`
- [ ] Update `scripts/orchestrate.py` to support `agy` command
- [ ] Update `config.yaml` to default to `agent: "antigravity"`
- [ ] Update documentation

### Phase 2: Agent Abstraction Layer (Week 2-3)

- [ ] Create `agents/` directory with adapter implementations
- [ ] Implement base interface `AgentInterface`
- [ ] Create adapter for each supported backend
- [ ] Update `orchestrate.py` to use adapter layer

### Phase 3: UI Integration (Week 4)

- [ ] Add agent selection dropdown to UI
- [ ] Display agent-specific options (model selection, etc.)
- [ ] Show agent status indicators

---

## Technical Details

### Agent Interface Specification

```python
class AgentInterface:
    """Base interface for all AI agents."""
    
    def __init__(self, config: dict):
        self.config = config
        self.name: str  # Display name
        self.command: str  # CLI command or API endpoint
    
    def execute(self, prompt: str, mode: str, options: dict = None) -> str:
        """Execute agent with given prompt and mode."""
        raise NotImplementedError
    
    def get_models(self) -> list:
        """Return available models."""
        raise NotImplementedError
    
    def is_available(self) -> bool:
        """Check if agent is available and properly configured."""
        raise NotImplementedError
```

### Adapter Examples

```python
# agents/antigravity_adapter.py
class AntigravityAdapter(AgentInterface):
    def __init__(self, config):
        super().__init__(config)
        self.name = "Antigravity CLI"
        self.command = "agy"
    
    def execute(self, prompt, mode, options=None):
        cmd = [self.command]
        if options.get("model"):
            cmd.extend(["-m", options["model"]])
        # Add other antigravity-specific options
        return subprocess.run(cmd, input=prompt, capture_output=True, text=True)
```

---

## References

- [Google Developers Blog: Transitioning Gemini CLI to Antigravity CLI](https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/)
- [Antigravity CLI Documentation](https://antigravity.google/docs/gcli-migration)
- [Antigravity CLI GitHub Repository](https://github.com/google-antigravity/antigravity-cli)
