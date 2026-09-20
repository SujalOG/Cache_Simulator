"""
Redis Benchmark Runner.
Connects to a live Redis server via connection pooling, configures memory limits
and eviction policies, replays identical workloads against Redis, and captures
real network socket round-trip latencies and INFO statistics.
"""

import os
import time
from typing import Dict, List, Optional, Tuple, Any
import redis


class RedisBenchmarkRunner:
    """
    Executes comparative workloads against a live Redis instance.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db: int = 0
    ) -> None:
        self.host = host or os.environ.get("REDIS_HOST", "localhost")
        self.port = port or int(os.environ.get("REDIS_PORT", 6379))
        self.db = db

        self._pool = redis.ConnectionPool(
            host=self.host,
            port=self.port,
            db=self.db,
            socket_timeout=2.0,
            decode_responses=True
        )
        self._client = redis.Redis(connection_pool=self._pool)

    def is_available(self) -> bool:
        """Check if Redis server is reachable."""
        try:
            return bool(self._client.ping())
        except Exception:
            return False

    def configure(self, maxmemory_bytes: int = 2097152, policy: str = "allkeys-lru") -> bool:
        """
        Configure Redis maxmemory limit and eviction policy.
        """
        try:
            self._client.config_set("maxmemory", str(maxmemory_bytes))
            self._client.config_set("maxmemory-policy", policy)
            return True
        except Exception:
            return False

    def run_workload(
        self,
        requests: List[Tuple[str, str, Optional[Any]]],
        policy: str = "allkeys-lru"
    ) -> Dict[str, Any]:
        """
        Execute the exact workload against live Redis.
        Measures individual request latencies and inspects INFO stats.
        """
        if not self.is_available():
            return {
                "available": False,
                "message": f"Redis is not reachable at {self.host}:{self.port}. Run via Docker to enable live Redis baseline.",
                "total_requests": len(requests),
                "hit_rate_pct": 0.0,
                "latency": {"avg_ms": 0.0, "p95_ms": 0.0}
            }

        try:
            self._client.flushdb()
            self._client.config_resetstat()
            # Redis startup overhead is ~1MB; ensure maxmemory is comfortably above it to permit keys and evictions
            try:
                mem_info = self._client.info("memory")
                base_overhead = mem_info.get("used_memory_startup", 1000000)
            except Exception:
                base_overhead = 1000000
            target_mem = max(base_overhead + 600000, 2097152)
            self.configure(maxmemory_bytes=target_mem, policy=policy)

            latencies: List[float] = []
            hits = 0
            misses = 0

            for op, key, val in requests:
                t0 = time.perf_counter()
                if op == "GET":
                    res = self._client.get(key)
                    t1 = time.perf_counter()
                    lat_ms = (t1 - t0) * 1000.0
                    latencies.append(lat_ms)

                    if res is not None:
                        hits += 1
                    else:
                        misses += 1
                        # Cache-aside on miss: set simulated value
                        self._client.set(key, f"redis_val_{key}")
                elif op == "SET":
                    val_to_set = val if val is not None else f"val_{key}"
                    self._client.set(key, val_to_set)
                    t1 = time.perf_counter()
                    lat_ms = (t1 - t0) * 1000.0
                    latencies.append(lat_ms)

            # Retrieve Redis telemetry
            info_stats = self._client.info("stats")
            keyspace_hits = info_stats.get("keyspace_hits", hits)
            keyspace_misses = info_stats.get("keyspace_misses", misses)
            evictions = info_stats.get("evicted_keys", 0)

            total_lookups = hits + misses
            hit_rate = (hits / total_lookups * 100) if total_lookups > 0 else 0.0

            sorted_lats = sorted(latencies)
            p95_idx = int(0.95 * len(sorted_lats))
            p95_lat = sorted_lats[p95_idx] if sorted_lats else 0.0
            avg_lat = sum(latencies) / len(latencies) if latencies else 0.0

            return {
                "available": True,
                "total_requests": len(requests),
                "hits": hits,
                "misses": misses,
                "hit_rate_pct": round(hit_rate, 2),
                "evictions": evictions,
                "latency": {
                    "avg_ms": round(avg_lat, 3),
                    "min_ms": round(sorted_lats[0], 3) if sorted_lats else 0.0,
                    "max_ms": round(sorted_lats[-1], 3) if sorted_lats else 0.0,
                    "p95_ms": round(p95_lat, 3),
                }
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e),
                "message": f"Redis execution error: {str(e)}",
                "total_requests": len(requests)
            }
