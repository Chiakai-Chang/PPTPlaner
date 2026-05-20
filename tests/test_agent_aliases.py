"""
Unit tests for agent aliases.
"""
import pytest
from agents import AgentFactory, AgentRegistry
from agents.antigravity import AntigravityAdapter
from agents.claude import ClaudeCodeAdapter
from agents.openai_compatible import OpenAICompatibleAdapter


def _ensure_adapters_registered():
    """Helper to ensure adapters are registered after registry reset."""
    registry = AgentRegistry()
    registry.register("antigravity", AntigravityAdapter)
    registry.register("agy", AntigravityAdapter)
    registry.register("claude", ClaudeCodeAdapter)
    registry.register("claude-code", ClaudeCodeAdapter)
    registry.register("openai-compatible", OpenAICompatibleAdapter)
    registry.register("ollama", OpenAICompatibleAdapter)
    registry.register("llamacpp", OpenAICompatibleAdapter)
    registry.register("openai", AgentFactory.__dict__.get('OpenAIDirectAdapter', object))  # Placeholder


class TestAgentAliases:
    """Test that agent aliases work correctly."""
    
    @pytest.fixture(autouse=True)
    def setup_registry(self):
        """Setup registry before each test."""
        AgentRegistry.reset()
        _ensure_adapters_registered()
        yield
        AgentRegistry.reset()
    
    def test_antigravity_alias_agy(self):
        """Test 'agy' alias for antigravity."""
        config = {"agent": "agy"}
        agent = AgentFactory.create(config)
        assert isinstance(agent, AntigravityAdapter)
    
    def test_claude_alias_claude_code(self):
        """Test 'claude-code' alias for claude."""
        config = {"agent": "claude-code"}
        agent = AgentFactory.create(config)
        assert isinstance(agent, ClaudeCodeAdapter)
    
    def test_openai_compatible_alias_ollama(self):
        """Test 'ollama' alias for openai-compatible."""
        config = {"agent": "ollama"}
        agent = AgentFactory.create(config)
        assert isinstance(agent, OpenAICompatibleAdapter)
    
    def test_openai_compatible_alias_llamacpp(self):
        """Test 'llamacpp' alias for openai-compatible."""
        config = {"agent": "llamacpp"}
        agent = AgentFactory.create(config)
        assert isinstance(agent, OpenAICompatibleAdapter)
    
    def test_all_aliases_listed(self):
        """Test that all aliases are in the agent list."""
        registry = AgentRegistry()
        agents = registry.list_agents()
        
        assert "antigravity" in agents
        assert "agy" in agents
        assert "claude" in agents
        assert "claude-code" in agents
        assert "openai-compatible" in agents
        assert "ollama" in agents
        assert "llamacpp" in agents
