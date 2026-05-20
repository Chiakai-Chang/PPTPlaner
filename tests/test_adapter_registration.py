"""
Integration tests for adapter registration.
"""
import pytest
from agents import AgentFactory, AgentRegistry
from agents.antigravity import AntigravityAdapter
from agents.claude import ClaudeCodeAdapter
from agents.openai_compatible import OpenAICompatibleAdapter
from agents.openai_direct import OpenAIDirectAdapter


def _ensure_adapters_registered():
    """Helper to ensure adapters are registered after registry reset."""
    registry = AgentRegistry()
    
    # Register all adapters
    registry.register("antigravity", AntigravityAdapter)
    registry.register("claude", ClaudeCodeAdapter)
    registry.register("openai-compatible", OpenAICompatibleAdapter)
    registry.register("openai", OpenAIDirectAdapter)


class TestAdapterRegistration:
    """Test that all adapters are properly registered."""
    
    @pytest.fixture(autouse=True)
    def setup_registry(self):
        """Setup registry before each test."""
        AgentRegistry.reset()
        _ensure_adapters_registered()
        yield
        AgentRegistry.reset()
    
    def test_all_adapters_registered(self):
        """All adapters should be registered."""
        registry = AgentRegistry()
        agents = registry.list_agents()
        
        assert "antigravity" in agents
        assert "claude" in agents
        assert "openai-compatible" in agents
        assert "openai" in agents
    
    def test_create_antigravity_agent(self):
        """Should create Antigravity adapter."""
        config = {"agent": "antigravity"}
        agent = AgentFactory.create(config)
        assert isinstance(agent, AntigravityAdapter)
    
    def test_create_claude_agent(self):
        """Should create Claude adapter."""
        config = {"agent": "claude"}
        agent = AgentFactory.create(config)
        assert isinstance(agent, ClaudeCodeAdapter)
    
    def test_create_openai_compatible_agent(self):
        """Should create OpenAI-compatible adapter."""
        config = {"agent": "openai-compatible"}
        agent = AgentFactory.create(config)
        assert isinstance(agent, OpenAICompatibleAdapter)
    
    def test_create_openai_direct_agent(self):
        """Should create OpenAI direct adapter."""
        config = {"agent": "openai"}
        agent = AgentFactory.create(config)
        assert isinstance(agent, OpenAIDirectAdapter)
    
    def test_agent_has_required_methods(self):
        """All agents should have required methods."""
        for agent_name in ["antigravity", "claude", "openai-compatible", "openai"]:
            config = {"agent": agent_name}
            agent = AgentFactory.create(config)
            
            assert hasattr(agent, "execute")
            assert hasattr(agent, "get_models")
            assert hasattr(agent, "is_available")
            assert callable(getattr(agent, "execute"))
            assert callable(getattr(agent, "get_models"))
            assert callable(getattr(agent, "is_available"))
