"""
Metrics Collection and Performance Analytics for Distributed Cache Simulation.
Calculates hit/miss rates, latency percentiles (P50, P90, P95, P99),
eviction totals, and traffic distribution across cluster nodes.
"""

import math
from typing import Dict, List, Any, Optional


class MetricsCollector:
    """
    Collects per-request telemetry and computes high-resolution statistics.
    """

    def __init__(self) -> None:
        self.total_requests: int = 0
        self.hits: int = 0
        self.misses: int = 0
        self.evictions: int = 0
        self.expired: int = 0
        self.get_ops: int = 0
        self.set_ops: int = 0
        self.db_reads: int = 0
        self.db_writes: int = 0

        self.latencies: List[float] = []
        self.node_requests: Dict[str, int] = {}
        self.node_hits: Dict[str, int] = {}
        self.node_misses: Dict[str, int] = {}

    def record_request(
        self,
        op: str,
        hit: bool,
        latency_ms: float,
        node_id: Optional[str] = None,
        evicted: bool = False,
        expired: bool = False,
        db_read: bool = False,
        db_write: bool = False
    ) -> None:
        """Record a single request's operational outcomes."""
        self.total_requests += 1
        self.latencies.append(latency_ms)

        if op.upper() == "GET":
            self.get_ops += 1
            if hit:
                self.hits += 1
            else:
                self.misses += 1
        elif op.upper() == "SET":
            self.set_ops += 1

        if evicted:
            self.evictions += 1
        if expired:
            self.expired += 1
        if db_read:
            self.db_reads += 1
        if db_write:
            self.db_writes += 1

        if node_id:
            self.node_requests[node_id] = self.node_requests.get(node_id, 0) + 1
            if hit:
                self.node_hits[node_id] = self.node_hits.get(node_id, 0) + 1
            elif op.upper() == "GET":
                self.node_misses[node_id] = self.node_misses.get(node_id, 0) + 1

    def _percentile(self, sorted_data: List[float], p: float) -> float:
        """Compute percentile p in [0, 100] using linear interpolation."""
        if not sorted_data:
            return 0.0
        n = len(sorted_data)
        if n == 1:
            return sorted_data[0]

        rank = (p / 100.0) * (n - 1)
        lower = int(rank)
        upper = min(lower + 1, n - 1)
        weight = rank - lower
        return round(sorted_data[lower] * (1.0 - weight) + sorted_data[upper] * weight, 3)

    def summary(self) -> Dict[str, Any]:
        """
        Compile and return complete statistical summary.
        """
        total_lookups = self.hits + self.misses
        hit_rate = (self.hits / total_lookups * 100) if total_lookups > 0 else 0.0
        miss_rate = (self.misses / total_lookups * 100) if total_lookups > 0 else 0.0

        sorted_latencies = sorted(self.latencies) if self.latencies else []
        avg_lat = (sum(self.latencies) / len(self.latencies)) if self.latencies else 0.0
        min_lat = sorted_latencies[0] if sorted_latencies else 0.0
        max_lat = sorted_latencies[-1] if sorted_latencies else 0.0

        p50 = self._percentile(sorted_latencies, 50.0)
        p90 = self._percentile(sorted_latencies, 90.0)
        p95 = self._percentile(sorted_latencies, 95.0)
        p99 = self._percentile(sorted_latencies, 99.0)

        # Node load distribution breakdown
        node_breakdown = {}
        for node_id, count in self.node_requests.items():
            pct = round((count / self.total_requests * 100), 2) if self.total_requests > 0 else 0.0
            node_hits = self.node_hits.get(node_id, 0)
            node_misses = self.node_misses.get(node_id, 0)
            node_total = node_hits + node_misses
            node_hr = round((node_hits / node_total * 100), 2) if node_total > 0 else 0.0
            node_breakdown[node_id] = {
                "requests": count,
                "percentage": pct,
                "hits": node_hits,
                "misses": node_misses,
                "hit_rate_pct": node_hr,
            }

        # Calculate standard deviation of node traffic
        req_counts = list(self.node_requests.values())
        if len(req_counts) > 1:
            mean_req = sum(req_counts) / len(req_counts)
            var = sum((c - mean_req) ** 2 for c in req_counts) / len(req_counts)
            std_dev_load = round(math.sqrt(var), 2)
        else:
            std_dev_load = 0.0

        return {
            "total_requests": self.total_requests,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_pct": round(hit_rate, 2),
            "miss_rate_pct": round(miss_rate, 2),
            "evictions": self.evictions,
            "expired": self.expired,
            "get_operations": self.get_ops,
            "set_operations": self.set_ops,
            "db_reads": self.db_reads,
            "db_writes": self.db_writes,
            "latency": {
                "avg_ms": round(avg_lat, 3),
                "min_ms": round(min_lat, 3),
                "max_ms": round(max_lat, 3),
                "p50_ms": p50,
                "p90_ms": p90,
                "p95_ms": p95,
                "p99_ms": p99,
            },
            "node_distribution": node_breakdown,
            "load_std_dev": std_dev_load,
        }
