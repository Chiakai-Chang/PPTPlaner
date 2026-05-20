"""
AgentFactory - Factory for creating agent instances.
"""
from typing import Dict, Any, Optional
from .registry import AgentRegistry
from .base import AgentInterface


class AgentFactory:
    """Factory for creating agent instances."""
    
    DEFAULT_AGENT = "antigravity"
    
    @staticmethod
    def create(config: Dict[str, Any]) -> AgentInterface:
        """Create agent instance from configuration."""
        agent_name = config.get("agent", AgentFactory.DEFAULT_AGENT)
        registry = AgentRegistry()
        
        agent_class = registry.get_agent_class(agent_name)
        return agent_class(config)
    
    @staticmethod
    def create_from_string(config_str: str) -> AgentInterface:
        """Create agent from YAML string."""
        import yaml
        config = yaml.safe_load(config_str)
        return AgentFactory.create(config)
    
    @staticmethod
    def list_available_agents() -> list[str]:
        """List all available agent names."""
        registry = AgentRegistry()
        return registry.list_agents()
    
    @staticmethod
    def get_agent_status(agent_name: str) -> Dict[str, Any]:
        """Get status of a specific agent."""
        config = {"agent": agent_name}
        try:
            agent = AgentFactory.create(config)
            return agent.get_status()
        except Exception as e:
            return {
                "name": agent_name,
                "available": False,
                "error": str(e)
            }
