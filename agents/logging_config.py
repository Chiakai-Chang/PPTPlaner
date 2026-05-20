"""
Enhanced logging configuration for PPTPlaner agent system.

Provides structured logging with timing information for agent execution.
"""
import logging
import time
from typing import Any, Dict, Optional


class AgentLogger:
    """Enhanced logger for agent operations."""
    
    def __init__(self, name: str = "pptplaner.agent"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Add console handler if not exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%H:%M:%S"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def log_agent_call(
        self,
        agent_name: str,
        mode: str,
        model: Optional[str] = None,
        attempt: int = 1,
        max_attempts: int = 3
    ) -> Dict[str, Any]:
        """Log the start of an agent call and return timing info."""
        timestamp = time.time()
        
        self.logger.info(
            f"🔹 [{agent_name}] Starting {mode} "
            f"(attempt {attempt}/{max_attempts}, model={model})"
        )
        
        return {
            "start_time": timestamp,
            "agent_name": agent_name,
            "mode": mode
        }
    
    def log_agent_response(
        self,
        timing_info: Dict[str, Any],
        success: bool,
        response_length: int = 0,
        error_msg: Optional[str] = None
    ):
        """Log the completion of an agent call."""
        elapsed = time.time() - timing_info["start_time"]
        
        if success:
            self.logger.info(
                f"✅ [{timing_info['agent_name']}] {timing_info['mode']} "
                f"completed in {elapsed:.2f}s ({response_length} chars)"
            )
        else:
            self.logger.warning(
                f"❌ [{timing_info['agent_name']}] {timing_info['mode']} "
                f"failed after {elapsed:.2f}s: {error_msg}"
            )
    
    def log_config(self, config: Dict[str, Any]):
        """Log agent configuration (masked for sensitive data)."""
        safe_config = config.copy()
        
        # Mask sensitive values
        for key in ["api_key", "token"]:
            if key in safe_config:
                safe_config[key] = "***masked***"
        
        self.logger.debug(f"Agent config: {safe_config}")


# Global logger instance
agent_logger = AgentLogger()
