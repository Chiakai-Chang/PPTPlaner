"""
Exception hierarchy for PPTPlaner agent system.
"""


class AgentError(Exception):
    """Base exception for all agent-related errors."""
    pass


class AgentNotFoundError(AgentError):
    """Agent not found in registry or not available."""
    
    def __init__(self, agent_name: str, available: list[str] | None = None):
        message = f"Agent '{agent_name}' not found."
        if available:
            message += f" Available: {', '.join(available)}"
        super().__init__(message)
        self.agent_name = agent_name
        self.available = available


class AgentExecutionError(AgentError):
    """Agent execution failed."""
    
    def __init__(self, message: str, agent_name: str, retry_count: int = 0):
        super().__init__(message)
        self.agent_name = agent_name
        self.retry_count = retry_count


class AgentAuthenticationError(AgentError):
    """Agent authentication failed."""
    
    def __init__(self, message: str, agent_name: str):
        super().__init__(message)
        self.agent_name = agent_name


class AgentQuotaExceededError(AgentError):
    """Agent quota exceeded."""
    
    def __init__(self, message: str, agent_name: str):
        super().__init__(message)
        self.agent_name = agent_name
