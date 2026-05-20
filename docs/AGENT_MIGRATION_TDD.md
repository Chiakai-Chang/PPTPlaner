# Test-Driven Development (TDD) Specifications

## Agent Migration Project

---

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures
├── test_agent_base.py            # AgentInterface tests
├── test_agent_registry.py        # AgentRegistry tests
├── test_agent_factory.py         # AgentFactory tests
├── test_retry_strategy.py        # RetryStrategy tests
├── agents/
│   ├── __init__.py
│   ├── test_antigravity.py       # Antigravity adapter tests
│   ├── test_claude.py           # Claude adapter tests
│   ├── test_ollama.py           # Ollama adapter tests
│   └── test_openai.py           # OpenAI adapter tests
├── integration/
│   ├── __init__.py
│   └── test_agent_execution.py  # End-to-end tests
└── ui/
    ├── __init__.py
    └── test_agent_selector.py   # UI component tests
```

---

## Test Fixtures (conftest.py)

```python
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
```

---

## Unit Tests: AgentInterface

```python
# tests/test_agent_base.py

import pytest
from agents.base import AgentInterface
from agents.exceptions import AgentError


class TestAgentInterface:
    """Test the base AgentInterface ABC."""
    
    def test_is_abstract(self):
        """AgentInterface should not be instantiable directly."""
        with pytest.raises(TypeError):
            AgentInterface()
    
    def test_concrete_implementation(self, mock_agent_interface):
        """A concrete implementation should be instantiable."""
        agent = mock_agent_interface({"test": True})
        assert agent.NAME == "MockAgent"
    
    def test_execute_returns_string(self, mock_agent_interface):
        """execute() should return a string."""
        agent = mock_agent_interface({})
        result = agent.execute("test prompt", "PLAN")
        assert isinstance(result, str)
    
    def test_get_models_returns_list(self, mock_agent_interface):
        """get_models() should return a list."""
        agent = mock_agent_interface({})
        models = agent.get_models()
        assert isinstance(models, list)
        assert len(models) > 0
    
    def test_is_available_returns_bool(self, mock_agent_interface):
        """is_available() should return a boolean."""
        agent = mock_agent_interface({})
        assert isinstance(agent.is_available(), bool)
    
    def test_get_status_returns_dict(self, mock_agent_interface):
        """get_status() should return a dictionary."""
        agent = mock_agent_interface({})
        status = agent.get_status()
        assert isinstance(status, dict)
        assert "name" in status
        assert "available" in status
        assert "models" in status
```

---

## Unit Tests: AgentRegistry

```python
# tests/test_agent_registry.py

import pytest
from agents.registry import AgentRegistry
from agents.exceptions import AgentNotFoundError


class TestAgentRegistry:
    """Test the AgentRegistry singleton."""
    
    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        AgentRegistry._instance = None
        yield
        AgentRegistry._instance = None
    
    def test_singleton_pattern(self):
        """Registry should be a singleton."""
        reg1 = AgentRegistry.get_instance()
        reg2 = AgentRegistry.get_instance()
        assert reg1 is reg2
    
    def test_register_agent(self):
        """Should register an agent class."""
        registry = AgentRegistry.get_instance()
        
        class TestAgent:
            pass
        
        registry.register("test", TestAgent)
        assert "test" in registry.list_agents()
    
    def test_get_agent_class(self):
        """Should retrieve registered agent class."""
        registry = AgentRegistry.get_instance()
        
        class TestAgent:
            pass
        
        registry.register("test", TestAgent)
        retrieved = registry.get_agent_class("test")
        assert retrieved is TestAgent
    
    def test_get_nonexistent_agent_raises(self):
        """Should raise error for unregistered agent."""
        registry = AgentRegistry.get_instance()
        
        with pytest.raises(AgentNotFoundError) as exc_info:
            registry.get_agent_class("nonexistent")
        
        assert "nonexistent" in str(exc_info.value)
    
    def test_list_agents(self):
        """Should list all registered agents."""
        registry = AgentRegistry.get_instance()
        
        registry.register("agent1", object)
        registry.register("agent2", object)
        
        agents = registry.list_agents()
        assert len(agents) == 2
        assert "agent1" in agents
        assert "agent2" in agents
    
    def test_case_insensitive_registration(self):
        """Agent names should be case-insensitive."""
        registry = AgentRegistry.get_instance()
        
        class TestAgent:
            pass
        
        registry.register("TEST", TestAgent)
        retrieved = registry.get_agent_class("test")
        assert retrieved is TestAgent
```

---

## Unit Tests: AgentFactory

```python
# tests/test_agent_factory.py

import pytest
from agents.factory import AgentFactory
from agents.registry import AgentRegistry


class TestAgentFactory:
    """Test the AgentFactory."""
    
    @pytest.fixture(autouse=True)
    def setup_registry(self):
        """Setup registry with test agent."""
        AgentRegistry._instance = None
        registry = AgentRegistry.get_instance()
        
        class TestAgent:
            NAME = "TestAgent"
            
            def __init__(self, config):
                self.config = config
            
            def execute(self, *args, **kwargs):
                return "test output"
            
            def get_models(self):
                return ["test-model"]
            
            def is_available(self):
                return True
        
        registry.register("test", TestAgent)
        yield
        AgentRegistry._instance = None
    
    def test_create_agent(self):
        """Should create agent instance from config."""
        config = {"agent": "test", "key": "value"}
        agent = AgentFactory.create(config)
        
        assert agent.NAME == "TestAgent"
        assert agent.config == config
    
    def test_create_agent_default(self):
        """Should use default agent if not specified."""
        config = {}  # No agent specified
        
        # This should fail since "antigravity" isn't registered in tests
        with pytest.raises(Exception):
            AgentFactory.create(config)
    
    def test_create_from_string(self, tmp_config):
        """Should parse YAML string and create agent."""
        yaml_str = """
agent: test
model: test-model
"""
        agent = AgentFactory.create_from_string(yaml_str)
        assert agent.NAME == "TestAgent"
```

---

## Unit Tests: RetryStrategy

```python
# tests/test_retry_strategy.py

import pytest
import time
from agents.retry import RetryStrategy
from agents.exceptions import AgentExecutionError


class TestRetryStrategy:
    """Test the RetryStrategy."""
    
    def test_success_on_first_try(self):
        """Should not retry on success."""
        strategy = RetryStrategy(max_retries=3)
        call_count = 0
        
        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = strategy.execute_with_retry(success_func)
        assert result == "success"
        assert call_count == 1  # No retries
    
    def test_retry_on_failure(self):
        """Should retry on transient failure."""
        strategy = RetryStrategy(max_retries=3, delay=0.1)
        call_count = 0
        
        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise AgentExecutionError("Transient error", "test")
            return "success"
        
        result = strategy.execute_with_retry(fail_then_succeed)
        assert result == "success"
        assert call_count == 3  # 2 retries + 1 success
    
    def test_exhaust_retries(self):
        """Should raise after all retries exhausted."""
        strategy = RetryStrategy(max_retries=2, delay=0.1)
        
        def always_fail():
            raise AgentExecutionError("Persistent error", "test")
        
        with pytest.raises(AgentExecutionError):
            strategy.execute_with_retry(always_fail)
    
    def test_exponential_backoff(self):
        """Should use exponential backoff between retries."""
        strategy = RetryStrategy(max_retries=3, delay=0.1, backoff_factor=2.0)
        timestamps = []
        
        def track_time():
            timestamps.append(time.time())
            raise AgentExecutionError("Error", "test")
        
        with pytest.raises(AgentExecutionError):
            strategy.execute_with_retry(track_time)
        
        # Check backoff delays
        if len(timestamps) >= 3:
            delay1 = timestamps[1] - timestamps[0]
            delay2 = timestamps[2] - timestamps[1]
            assert delay2 > delay1  # Backoff should increase
```

---

## Integration Tests: Agent Execution

```python
# tests/integration/test_agent_execution.py

import pytest
from agents.factory import AgentFactory
from agents.registry import AgentRegistry


@pytest.mark.integration
@pytest.mark.skipif(not pytest.config.getoption("--integration"), 
                    reason="Integration tests not enabled")
class TestAgentExecution:
    """Integration tests for agent execution."""
    
    def test_antigravity_execution(self):
        """Test actual Antigravity CLI execution."""
        config = {"agent": "antigravity"}
        agent = AgentFactory.create(config)
        
        if not agent.is_available():
            pytest.skip("Antigravity CLI not installed")
        
        result = agent.execute("Say 'hello' in one word", "test")
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_json_mode(self):
        """Test JSON output mode."""
        config = {"agent": "antigravity"}
        agent = AgentFactory.create(config)
        
        if not agent.is_available():
            pytest.skip("Antigravity CLI not installed")
        
        prompt = "Output JSON: {\"status\": \"ok\"}"
        result = agent.execute(prompt, "test", options={"output_format": "json"})
        assert isinstance(result, str)
```

---

## Running Tests

```bash
# Unit tests only
pytest tests/ -m "not integration"

# With coverage
pytest tests/ --cov=agents --cov-report=html

# Integration tests
pytest tests/ --integration

# Type checking
mypy agents/
```
