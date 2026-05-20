# System Design Document: Multi-Agent Architecture

## 1. Overview

### 1.1 Purpose
Design a flexible agent abstraction layer that allows PPTPlaner to support multiple AI backends:
- Antigravity CLI (successor to Gemini CLI)
- Claude Code
- Codex CLI
- Ollama (local models)
- OpenAI-compatible APIs

### 1.2 Design Goals
| Goal | Priority | Description |
|------|----------|-------------|
| **Extensibility** | High | Easy to add new agent backends |
| **Backward Compatibility** | High | Existing configs should continue working |
| **Testability** | High | Each component independently testable |
| **Performance** | Medium | Minimal overhead compared to direct CLI calls |
| **Observability** | Medium | Full logging and error reporting |

---

## 2. Architecture

### 2.1 High-Level Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        run_ui.py                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  AgentSelector                      │    │
│  │  • Agent Type Dropdown                             │    │
│  │  • Model Selector (dynamic)                        │    │
│  │  • Availability Indicator                          │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     orchestrate.py                          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  AgentFactory                       │    │
│  │  • create_agent(config)                            │    │
│  │  • discover_available_agents()                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  AgentRegistry                      │    │
│  │  • register(name, agent_class)                     │    │
│  │  • get_agent_class(name)                           │    │
│  │  • list_available()                                │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     agents/                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ AgentInterface│  │ Agent        │  │ Agent        │      │
│  │ (ABC)        │──│Factory       │  │Registry      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                    │              │               │
│         ▼                    ▼              ▼               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │Antigravity   │  │ClaudeCode    │  │Ollama        │      │
│  │Adapter       │  │Adapter       │  │Adapter       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                    │              │               │
│         ▼                    ▼              ▼               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   agy CLI    │  │  claude CLI  │  │  ollama API  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Component Specifications

### 3.1 AgentInterface (Abstract Base Class)

```python
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
```

### 3.2 AgentRegistry

```python
class AgentRegistry:
    """Registry for managing agent implementations."""
    
    _instance: Optional['AgentRegistry'] = None
    _agents: Dict[str, type]
    
    @classmethod
    def get_instance(cls) -> 'AgentRegistry':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def register(self, name: str, agent_class: type) -> None:
        """Register an agent class with its name."""
        self._agents[name.lower()] = agent_class
    
    def get_agent_class(self, name: str) -> type:
        """Get agent class by name."""
        if name.lower() not in self._agents:
            raise AgentNotFoundError(f"Agent '{name}' not registered")
        return self._agents[name.lower()]
    
    def list_agents(self) -> List[str]:
        """List all registered agent names."""
        return list(self._agents.keys())
    
    def discover_agents(self) -> None:
        """Auto-discover and register available agents."""
        # Import and register all adapters
        from agents.antigravity import AntigravityAdapter
        from agents.claude import ClaudeCodeAdapter
        # etc.
        
        self.register("antigravity", AntigravityAdapter)
        self.register("claude", ClaudeCodeAdapter)
        # etc.
```

### 3.3 AgentFactory

```python
class AgentFactory:
    """Factory for creating agent instances."""
    
    @staticmethod
    def create(config: Dict[str, Any]) -> AgentInterface:
        """Create agent instance from configuration."""
        agent_name = config.get("agent", "antigravity")
        registry = AgentRegistry.get_instance()
        
        agent_class = registry.get_agent_class(agent_name)
        return agent_class(config)
    
    @staticmethod
    def create_from_string(config_str: str) -> AgentInterface:
        """Create agent from YAML/JSON string."""
        import yaml
        config = yaml.safe_load(config_str)
        return AgentFactory.create(config)
```

---

## 4. Error Handling Strategy

### 4.1 Exception Hierarchy

```python
class AgentError(Exception):
    """Base exception for all agent-related errors."""
    pass

class AgentNotFoundError(AgentError):
    """Agent not found in registry."""
    pass

class AgentExecutionError(AgentError):
    """Agent execution failed."""
    def __init__(self, message: str, agent_name: str, retry_count: int = 0):
        self.agent_name = agent_name
        self.retry_count = retry_count
        super().__init__(message)

class AgentAuthenticationError(AgentError):
    """Agent authentication failed."""
    pass

class AgentQuotaExceededError(AgentError):
    """Agent quota exceeded."""
    pass
```

### 4.2 Retry Strategy

```python
class RetryStrategy:
    """Configurable retry strategy."""
    
    def __init__(
        self,
        max_retries: int = 3,
        delay: int = 5,
        backoff_factor: float = 2.0,
        retryable_exceptions: tuple = (AgentExecutionError,)
    ):
        self.max_retries = max_retries
        self.delay = delay
        self.backoff_factor = backoff_factor
        self.retryable_exceptions = retryable_exceptions
    
    def execute_with_retry(self, func, *args, **kwargs):
        """Execute function with retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except self.retryable_exceptions as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay * (self.backoff_factor ** attempt))
        
        raise last_exception
```

---

## 5. Configuration Schema

```yaml
# config.yaml - Agent Configuration
agent: "antigravity"  # Agent name
agent_config:
  model: "gemini-1.5-pro"  # Model selection
  api_base: null  # For local models
  api_key: null  # For API-based agents
  command_override: null  # Custom command path
  
  # Retry settings
  max_retries: 3
  retry_delay: 5
  
  # Agent-specific options
  options:
    temperature: 0.7
    max_tokens: 4096
```

---

## 6. Migration Path

### 6.1 Phase 1: Emergency Migration

```python
# Minimal change to support antigravity
# In run_agent():

def run_agent(agent: str, mode: str, vars_map: dict, **kwargs):
    # Legacy support: map "gemini" to "antigravity"
    if agent == "gemini":
        print_warning("Gemini CLI is deprecated. Using Antigravity CLI.")
        agent = "antigravity"
    
    # Use new agent abstraction
    agent_adapter = AgentFactory.create({"agent": agent})
    return agent_adapter.execute(build_prompt(vars_map), mode, **kwargs)
```

### 6.2 Phase 2: Full Abstraction

```python
# Complete migration to agent abstraction
# All agent calls go through AgentInterface

def orchestrate_task(task_config):
    agent = AgentFactory.create(task_config)
    
    # Execute with retry
    result = agent.execute(
        prompt=task_config["prompt"],
        mode=task_config["mode"],
        max_retries=task_config["retries"]
    )
    
    return parse_ai_json_output(result, task_config["mode"])
```

---

## 7. Security Considerations

| Concern | Mitigation |
|---------|------------|
| API Key Exposure | Environment variables only, never in config |
| Command Injection | Input sanitization, no shell=True |
| Prompt Injection | Existing `_SAFETY_PREAMBLE.md` mechanism |
| Credential Rotation | Clear error messages, retry with new creds |
