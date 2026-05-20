"""
RetryStrategy - Configurable retry logic for agent execution.
"""
import time
from typing import Callable, Tuple, Any
from .exceptions import AgentExecutionError


class RetryStrategy:
    """Configurable retry strategy."""
    
    def __init__(
        self,
        max_retries: int = 3,
        delay: int = 5,
        backoff_factor: float = 2.0,
        retryable_exceptions: Tuple[type, ...] | None = None
    ):
        self.max_retries = max_retries
        self.delay = delay
        self.backoff_factor = backoff_factor
        self.retryable_exceptions = retryable_exceptions or (AgentExecutionError,)
    
    def execute_with_retry(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute function with retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except self.retryable_exceptions as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    sleep_time = self.delay * (self.backoff_factor ** attempt)
                    time.sleep(sleep_time)
        
        raise last_exception
