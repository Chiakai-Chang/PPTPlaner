"""
Unit tests for RetryStrategy.
"""
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
