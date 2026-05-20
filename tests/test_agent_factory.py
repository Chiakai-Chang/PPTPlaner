"""
Unit tests for AgentFactory.
"""
import pytest
from agents.factory import AgentFactory
from agents.registry import AgentRegistry
from agents.base import AgentInterface


class TestAgentFactory:
    """Test the AgentFactory."""
    
    @pytest.fixture(autouse=True)
    def setup_registry(self):
        """Setup registry with test agent."""
        AgentRegistry.reset()
        registry = AgentRegistry()
        
        class TestAgent(AgentInterface):
            NAME = "TestAgent"
            COMMAND = "test"
            
            def __init__(self, config):
                self.config = config
            
            def execute(self, prompt, mode, **kwargs):
                return "test output"
            
            def get_models(self):
                return ["test-model"]
            
            def is_available(self):
                return True
        
        registry.register("test", TestAgent)
        yield
        AgentRegistry.reset()
    
    def test_create_agent(self):
        """Should create agent instance from config."""
        config = {"agent": "test", "key": "value"}
        agent = AgentFactory.create(config)
        
        assert agent.NAME == "TestAgent"
        assert agent.config == config
    
    def test_create_from_string(self):
        """Should parse YAML string and create agent."""
        yaml_str = """
agent: test
model: test-model
"""
        agent = AgentFactory.create_from_string(yaml_str)
        assert agent.NAME == "TestAgent"
    
    def test_list_available_agents(self):
        """Should list all available agents."""
        agents = AgentFactory.list_available_agents()
        assert "test" in agents
    
    def test_get_agent_status(self):
        """Should get agent status."""
        status = AgentFactory.get_agent_status("test")
        assert status["name"] == "TestAgent"
        assert status["available"] == True
