"""
AgentRegistry - Singleton registry for managing agent implementations.
"""
from typing import Dict, List, Type
from .base import AgentInterface
from .exceptions import AgentNotFoundError


class AgentRegistry:
    """Registry for managing agent implementations.
    
    Singleton pattern ensures single global registry.
    """
    
    _instance: 'AgentRegistry | None' = None
    _agents: Dict[str, Type[AgentInterface]]
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._agents = {}
        return cls._instance
    
    @classmethod
    def reset(cls):
        """Reset registry (for testing)."""
        cls._instance = None
    
    def register(self, name: str, agent_class: Type[AgentInterface]) -> None:
        """Register an agent class with its name."""
        self._agents[name.lower()] = agent_class
    
    def get_agent_class(self, name: str) -> Type[AgentInterface]:
        """Get agent class by name."""
        if name.lower() not in self._agents:
            raise AgentNotFoundError(name, list(self._agents.keys()))
        return self._agents[name.lower()]
    
    def list_agents(self) -> List[str]:
        """List all registered agent names."""
        return list(self._agents.keys())
    
    def has_agent(self, name: str) -> bool:
        """Check if an agent is registered."""
        return name.lower() in self._agents
    
    def discover_agents(self) -> None:
        """Auto-discover and register available agents.
        
        Import and register all adapters that are installed.
        """
        # Import all adapters (they auto-register)
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
