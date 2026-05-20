"""
Enhanced logging configuration for PPTPlaner agent system.

Provides structured logging with timing information for agent execution.
Also integrates with performance monitoring.
"""
import logging
import sys
import time
from typing import Any, Dict, Optional
from .performance import performance_monitor


class AgentLogger:
    """Enhanced logger for agent operations."""
    
    def __init__(self, name: str = "pptplaner.agent"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Add console handler if not exists
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%H:%M:%S"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def set_research_logger(self, research_logger):
        """Set the research logger for dual logging."""
        self._research_logger = research_logger
    
    def _log_to_research(self, message: str):
        """Log message to research log if available."""
        if hasattr(self, '_research_logger'):
            self._research_logger(message)
    
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
        
        msg = f"🔹 [{agent_name}] Starting {mode} (attempt {attempt}/{max_attempts}, model={model})"
        self.logger.info(msg)
        self._log_to_research(f"AGENT_CALL: {msg}")
        
        return {
            "start_time": timestamp,
            "agent_name": agent_name,
            "mode": mode,
            "model": model,
            "attempt": attempt,
            "max_attempts": max_attempts
        }
    
    def log_agent_response(
        self,
        timing_info: Dict[str, Any],
        success: bool,
        response_length: int = 0,
        error_msg: Optional[str] = None
    ):
        """Log the completion of an agent call and record metrics."""
        elapsed = time.time() - timing_info["start_time"]
        elapsed_ms = elapsed * 1000
        
        # Record performance metrics
        performance_monitor.record_call(
            agent_name=timing_info["agent_name"],
            mode=timing_info["mode"],
            duration_ms=elapsed_ms,
            success=success,
            model=timing_info.get("model"),
            response_size=response_length,
            retry_count=timing_info.get("attempt", 1) - 1,
            error_category="error" if error_msg else None
        )
        
        if success:
            msg = f"✅ [{timing_info['agent_name']}] {timing_info['mode']} completed in {elapsed:.2f}s ({response_length} chars)"
            self.logger.info(msg)
            self._log_to_research(f"AGENT_SUCCESS: {msg}")
        else:
            msg = f"❌ [{timing_info['agent_name']}] {timing_info['mode']} failed after {elapsed:.2f}s: {error_msg}"
            self.logger.warning(msg)
            self._log_to_research(f"AGENT_FAILURE: {msg}")
    
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
            "mode": mode,
            "model": model,
            "attempt": attempt,
            "max_attempts": max_attempts
        }
    
    def log_agent_response(
        self,
        timing_info: Dict[str, Any],
        success: bool,
        response_length: int = 0,
        error_msg: Optional[str] = None
    ):
        """Log the completion of an agent call and record metrics."""
        elapsed = time.time() - timing_info["start_time"]
        elapsed_ms = elapsed * 1000
        
        # Record performance metrics
        performance_monitor.record_call(
            agent_name=timing_info["agent_name"],
            mode=timing_info["mode"],
            duration_ms=elapsed_ms,
            success=success,
            model=timing_info.get("model"),
            response_size=response_length,
            retry_count=timing_info.get("attempt", 1) - 1,
            error_category="error" if error_msg else None
        )
        
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
