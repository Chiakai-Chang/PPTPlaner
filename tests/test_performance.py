"""
Unit tests for performance monitoring.
"""
import pytest
import time
from agents.performance import PerformanceMonitor, AgentCallMetrics


class TestPerformanceMonitor:
    """Test performance monitoring functionality."""
    
    @pytest.fixture
    def monitor(self):
        """Create a fresh monitor for each test."""
        monitor = PerformanceMonitor()
        monitor.reset()
        yield monitor
        # Don't reset after test to preserve singleton state
    
    def test_record_call(self, monitor):
        """Test recording an agent call."""
        monitor.record_call(
            agent_name="test-agent",
            mode="PLAN",
            duration_ms=1000,
            success=True,
            model="gemini-1.5-pro",
            response_size=500
        )
        
        summary = monitor.get_summary()
        assert summary["total_calls"] == 1
        assert summary["successful"] == 1
    
    def test_success_rate_calculation(self, monitor):
        """Test success rate calculation."""
        # Record 3 successful calls
        for _ in range(3):
            monitor.record_call(
                agent_name="test",
                mode="PLAN",
                duration_ms=100,
                success=True
            )
        
        # Record 2 failed calls
        for _ in range(2):
            monitor.record_call(
                agent_name="test",
                mode="PLAN",
                duration_ms=100,
                success=False
            )
        
        summary = monitor.get_summary()
        assert summary["total_calls"] == 5
        assert summary["successful"] == 3
        assert summary["failed"] == 2
        assert summary["success_rate"] == 60.0
    
    def test_duration_statistics(self, monitor):
        """Test duration statistics calculation."""
        # Record calls with different durations
        monitor.record_call("agent", "PLAN", 100, True)
        monitor.record_call("agent", "PLAN", 200, True)
        monitor.record_call("agent", "PLAN", 300, True)
        
        summary = monitor.get_summary()
        assert summary["avg_duration_ms"] == 200.0
        assert summary["max_duration_ms"] == 300.0
        assert summary["min_duration_ms"] == 100.0
    
    def test_agent_grouping(self, monitor):
        """Test that calls are grouped by agent."""
        monitor.record_call("agent1", "PLAN", 100, True)
        monitor.record_call("agent1", "PLAN", 200, True)
        monitor.record_call("agent2", "PLAN", 300, True)
        
        summary = monitor.get_summary()
        assert "agent1" in summary["agents"]
        assert "agent2" in summary["agents"]
        assert summary["agents"]["agent1"]["calls"] == 2
        assert summary["agents"]["agent2"]["calls"] == 1
    
    def test_recent_calls(self, monitor):
        """Test getting recent calls."""
        for i in range(5):
            monitor.record_call("agent", "PLAN", 100 + i, True)
        
        recent = monitor.get_recent_calls(3)
        assert len(recent) == 3
        # Most recent should be last recorded
        assert recent[0]["duration_ms"] == 104.0
    
    def test_no_data_summary(self, monitor):
        """Test summary when no data is available."""
        monitor.reset()
        summary = monitor.get_summary()
        assert summary["status"] == "no_data"
    
    def test_reset(self, monitor):
        """Test resetting all metrics."""
        monitor.record_call("agent", "PLAN", 100, True)
        assert monitor.get_summary()["total_calls"] == 1
        
        monitor.reset()
        assert monitor.get_summary()["status"] == "no_data"
    
    def test_concurrent_access(self, monitor):
        """Test thread-safe access."""
        import threading
        
        def record_calls():
            for _ in range(10):
                monitor.record_call("agent", "PLAN", 100, True)
        
        threads = [threading.Thread(target=record_calls) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        summary = monitor.get_summary()
        assert summary["total_calls"] == 50
