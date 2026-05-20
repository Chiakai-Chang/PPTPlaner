"""
Claude Code CLI Adapter

Supports the Claude Code CLI (claude) command-line tool.
"""
import subprocess
import os
import time
import logging
from typing import Optional, List, Dict, Any
from .base import AgentInterface
from .exceptions import AgentExecutionError, AgentAuthenticationError
from .retry import RetryStrategy

logger = logging.getLogger(__name__)


class ClaudeCodeAdapter(AgentInterface):
    """Claude Code CLI adapter."""
    
    NAME = "Claude Code"
    COMMAND = "claude"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model = config.get("agent_config", {}).get("model") or config.get("model")
        self.max_retries = config.get("agent_config", {}).get("max_retries", 3)
        self.retry_delay = config.get("agent_config", {}).get("retry_delay", 5)
        self.command_override = config.get("agent_config", {}).get("command_override")
    
    def _build_command(self, prompt: str, mode: str, options: Optional[Dict[str, Any]] = None) -> list[str]:
        """Build command line for Claude Code CLI."""
        cmd = [self.command_override or self.COMMAND]
        
        # Add model flag if specified
        model = options.get("model", self.model) if options else self.model
        if model:
            cmd.extend(["--model", model])
        
        # Add JSON output for structured modes
        if options and options.get("output_format") == "json":
            cmd.extend(["--output-format", "json"])
        
        return cmd
    
    def _detect_error_type(self, stderr: str) -> str:
        """Detect error type from stderr."""
        stderr_lower = stderr.lower()
        if "authentication" in stderr_lower or "unauthorized" in stderr_lower:
            return "auth"
        if "rate limit" in stderr_lower or "quota" in stderr_lower:
            return "quota"
        return "other"
    
    def execute(
        self,
        prompt: str,
        mode: str,
        model: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: int = 5,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Execute agent with given prompt and mode."""
        cmd = self._build_command(prompt, mode, options)
        
        attempt = 0
        while attempt < max_retries:
            try:
                logger.info(f"Calling {self.NAME} for {mode}... (Attempt {attempt + 1}/{max_retries})")
                result = subprocess.run(
                    cmd,
                    input=prompt,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=True
                )
                
                output = result.stdout.strip()
                if output:
                    return output
                
                attempt += 1
                
            except subprocess.CalledProcessError as e:
                error_type = self._detect_error_type(e.stderr)
                
                if error_type == "auth":
                    raise AgentAuthenticationError("Authentication failed", self.NAME)
                elif error_type == "quota":
                    raise AgentAuthenticationError("Quota exceeded", self.NAME)
                else:
                    logger.warning(f"Agent execution failed: {e.stderr.strip()}")
                    attempt += 1
            
            if attempt < max_retries:
                time.sleep(retry_delay)
        
        raise AgentExecutionError(
            f"Agent failed after {max_retries} attempts",
            self.NAME,
            max_retries
        )
    
    def get_models(self) -> List[str]:
        """Return list of available models."""
        return ["claude-sonnet-4-20250514", "claude-opus-4-20250514"]
    
    def is_available(self) -> bool:
        """Check if Claude Code CLI is available."""
        cmd = self.command_override or self.COMMAND
        return os.path.exists(cmd) or subprocess.run(
            ["where", cmd] if os.name == "nt" else ["which", cmd],
            capture_output=True
        ).returncode == 0
    
    def get_installation_hint(self) -> str:
        """Return installation instructions."""
        return "Install Claude Code: npm install -g @anthropic-ai/claude-code"


# Auto-register
from .registry import AgentRegistry
AgentRegistry().register("claude", ClaudeCodeAdapter)
AgentRegistry().register("claude-code", ClaudeCodeAdapter)  # Alias
