# Behavior-Driven Development (BDD) Specifications

## Agent Migration Project

---

## Feature: Multi-Agent Support

### Background
As a PPTPlaner user, I want to choose different AI backends so that I'm not locked into a single provider and can adapt to service changes.

---

### Scenario: User selects Antigravity CLI as default agent

```gherkin
Given the user has Antigravity CLI installed (agy command available)
And the config.yaml specifies agent: "antigravity"
When PPTPlaner starts
Then the UI should show "Antigravity CLI" as the selected agent
And the agent availability indicator should show "Available" ✓
```

---

### Scenario: User switches from Gemini to Antigravity

```gherkin
Given the user currently has agent: "gemini" in config
And Gemini CLI is no longer available
When the user tries to run a generation task
Then PPTPlaner should display a migration warning
And suggest switching to Antigravity CLI
And provide a one-click migration option
```

---

### Scenario: User selects local model via Ollama

```gherkin
Given the user has Ollama running on localhost:11434
And the config.yaml specifies agent: "ollama" with model: "llama3.1"
When the user runs a generation task
Then PPTPlaner should connect to Ollama API
And use the specified model
And not require any external API keys
```

---

### Scenario: Agent is unavailable

```gherkin
Given the user has selected agent: "claude"
And Claude Code is not installed
When the user tries to run a generation task
Then PPTPlaner should display an error: "Claude Code not found in PATH"
And suggest installation steps
And offer to switch to an available agent
```

---

### Scenario: API key authentication failure

```gherkin
Given the user has configured agent: "openai"
And the API key is invalid
When the user runs a generation task
Then PPTPlaner should display: "Authentication failed for OpenAI"
And prompt the user to update their API key
And not crash the application
```

---

### Scenario: Quota exceeded with retry

```gherkin
Given the user has reached their API quota
When the user runs a generation task
Then PPTPlaner should detect the quota error
And pause execution with clear message
And allow the user to:
  - Wait and retry
  - Switch to a different agent
  - Switch to a different model
```

---

### Scenario: Model selection per agent

```gherkin
Given the user has selected agent: "antigravity"
When the user opens the agent settings
Then the UI should show available models for Antigravity
And allow the user to select a specific model
And save this selection to config
```

---

## Feature: Agent Abstraction Layer

### Scenario: Register a new agent adapter

```gherkin
Given a new agent adapter implementing AgentInterface
When the adapter is imported
Then it should be automatically registered in AgentRegistry
And appear in the list of available agents
```

---

### Scenario: Execute task with different agents

```gherkin
Given a task with mode "PLAN"
And two different agents configured (antigravity, ollama)
When the task is executed with antigravity
Then it should produce valid JSON output
When the same task is executed with ollama
Then it should also produce valid JSON output
And both outputs should have the same structure
```

---

### Scenario: Retry on transient failure

```gherkin
Given an agent execution fails with network error
And max_retries is set to 3
When the agent is executed
Then it should retry up to 3 times
With exponential backoff (5s, 10s, 20s)
And only fail after all retries exhausted
```

---

## Feature: Configuration Management

### Scenario: Load agent configuration

```gherkin
Given config.yaml contains agent configuration
When PPTPlaner loads the configuration
Then it should parse agent settings
And validate the agent name exists
And apply default values for missing options
```

---

### Scenario: Update agent via UI

```gherkin
Given the user is on the main UI
When the user selects a different agent from dropdown
And clicks "Save"
Then the config.yaml should be updated
And the new agent should be used for subsequent tasks
```

---

## Feature: Backward Compatibility

### Scenario: Legacy gemini configuration

```gherkin
Given config.yaml has agent: "gemini"
And Gemini CLI is deprecated
When PPTPlaner loads the configuration
Then it should show a deprecation warning
And automatically map to "antigravity"
And update the config file
```

---

### Scenario: Legacy CLI arguments

```gherkin
Given a user runs: python orchestrate.py --gemini-model gemini-1.5-pro
When the command is executed
Then it should still work (backward compatible)
But show a deprecation notice
And suggest using --model instead
```

---

## Feature: Error Reporting

### Scenario: Agent not found

```gherkin
Given agent: "nonexistent" in config
When PPTPlaner tries to create the agent
Then it should raise AgentNotFoundError
With message: "Agent 'nonexistent' not found. Available: [antigravity, claude, ...]"
```

---

### Scenario: Command not in PATH

```gherkin
Given agent: "claude" configured
And claude command not in PATH
When agent.is_available() is called
Then it should return False
And agent.get_status() should include:
  - error: "Command 'claude' not found in PATH"
  - suggestion: "Install Claude Code: npm install -g @anthropic-ai/claude-code"
```
