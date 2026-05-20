"""
Unit tests for AgentRegistry.
"""
import pytest
from agents.registry import AgentRegistry
from agents.exceptions import AgentNotFoundError


class TestAgentRegistry:
    """Test the AgentRegistry singleton."""
    
    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        AgentRegistry.reset()
        yield
        AgentRegistry.reset()
    
    def test_singleton_pattern(self):
        """Registry should be a singleton."""
        reg1 = AgentRegistry()
        reg2 = AgentRegistry()
        assert reg1 is reg2
    
    def test_register_agent(self):
        """Should register an agent class."""
        from agents.base import AgentInterface
        
        class TestAgent(AgentInterface):
            NAME = "TestAgent"
            COMMAND = "test"
            
            def __init__(self, config):
                self.config = config
            
            def execute(self, prompt, mode, **kwargs):
                return "test"
            
            def get_models(self):
                return []
            
            def is_available(self):
                return True
        
        registry = AgentRegistry()
        registry.register("test", TestAgent)
        assert "test" in registry.list_agents()
    
    def test_get_agent_class(self):
        """Should retrieve registered agent class."""
        from agents.base import AgentInterface
        
        class TestAgent(AgentInterface):
            NAME = "TestAgent"
            COMMAND = "test"
            
            def __init__(self, config):
                self.config = config
            
            def execute(self, prompt, mode, **kwargs):
                return "test"
            
            def get_models(self):
                return []
            
            def is_available(self):
                return True
        
        registry = AgentRegistry()
        registry.register("test", TestAgent)
        retrieved = registry.get_agent_class("test")
        assert retrieved is TestAgent
    
    def test_get_nonexistent_agent_raises(self):
        """Should raise error for unregistered agent."""
        registry = AgentRegistry()
        
        with pytest.raises(AgentNotFoundError) as exc_info:
            registry.get_agent_class("nonexistent")
        
        assert "nonexistent" in str(exc_info.value)
    
    def test_list_agents(self):
        """Should list all registered agents."""
        from agents.base import AgentInterface
        
        class TestAgent(AgentInterface):
            NAME = "TestAgent"
            COMMAND = "test"
            
            def __init__(self, config):
                self.config = config
            
            def execute(self, prompt, mode, **kwargs):
                return "test"
            
            def get_models(self):
                return []
            
            def is_available(self):
                return True
        
        registry = AgentRegistry()
        registry.register("agent1", TestAgent)
        registry.register("agent2", TestAgent)
        
        agents = registry.list_agents()
        assert len(agents) == 2
        assert "agent1" in agents
        assert "agent2" in agents
    
    def test_case_insensitive_registration(self):
        """Agent names should be case-insensitive."""
        from agents.base import AgentInterface
        
        class TestAgent(AgentInterface):
            NAME = "TestAgent"
            COMMAND = "test"
            
            def __init__(self, config):
                self.config = config
            
            def execute(self, prompt, mode, **kwargs):
                return "test"
            
            def get_models(self):
                return []
            
            def is_available(self):
                return True
        
        registry = AgentRegistry()
        registry.register("TEST", TestAgent)
        retrieved = registry.get_agent_class("test")
        assert retrieved is TestAgent
    
    def test_has_agent(self):
        """Should check if agent exists."""
        from agents.base import AgentInterface
        
        class TestAgent(AgentInterface):
            NAME = "TestAgent"
            COMMAND = "test"
            
            def __init__(self, config):
                self.config = config
            
            def execute(self, prompt, mode, **kwargs):
                return "test"
            
            def get_models(self):
                return []
            
            def is_available(self):
                return True
        
        registry = AgentRegistry()
        registry.register("test", TestAgent)
        
        assert registry.has_agent("test") == True
        assert registry.has_agent("nonexistent") == False
