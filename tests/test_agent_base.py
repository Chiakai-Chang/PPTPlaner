"""
Unit tests for AgentInterface ABC.
"""
import pytest
from agents.base import AgentInterface


class TestAgentInterface:
    """Test the base AgentInterface ABC."""
    
    def test_is_abstract(self):
        """AgentInterface should not be instantiable directly."""
        with pytest.raises(TypeError):
            AgentInterface()
    
    def test_concrete_implementation(self):
        """A concrete implementation should be instantiable."""
        class MockAgent(AgentInterface):
            NAME = "MockAgent"
            COMMAND = "mock"
            
            def __init__(self, config):
                self.config = config
            
            def execute(self, prompt, mode, **kwargs):
                return f"Mock response for {mode}"
            
            def get_models(self):
                return ["mock-model-1"]
            
            def is_available(self):
                return True
        
        agent = MockAgent({"test": True})
        assert agent.NAME == "MockAgent"
    
    def test_execute_returns_string(self):
        """execute() should return a string."""
        class MockAgent(AgentInterface):
            NAME = "Test"
            COMMAND = "test"
            
            def __init__(self, config):
                self.config = config
            
            def execute(self, prompt, mode, **kwargs):
                return "response"
            
            def get_models(self):
                return []
            
            def is_available(self):
                return True
        
        agent = MockAgent({})
        result = agent.execute("test prompt", "PLAN")
        assert isinstance(result, str)
    
    def test_get_models_returns_list(self):
        """get_models() should return a list."""
        class MockAgent(AgentInterface):
            NAME = "Test"
            COMMAND = "test"
            
            def __init__(self, config):
                self.config = config
            
            def execute(self, prompt, mode, **kwargs):
                return "response"
            
            def get_models(self):
                return ["model-1", "model-2"]
            
            def is_available(self):
                return True
        
        agent = MockAgent({})
        models = agent.get_models()
        assert isinstance(models, list)
        assert len(models) > 0
    
    def test_is_available_returns_bool(self):
        """is_available() should return a boolean."""
        class MockAgent(AgentInterface):
            NAME = "Test"
            COMMAND = "test"
            
            def __init__(self, config):
                self.config = config
            
            def execute(self, prompt, mode, **kwargs):
                return "response"
            
            def get_models(self):
                return []
            
            def is_available(self):
                return True
        
        agent = MockAgent({})
        assert isinstance(agent.is_available(), bool)
    
    def test_get_status_returns_dict(self):
        """get_status() should return a dictionary."""
        class MockAgent(AgentInterface):
            NAME = "Test"
            COMMAND = "test"
            
            def __init__(self, config):
                self.config = config
            
            def execute(self, prompt, mode, **kwargs):
                return "response"
            
            def get_models(self):
                return ["model-1"]
            
            def is_available(self):
                return True
        
        agent = MockAgent({})
        status = agent.get_status()
        assert isinstance(status, dict)
        assert "name" in status
        assert "available" in status
        assert "models" in status
