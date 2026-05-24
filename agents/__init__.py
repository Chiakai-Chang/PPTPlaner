"""
Multi-Agent Architecture for PPTPlaner.

Supports:
- Antigravity CLI (agy)
- Claude Code CLI (claude)
- OpenAI-compatible API (Ollama, llama.cpp, vLLM, etc.)
- OpenAI API (direct)

Usage:
    from agents import AgentFactory
    
    config = {"agent": "antigravity"}
    agent = AgentFactory.create(config)
    
    result = agent.execute("Hello", "PLAN")
"""

from .base import AgentInterface
from .registry import AgentRegistry
from .factory import AgentFactory
from .exceptions import (
    AgentError,
    AgentNotFoundError,
    AgentExecutionError,
    AgentAuthenticationError,
    AgentQuotaExceededError
)
from .logging_config import agent_logger

# Import adapters (auto-registers them)
try:
    from .antigravity import AntigravityAdapter  # noqa: F401
except ImportError:
    pass

try:
    from .claude import ClaudeCodeAdapter  # noqa: F401
except ImportError:
    pass

try:
    from .openai_compatible import OpenAICompatibleAdapter  # noqa: F401
except ImportError:
    pass

try:
    from .openai_direct import OpenAIDirectAdapter  # noqa: F401
except ImportError:
    pass

__all__ = [
    'AgentInterface',
    'AgentRegistry',
    'AgentFactory',
    'AgentError',
    'AgentNotFoundError',
    'AgentExecutionError',
    'AgentAuthenticationError',
    'AgentQuotaExceededError',
    'AntigravityAdapter',
    'ClaudeCodeAdapter',
    'OpenAICompatibleAdapter',
    'OpenAIDirectAdapter',
]
