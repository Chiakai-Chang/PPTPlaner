"""
Antigravity CLI Adapter

Supports the Antigravity CLI (agy) command-line tool.
This is the successor to Gemini CLI.

IMPORTANT: agy is a TTY-aware CLI. It requires a pseudo-terminal (PTY)
to produce output. Standard subprocess.PIPE will NOT work.
This adapter uses pywinpty on Windows to create a PTY.

IMPORTANT: For large prompts, we write to a temp file and use stdin
because Windows command line has a 8191 character limit.
"""
import subprocess
import os
import shutil
import time
import re
import logging
import threading
import tempfile
from typing import Optional, List, Dict, Any
from .base import AgentInterface
from .exceptions import AgentExecutionError, AgentAuthenticationError
from .retry import RetryStrategy

logger = logging.getLogger(__name__)


# Windows command line limit
WINDOWS_CMD_LIMIT = 8000  # Be conservative, actual limit is 8191


class AntigravityAdapter(AgentInterface):
    """Antigravity CLI (agy) adapter.
    
    Uses pywinpty to create a pseudo-terminal for agy CLI,
    which requires TTY to output results.
    
    For large prompts (>8KB), writes prompt to temp file
    to avoid Windows command line length limit.
    """
    
    NAME = "Antigravity CLI"
    COMMAND = "agy"
    
    # Cooldown settings
    COOLDOWN_DURATION = 5  # Seconds between calls
    COOLDOWN_AFTER_LARGE = 15  # Extra cooldown after large outputs
    LARGE_OUTPUT_THRESHOLD = 5000  # Characters that trigger extra cooldown
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model = config.get("agent_config", {}).get("model") or config.get("model")
        self.max_retries = config.get("agent_config", {}).get("max_retries", 3)
        self.retry_delay = config.get("agent_config", {}).get("retry_delay", 5)
        self.command_override = config.get("agent_config", {}).get("command_override")
        self._use_pywinpty = True  # Enable by default
        
        # Resolve command path to absolute path for winpty reliability
        cmd = self.command_override or self.COMMAND
        self.resolved_command = cmd
        found_cmd = shutil.which(cmd)
        if found_cmd:
            self.resolved_command = found_cmd
        else:
            if os.name == 'nt':
                local_appdata = os.environ.get('LOCALAPPDATA', '')
                if local_appdata:
                    agy_paths = [
                        os.path.join(local_appdata, 'agy', 'bin', 'agy.exe'),
                        os.path.join(local_appdata, 'agy', 'bin', 'agy.EXE'),
                    ]
                    for agy_path in agy_paths:
                        if os.path.exists(agy_path):
                            self.resolved_command = agy_path
                            break
            else:
                candidates = [
                    "/usr/local/bin/agy",
                    "/opt/homebrew/bin/agy",
                    os.path.expanduser("~/.local/bin/agy"),
                ]
                for candidate in candidates:
                    if os.path.exists(candidate):
                        self.resolved_command = candidate
                        break
        
        logger.info(f"[Antigravity] Resolved command to: '{self.resolved_command}'")
        
        # Thread-safe cooldown tracking
        self._last_call_time = 0
        self._last_output_size = 0
        self._lock = threading.Lock()
        
        # Check if pywinpty is available
        try:
            import winpty
            logger.debug("pywinpty available")
        except ImportError:
            logger.warning("pywinpty not available, falling back to subprocess")
            self._use_pywinpty = False
    
    def _cooldown(self):
        """Wait for cooldown period between calls."""
        with self._lock:
            now = time.time()
            elapsed = now - self._last_call_time
            
            # Calculate required cooldown
            required_cooldown = self.COOLDOWN_DURATION
            if self._last_output_size > self.LARGE_OUTPUT_THRESHOLD:
                required_cooldown += self.COOLDOWN_AFTER_LARGE
                logger.debug(f"Large output detected ({self._last_output_size} chars), adding extra cooldown")
            
            sleep_time = max(0, required_cooldown - elapsed)
            
            if sleep_time > 0:
                logger.debug(f"Cooldown: waiting {sleep_time:.1f}s")
                time.sleep(sleep_time)
            
            self._last_call_time = time.time()
    
    def _build_command_with_file(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> tuple[str, str]:
        """Build command using temp file for large prompts.
        
        Returns (cmd_string, temp_file_path)
        """
        cmd_exe = self.resolved_command
        
        # Create temp file with prompt
        temp_dir = os.path.join(os.getcwd(), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        temp_file = os.path.join(temp_dir, f"agy_prompt_{int(time.time()*1000)}.txt")
        
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(prompt)
        
        logger.debug(f"Prompt written to temp file: {temp_file} ({os.path.getsize(temp_file)} bytes)")
        
        # Build command to read from file
        # Use type command to read file content as prompt
        cmd_string = f'"{cmd_exe}" -p "@type {temp_file}" --dangerously-skip-permissions --print-timeout 600s'
        
        return cmd_string, temp_file
    
    def _build_command_inline(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> tuple[List[str], str]:
        """Build command with inline prompt for small prompts.
        
        Returns (cmd_args, temp_file_path)
        """
        cmd_exe = self.resolved_command
        
        cmd_args = [cmd_exe, "-p", prompt, "--dangerously-skip-permissions", "--print-timeout", "600s"]
        
        # Add workspace directory if specified
        workspace = options.get("workspace") if options else None
        if workspace:
            cmd_args.extend(["--add-dir", workspace])
        
        return cmd_args, None
    
    def _build_command(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> tuple[List[str], str]:
        """Build command list for execution.
        
        Uses temp file for large prompts to avoid Windows command line limit.
        
        Returns (cmd_args, temp_file_path)
        """
        # For large prompts, use temp file
        if len(prompt) > WINDOWS_CMD_LIMIT:
            print(f"  ℹ️  [Antigravity] Large prompt ({len(prompt)} chars), using temp file", flush=True)
            return self._build_command_with_file(prompt, options)
        
        return self._build_command_inline(prompt, options)
    
    def _strip_ansi_codes(self, text: str) -> str:
        """Remove ANSI escape codes from terminal output."""
        # ANSI escape sequences
        ansi_escape = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]|\x1b\([^)]*\)|\x1b\[[0-9;]*[mGKH]')
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
    
    def _execute_with_pywinpty(self, cmd_args: List[str]) -> str:
        """Execute command using pywinpty for TTY support."""
        from winpty import PtyProcess
        
        print(f"  🔄 [Antigravity] Executing command... (may take 1-10 minutes)", flush=True)
        
        proc = PtyProcess.spawn(cmd_args)
        
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
    
    def _execute_with_subprocess(self, cmd_args: List[str]) -> str:
        """Fallback to subprocess if pywinpty not available."""
        process = subprocess.Popen(
            cmd_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            shell=False,
            bufsize=1
        )
        
        full_output = ""
        for line in process.stdout:
            full_output += line
        
        process.wait()
        return full_output

    def _execute_with_unix_pty(self, cmd_args: List[str]) -> str:
        """Execute command using native pty on macOS/Linux for TTY support."""
        import pty
        import os
        import sys
        
        print(f"  🔄 [Antigravity] Executing command in Unix PTY... (may take 1-10 minutes)", flush=True)
        
        master_fd, slave_fd = pty.openpty()
        try:
            process = subprocess.Popen(
                cmd_args,
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                shell=False,
                close_fds=True,
            )
        finally:
            # Safe to close in parent, child maintains open reference
            os.close(slave_fd)
            
        full_output = b""
        timeout = 600  # 10 minutes
        elapsed = 0
        last_progress = 0
        
        # Read from master end of the pseudo-terminal
        while process.poll() is None and elapsed < timeout:
            try:
                # Use non-blocking read or check ready using select
                import select
                r, _, _ = select.select([master_fd], [], [], 0.1)
                if master_fd in r:
                    chunk = os.read(master_fd, 4096)
                    if chunk:
                        full_output += chunk
                        # Show progress every 30 seconds
                        if elapsed - last_progress > 30:
                            minutes = int(elapsed // 60)
                            seconds = int(elapsed % 60)
                            print(f"  ⏳ [Antigravity] Processing... {minutes}m {seconds}s elapsed", flush=True)
                            last_progress = elapsed
            except OSError:
                break
            
            time.sleep(0.1)
            elapsed += 0.1
            
        # Read any remaining output after process exits
        try:
            import select
            while select.select([master_fd], [], [], 0.0)[0]:
                chunk = os.read(master_fd, 4096)
                if not chunk:
                    break
                full_output += chunk
        except OSError:
            pass
            
        # Clean up process if still alive
        if process.poll() is None:
            print(f"  ⚠️ [Antigravity] Timeout after {int(elapsed)}s, killing process", flush=True)
            process.kill()
            process.wait()
            
        os.close(master_fd)
        decoded = full_output.decode("utf-8", errors="replace")
        print(f"  ✅ [Antigravity] Received {len(decoded)} chars", flush=True)
        return decoded
    
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
        
        # Apply cooldown before starting
        self._cooldown()
        
        attempt = 0
        while attempt < max_retries:
            timing = agent_logger.log_agent_call(
                self.NAME, mode, model, attempt + 1, max_retries
            )
            
            try:
                logger.info(f"Calling {self.NAME} for {mode}... (Attempt {attempt + 1}/{max_retries})")
                
                # Build command list (uses temp file for large prompts)
                cmd_args, temp_file = self._build_command(prompt, options)
                logger.debug(f"Command args: {cmd_args}")
                
                if temp_file:
                    logger.debug(f"Prompt file: {temp_file} ({os.path.getsize(temp_file)} bytes)")
                
                # Execute using pywinpty (TTY required)
                import sys
                if self._use_pywinpty:
                    raw_output = self._execute_with_pywinpty(cmd_args)
                elif sys.platform != "win32":
                    try:
                        raw_output = self._execute_with_unix_pty(cmd_args)
                    except Exception as e:
                        logger.warning(f"Unix PTY failed, falling back to subprocess: {e}")
                        raw_output = self._execute_with_subprocess(cmd_args)
                else:
                    raw_output = self._execute_with_subprocess(cmd_args)
                
                # Clean up temp file
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                
                # Clean up output
                output = self._strip_ansi_codes(raw_output)
                output = self._extract_json(output)
                
                # Track output size for cooldown
                with self._lock:
                    self._last_output_size = len(output)
                
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
        """Check if Antigravity CLI is available.
        
        Checks multiple locations:
        1. Command in PATH (via shutil.which)
        2. Direct file path
        3. Common installation locations (Windows & macOS/Linux)
        """
        import sys
        import shutil
        cmd = self.command_override or self.COMMAND
        
        print(f"[Antigravity] Checking availability for command: '{cmd}'", file=sys.stderr, flush=True)
        print(f"[Antigravity] os.name: {os.name}", file=sys.stderr, flush=True)
        
        # 1. Check if command exists directly or in PATH using shutil.which
        if shutil.which(cmd):
            print(f"[Antigravity] Command found via shutil.which", file=sys.stderr, flush=True)
            return True
            
        if os.path.exists(cmd):
            print(f"[Antigravity] Command found via os.path.exists", file=sys.stderr, flush=True)
            return True
        
        # 2. Try common installation locations on Windows
        if os.name == 'nt':
            print(f"[Antigravity] Running 'where {cmd}'...", file=sys.stderr, flush=True)
            try:
                result = subprocess.run(
                    ["where", cmd],
                    capture_output=True,
                    timeout=5
                )
                print(f"[Antigravity] where returncode: {result.returncode}", file=sys.stderr, flush=True)
                if result.returncode == 0:
                    print(f"[Antigravity] Command found via 'where'", file=sys.stderr, flush=True)
                    return True
            except Exception as e:
                print(f"[Antigravity] Exception in 'where' call: {e}", file=sys.stderr, flush=True)
            
            local_appdata = os.environ.get('LOCALAPPDATA', '')
            if local_appdata:
                agy_paths = [
                    os.path.join(local_appdata, 'agy', 'bin', 'agy.EXE'),
                    os.path.join(local_appdata, 'agy', 'bin', 'agy.exe'),
                ]
                for agy_path in agy_paths:
                    if os.path.exists(agy_path):
                        print(f"[Antigravity] Command found at: {agy_path}", file=sys.stderr, flush=True)
                        return True
                        
        # 3. Try common installation locations on macOS/Linux
        else:
            candidates = [
                "/usr/local/bin/agy",
                "/opt/homebrew/bin/agy",
                os.path.expanduser("~/.local/bin/agy"),
            ]
            for candidate in candidates:
                if os.path.exists(candidate):
                    print(f"[Antigravity] Command found at: {candidate}", file=sys.stderr, flush=True)
                    return True
        
        print(f"[Antigravity] Command NOT found", file=sys.stderr, flush=True)
        return False
    
    def get_installation_hint(self) -> str:
        """Return installation instructions."""
        return "Install Antigravity CLI: irm https://antigravity.google/cli/install.ps1 | iex"


# Auto-register
from .registry import AgentRegistry
AgentRegistry().register("antigravity", AntigravityAdapter)
AgentRegistry().register("agy", AntigravityAdapter)  # Alias
