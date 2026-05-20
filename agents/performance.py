"""
Performance monitoring for PPTPlaner agent system.

Provides metrics collection and reporting for agent execution.
"""
import time
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class AgentCallMetrics:
    """Metrics for a single agent call."""
    timestamp: float
    agent_name: str
    mode: str
    model: Optional[str]
    duration_ms: float
    success: bool
    response_size: int = 0
    retry_count: int = 0
    error_category: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.timestamp)),
            "agent": self.agent_name,
            "mode": self.mode,
            "model": self.model,
            "duration_ms": round(self.duration_ms, 2),
            "success": self.success,
            "response_size": self.response_size,
            "retries": self.retry_count,
            "error": self.error_category
        }


class PerformanceMonitor:
    """
    Monitors and reports agent performance metrics.
    
    Thread-safe singleton for collecting metrics across the application.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._metrics: List[AgentCallMetrics] = []
        self._metrics_lock = threading.Lock()
        self._start_time = time.time()
    
    def record_call(
        self,
        agent_name: str,
        mode: str,
        duration_ms: float,
        success: bool,
        model: Optional[str] = None,
        response_size: int = 0,
        retry_count: int = 0,
        error_category: Optional[str] = None
    ):
        """Record an agent call."""
        metrics = AgentCallMetrics(
            timestamp=time.time(),
            agent_name=agent_name,
            mode=mode,
            model=model,
            duration_ms=duration_ms,
            success=success,
            response_size=response_size,
            retry_count=retry_count,
            error_category=error_category
        )
        
        with self._metrics_lock:
            self._metrics.append(metrics)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        with self._metrics_lock:
            if not self._metrics:
                return {"status": "no_data"}
            
            total_calls = len(self._metrics)
            successful = sum(1 for m in self._metrics if m.success)
            failed = total_calls - successful
            
            durations = [m.duration_ms for m in self._metrics]
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)
            
            # Group by agent
            by_agent = defaultdict(list)
            for m in self._metrics:
                by_agent[m.agent_name].append(m)
            
            agent_stats = {}
            for agent, calls in by_agent.items():
                agent_durations = [c.duration_ms for c in calls]
                agent_stats[agent] = {
                    "calls": len(calls),
                    "avg_ms": round(sum(agent_durations) / len(agent_durations), 2),
                    "max_ms": round(max(agent_durations), 2),
                    "success_rate": round(
                        sum(1 for c in calls if c.success) / len(calls) * 100, 1
                    )
                }
            
            return {
                "total_calls": total_calls,
                "successful": successful,
                "failed": failed,
                "success_rate": round(successful / total_calls * 100, 1),
                "avg_duration_ms": round(avg_duration, 2),
                "max_duration_ms": round(max_duration, 2),
                "min_duration_ms": round(min_duration, 2),
                "uptime_seconds": round(time.time() - self._start_time, 1),
                "agents": agent_stats
            }
    
    def get_recent_calls(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent agent calls."""
        with self._metrics_lock:
            recent = self._metrics[-limit:]
            return [m.to_dict() for m in reversed(recent)]
    
    def reset(self):
        """Reset all metrics."""
        with self._metrics_lock:
            self._metrics.clear()
            self._start_time = time.time()
    
    def print_report(self):
        """Print performance report to console."""
        summary = self.get_summary()
        
        print("\n" + "="*60)
        print("📊 PPTPlaner 效能報告")
        print("="*60)
        
        if summary.get("status") == "no_data":
            print("  沒有效能數據")
            return
        
        print(f"\n📈 總覽")
        print(f"  總呼叫數: {summary['total_calls']}")
        print(f"  成功: {summary['successful']} ({summary['success_rate']}%)")
        print(f"  失敗: {summary['failed']}")
        print(f"  平均延遲: {summary['avg_duration_ms']}ms")
        print(f"  最大延遲: {summary['max_duration_ms']}ms")
        print(f"  最小延遲: {summary['min_duration_ms']}ms")
        
        if "agents" in summary:
            print(f"\n🤖 Agent 效能")
            for agent, stats in summary["agents"].items():
                print(f"\n  {agent}:")
                print(f"    呼叫數: {stats['calls']}")
                print(f"    平均延遲: {stats['avg_ms']}ms")
                print(f"    成功率: {stats['success_rate']}%")
        
        print("\n" + "="*60)


# Global performance monitor instance
performance_monitor = PerformanceMonitor()
