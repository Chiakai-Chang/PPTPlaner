"""
AgentInterface - Abstract base class for all AI agents.

All agent adapters must implement this interface.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class AgentInterface(ABC):
    """Abstract interface for all AI agents."""
    
    # Agent metadata
    NAME: str = ""  # Display name
    COMMAND: str = ""  # CLI command or API identifier
    
    @abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """Initialize agent with configuration."""
        self.config = config
    
    @abstractmethod
    def execute(
        self,
        prompt: str,
        mode: str,
        model: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: int = 5,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Execute agent with given prompt and mode.
        
        Args:
            prompt: The prompt text to send to the agent
            mode: Task mode (e.g., "PLAN", "DECK", "MEMO")
            model: Specific model to use (optional)
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries in seconds
            options: Additional agent-specific options
            
        Returns:
            Agent response text
            
        Raises:
            AgentExecutionError: When execution fails after retries
            AgentNotFoundError: When agent is not available
        """
        pass
    
    @abstractmethod
    def get_models(self) -> List[str]:
        """Return list of available models for this agent."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if agent is available and properly configured."""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Return agent status information."""
        return {
            "name": self.NAME,
            "available": self.is_available(),
            "models": self.get_models(),
            "config": self.config
        }
