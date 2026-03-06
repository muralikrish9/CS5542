"""
CS 5542 — Week 9 Lab: Metrics Collector
Tracks query latency, token usage, error rates, and system health.
"""

import json
import os
import time
import threading
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass
class QueryMetric:
    timestamp: str
    query: str
    backend: str
    latency_ms: float
    tokens_used: int
    success: bool
    error: Optional[str] = None
    iterations: int = 0


class MetricsCollector:
    """Thread-safe metrics collector with file persistence."""

    def __init__(self, log_dir: str = "logs/metrics"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._metrics: list[dict] = []
        self._load_existing()

    def _log_path(self) -> Path:
        return self.log_dir / f"metrics_{datetime.now().strftime('%Y%m%d')}.jsonl"

    def _load_existing(self):
        path = self._log_path()
        if path.exists():
            with open(path) as f:
                for line in f:
                    try:
                        self._metrics.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

    def record(self, metric: QueryMetric):
        """Record a query metric."""
        entry = asdict(metric)
        with self._lock:
            self._metrics.append(entry)
            with open(self._log_path(), "a") as f:
                f.write(json.dumps(entry) + "\n")

    def get_summary(self, last_n: int = 100) -> dict:
        """Get summary statistics for recent queries."""
        with self._lock:
            recent = self._metrics[-last_n:]

        if not recent:
            return {"total": 0}

        latencies = [m["latency_ms"] for m in recent]
        successes = [m for m in recent if m["success"]]
        errors = [m for m in recent if not m["success"]]

        return {
            "total": len(recent),
            "success_rate": round(len(successes) / len(recent) * 100, 1),
            "avg_latency_ms": round(sum(latencies) / len(latencies), 1),
            "p95_latency_ms": round(sorted(latencies)[int(len(latencies) * 0.95)], 1) if latencies else 0,
            "total_tokens": sum(m["tokens_used"] for m in recent),
            "error_count": len(errors),
            "by_backend": _group_by(recent, "backend"),
        }

    def get_recent(self, n: int = 20) -> list[dict]:
        with self._lock:
            return self._metrics[-n:]


def _group_by(metrics: list[dict], key: str) -> dict:
    groups = {}
    for m in metrics:
        g = m.get(key, "unknown")
        if g not in groups:
            groups[g] = {"count": 0, "avg_latency": 0, "total_latency": 0}
        groups[g]["count"] += 1
        groups[g]["total_latency"] += m["latency_ms"]
    for g in groups:
        groups[g]["avg_latency"] = round(groups[g]["total_latency"] / groups[g]["count"], 1)
        del groups[g]["total_latency"]
    return groups


# Singleton
_collector = None

def get_collector(log_dir: str = "logs/metrics") -> MetricsCollector:
    global _collector
    if _collector is None:
        _collector = MetricsCollector(log_dir)
    return _collector
