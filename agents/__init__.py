"""
Multi-Agent Architecture for PPTPlaner.

Supports:
- Antigravity CLI (agy)
- Claude Code CLI (claude)
- OpenAI-compatible API (Ollama, llama.cpp, etc.)
- OpenAI API (direct)
"""

from .base import AgentInterface
from .registry import AgentRegistry
from .factory import AgentFactory

__all__ = ['AgentInterface', 'AgentRegistry', 'AgentFactory']
