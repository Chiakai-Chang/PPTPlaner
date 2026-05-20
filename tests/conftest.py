"""
Shared test fixtures for PPTPlaner agent migration tests.
"""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path


@pytest.fixture
def tmp_config(tmp_path):
    """Create a temporary config file."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
agent: antigravity
agent_config:
  model: gemini-1.5-pro
  max_retries: 3
""")
    return config_file


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run for agent testing."""
    with patch('subprocess.run') as mock:
        mock.return_value = Mock(
            returncode=0,
            stdout='{"test": "output"}',
            stderr=''
        )
        yield mock


@pytest.fixture
def sample_agent_config():
    """Sample agent configuration."""
    return {
        "agent": "antigravity",
        "agent_config": {
            "model": "gemini-1.5-pro",
            "max_retries": 3,
            "retry_delay": 5
        }
    }


@pytest.fixture
def mock_agent_interface():
    """Mock AgentInterface implementation for testing."""
    class MockAgent:
        NAME = "MockAgent"
        COMMAND = "mock"
        
        def __init__(self, config):
            self.config = config
        
        def execute(self, prompt, mode, **kwargs):
            return f"Mock response for {mode}"
        
        def get_models(self):
            return ["mock-model-1", "mock-model-2"]
        
        def is_available(self):
            return True
    
    return MockAgent
