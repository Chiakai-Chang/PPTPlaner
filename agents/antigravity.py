"""
Antigravity CLI Adapter

Supports the Antigravity CLI (agy) command-line tool.
This is the successor to Gemini CLI.
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


class AntigravityAdapter(AgentInterface):
    """Antigravity CLI (agy) adapter."""
    
    NAME = "Antigravity CLI"
    COMMAND = "agy"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model = config.get("agent_config", {}).get("model") or config.get("model")
        self.max_retries = config.get("agent_config", {}).get("max_retries", 3)
        self.retry_delay = config.get("agent_config", {}).get("retry_delay", 5)
        self.command_override = config.get("agent_config", {}).get("command_override")
    
    def _build_command(self, prompt: str, mode: str, options: Optional[Dict[str, Any]] = None) -> list[str]:
        """Build command line for Antigravity CLI.
        
        IMPORTANT: agy -p requires the prompt as an argument, NOT via stdin.
        Example: agy -p "your prompt here" --dangerously-skip-permissions
        """
        cmd = [self.command_override or self.COMMAND]
        
        # Use -p flag with prompt as argument
        cmd.append("-p")
        cmd.append(prompt)  # Prompt MUST be passed as argument, not stdin!
        
        # Auto-approve tool permissions for automation
        # This allows the agent to use tools without user intervention
        cmd.append("--dangerously-skip-permissions")
        
        # Add workspace directory for file access
        workspace = options.get("workspace") if options else None
        if workspace:
            cmd.extend(["--add-dir", workspace])
        
        # Add timeout (default 5 minutes)
        cmd.extend(["--print-timeout", "600s"])
        
        return cmd
    
    def _detect_error_type(self, stderr: str, stdout: str = "") -> str:
        """Detect error type from stderr using enhanced parsing."""
        from .error_parser import parse_cli_error, ErrorCategory
        
        parsed = parse_cli_error(stderr, stdout)
        
        # Map to legacy error types for backward compatibility
        if parsed.category == ErrorCategory.AUTH:
            return "auth"
        elif parsed.category == ErrorCategory.QUOTA:
            return "quota"
        else:
            return "other"
    
    def _get_parsed_error(self, stderr: str, stdout: str = "") -> "ParsedError":
        """Get detailed parsed error."""
        from .error_parser import parse_cli_error
        return parse_cli_error(stderr, stdout)
    
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
        from .logging_config import agent_logger
        
        cmd = self._build_command(prompt, mode, options)
        
        attempt = 0
        while attempt < max_retries:
            timing = agent_logger.log_agent_call(
                self.NAME, mode, model, attempt + 1, max_retries
            )
            
            try:
                logger.info(f"Calling {self.NAME} for {mode}... (Attempt {attempt + 1}/{max_retries})")
                logger.debug(f"Command: {' '.join(cmd)}")
                
                # CRITICAL: Use Popen with line-by-line reading
                # agy -p requires prompt as argument, NOT stdin!
                # subprocess.run does not work - must use Popen!
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,  # Merge stderr into stdout
                    text=True,
                    encoding="utf-8",
                    bufsize=1  # Line buffered
                )
                
                # Read line by line
                full_output = ""
                for line in process.stdout:
                    full_output += line
                
                process.wait()
                
                # Log detailed output for debugging
                logger.debug(f"Return code: {process.returncode}")
                logger.debug(f"Output length: {len(full_output)}")
                
                if process.returncode != 0:
                    # Command failed
                    error_msg = full_output.strip() or "Unknown error"
                    logger.warning(f"Command failed with code {process.returncode}: {error_msg[:500]}")
                    agent_logger.log_agent_response(
                        timing, 
                        False, 
                        error_msg=f"Exit code {process.returncode}: {error_msg[:200]}"
                    )
                    attempt += 1
                    continue
                
                output = full_output.strip()
                if output:
                    agent_logger.log_agent_response(timing, True, len(output))
                    return output
                
                # Empty output - log and retry
                logger.warning(f"Empty output from {self.NAME} (attempt {attempt + 1}/{max_retries})")
                logger.debug(f"Output: {full_output[:200] if full_output else 'None'}")
                attempt += 1
                
            except subprocess.CalledProcessError as e:
                # Get parsed error with detailed classification
                parsed_error = self._get_parsed_error(e.stderr, e.stdout)
                error_type = self._detect_error_type(e.stderr, e.stdout)
                
                agent_logger.log_agent_response(
                    timing, 
                    False, 
                    error_msg=f"[{parsed_error.category}] {parsed_error.message}"
                )
                
                if error_type == "auth":
                    raise AgentAuthenticationError(
                        str(parsed_error), 
                        self.NAME
                    )
                elif error_type == "quota":
                    raise AgentAuthenticationError(
                        str(parsed_error), 
                        self.NAME
                    )
                else:
                    logger.warning(f"Agent execution failed: {parsed_error}")
                    if not parsed_error.retryable:
                        # Don't retry non-retryable errors
                        raise AgentExecutionError(
                            str(parsed_error), 
                            self.NAME, 
                            attempt + 1
                        )
                    attempt += 1
            
            if attempt < max_retries:
                logger.warning(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
        
        raise AgentExecutionError(
            f"Agent failed after {max_retries} attempts",
            self.NAME,
            max_retries
        )
    
    def get_models(self) -> List[str]:
        """Return list of available models."""
        # Default models - can be extended
        return ["gemini-1.5-pro", "gemini-2.0-flash"]
    
    def is_available(self) -> bool:
        """Check if Antigravity CLI is available."""
        cmd = self.command_override or self.COMMAND
        
        # Try direct path
        if os.path.exists(cmd):
            return True
        
        # Try finding in PATH
        result = subprocess.run(
            ["where", cmd] if os.name == "nt" else ["which", cmd],
            capture_output=True
        )
        
        return result.returncode == 0
    
    def get_installation_hint(self) -> str:
        """Return installation instructions."""
        return "Install Antigravity CLI: npm install -g @google/antigravity-cli"


# Auto-register
from .registry import AgentRegistry
AgentRegistry().register("antigravity", AntigravityAdapter)
AgentRegistry().register("agy", AntigravityAdapter)  # Alias
