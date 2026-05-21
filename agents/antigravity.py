"""
Antigravity CLI Adapter

Supports the Antigravity CLI (agy) command-line tool.
This is the successor to Gemini CLI.

IMPORTANT: agy is a TTY-aware CLI. It requires a pseudo-terminal (PTY)
to produce output. Standard subprocess.PIPE will NOT work.
This adapter uses pywinpty on Windows to create a PTY.
"""
import subprocess
import os
import time
import re
import logging
from typing import Optional, List, Dict, Any
from .base import AgentInterface
from .exceptions import AgentExecutionError, AgentAuthenticationError
from .retry import RetryStrategy

logger = logging.getLogger(__name__)


class AntigravityAdapter(AgentInterface):
    """Antigravity CLI (agy) adapter.
    
    Uses pywinpty to create a pseudo-terminal for agy CLI,
    which requires TTY to output results.
    """
    
    NAME = "Antigravity CLI"
    COMMAND = "agy"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model = config.get("agent_config", {}).get("model") or config.get("model")
        self.max_retries = config.get("agent_config", {}).get("max_retries", 3)
        self.retry_delay = config.get("agent_config", {}).get("retry_delay", 5)
        self.command_override = config.get("agent_config", {}).get("command_override")
        self._use_pywinpty = True  # Enable by default
        
        # Check if pywinpty is available
        try:
            import winpty
            logger.debug("pywinpty available")
        except ImportError:
            logger.warning("pywinpty not available, falling back to subprocess")
            self._use_pywinpty = False
    
    def _build_command_string(self, prompt: str, mode: str, options: Optional[Dict[str, Any]] = None) -> str:
        """Build command string for shell execution.
        
        Returns a shell command string for pywinpty.
        """
        cmd_exe = self.command_override or self.COMMAND
        
        # Build command parts - escape quotes in prompt
        escaped_prompt = prompt.replace('"', '\\"')
        parts = [cmd_exe, "-p", f'"{escaped_prompt}"']
        
        # Auto-approve tool permissions
        parts.append("--dangerously-skip-permissions")
        
        # Add timeout
        parts.append("--print-timeout 600s")
        
        # Add workspace directory if specified
        workspace = options.get("workspace") if options else None
        if workspace:
            parts.extend(["--add-dir", workspace])
        
        return " ".join(parts)
    
    def _strip_ansi_codes(self, text: str) -> str:
        """Remove ANSI escape codes from terminal output."""
        # ANSI escape sequences
        ansi_escape = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]|\x1b\([^)]*\)|\x1b\[[0-9;]*[mGKH]|\\r\\n')
        text = ansi_escape.sub('', text)
        
        # Remove other control characters
        text = re.sub(r'\x1b\?.*?[hH]', '', text)
        
        return text
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON content from markdown code blocks."""
        # Try to find JSON in code blocks
        json_match = re.search(r'```(?:json)?\s*\n?(.+?)\s*```', text, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()
        
        # Try to find bare JSON
        json_match = re.search(r'\{[^{}]+(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        return text.strip()
    
    def _execute_with_pywinpty(self, cmd_string: str) -> str:
        """Execute command using pywinpty for TTY support."""
        from winpty import PtyProcess
        
        print(f"  🔄 [Antigravity] Executing command... (may take 1-10 minutes)", flush=True)
        
        proc = PtyProcess.spawn(cmd_string)
        
        full_output = ""
        timeout = 600  # 10 minutes for local models
        elapsed = 0
        idle_time = 0
        last_progress = 0
        
        while proc.isalive() and elapsed < timeout:
            try:
                chunk = proc.read(4096)
                if chunk:
                    full_output += chunk
                    idle_time = 0
                    # Show progress every 30 seconds
                    if elapsed - last_progress > 30:
                        minutes = int(elapsed // 60)
                        seconds = int(elapsed % 60)
                        print(f"  ⏳ [Antigravity] Processing... {minutes}m {seconds}s elapsed", flush=True)
                        last_progress = elapsed
            except EOFError:
                break
            
            time.sleep(0.1)
            elapsed += 0.1
        
        # Clean up process if still alive
        if proc.isalive():
            print(f"  ⚠️ [Antigravity] Timeout after {int(elapsed)}s, killing process", flush=True)
            proc.kill()
        
        print(f"  ✅ [Antigravity] Received {len(full_output)} chars", flush=True)
        return full_output
    
    def _execute_with_subprocess(self, cmd_string: str) -> str:
        """Fallback to subprocess if pywinpty not available."""
        process = subprocess.Popen(
            cmd_string,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            shell=True,
            bufsize=1
        )
        
        full_output = ""
        for line in process.stdout:
            full_output += line
        
        process.wait()
        return full_output
    
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
        
        attempt = 0
        while attempt < max_retries:
            timing = agent_logger.log_agent_call(
                self.NAME, mode, model, attempt + 1, max_retries
            )
            
            try:
                logger.info(f"Calling {self.NAME} for {mode}... (Attempt {attempt + 1}/{max_retries})")
                
                # Build command string
                cmd_string = self._build_command_string(prompt, mode, options)
                logger.debug(f"Command: {cmd_string}")
                
                # Execute using pywinpty (TTY required)
                if self._use_pywinpty:
                    raw_output = self._execute_with_pywinpty(cmd_string)
                else:
                    raw_output = self._execute_with_subprocess(cmd_string)
                
                # Clean up output
                output = self._strip_ansi_codes(raw_output)
                output = self._extract_json(output)
                
                # Log result
                logger.debug(f"Output length: {len(output)}")
                
                if output.strip():
                    agent_logger.log_agent_response(timing, True, len(output))
                    return output.strip()
                
                # Empty output - log and retry
                logger.warning(f"Empty output from {self.NAME} (attempt {attempt + 1}/{max_retries})")
                logger.debug(f"Raw output: {raw_output[:200] if raw_output else 'None'}")
                attempt += 1
                
            except Exception as e:
                logger.error(f"Error executing {self.NAME}: {e}")
                agent_logger.log_agent_response(timing, False, error_msg=str(e))
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
        return ["gemini-1.5-pro", "gemini-2.0-flash"]
    
    def is_available(self) -> bool:
        """Check if Antigravity CLI is available."""
        cmd = self.command_override or self.COMMAND
        
        if os.path.exists(cmd):
            return True
        
        result = subprocess.run(
            ["where", cmd] if os.name == "nt" else ["which", cmd],
            capture_output=True
        )
        
        return result.returncode == 0
    
    def get_installation_hint(self) -> str:
        """Return installation instructions."""
        return "Install Antigravity CLI: irm https://antigravity.google/cli/install.ps1 | iex"


# Auto-register
from .registry import AgentRegistry
AgentRegistry().register("antigravity", AntigravityAdapter)
AgentRegistry().register("agy", AntigravityAdapter)  # Alias
