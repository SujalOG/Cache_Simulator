"""
Simulation Engine coordinating CacheCluster, SimulatedDatabase, and Metrics.
Executes workloads using the hybrid deterministic latency model.
Supports node failure injection during active simulation runs.
"""

import random
from typing import Dict, List, Optional, Tuple, Any
from distributed.cluster import CacheCluster
from simulator.db import SimulatedDatabase
from simulator.metrics import MetricsCollector
from simulator.workload import WorkloadGenerator


class SimulationEngine:
    """
    Orchestrates workloads, cluster routing, simulated DB queries, and metrics.
    """

    def __init__(
        self,
        cluster: Optional[CacheCluster] = None,
        database: Optional[SimulatedDatabase] = None,
        cache_hit_latency_mean: float = 0.8,
        cache_hit_latency_std: float = 0.15,
    ) -> None:
        self.cluster: CacheCluster = cluster if cluster is not None else CacheCluster()
        self.db: SimulatedDatabase = database if database is not None else SimulatedDatabase()
        self.cache_hit_latency_mean = cache_hit_latency_mean
        self.cache_hit_latency_std = cache_hit_latency_std

    def _sample_cache_latency(self) -> float:
        """Sample cache lookup overhead in milliseconds."""
        sampled = random.gauss(self.cache_hit_latency_mean, self.cache_hit_latency_std)
        return round(max(0.2, sampled), 3)

    def execute_request(
        self,
        op: str,
        key: str,
        value: Optional[Any],
        ttl: Optional[float] = None,
        current_time: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Execute a single cache request according to cache-aside architecture:
        - GET:
          1. Check Cache Cluster.
          2. On Hit: return value immediately with low latency (~0.8ms).
          3. On Miss: fetch from SimulatedDatabase (~20ms), store in Cache Cluster, return value.
        - SET:
          1. Write to SimulatedDatabase.
          2. Store in Cache Cluster.
        """
        op = op.upper()
        cache_lat = self._sample_cache_latency()

        if op == "GET":
            get_res = self.cluster.get(key, current_time=current_time)
            hit = get_res["found"]
            node_id = get_res["node_id"]

            if hit:
                # CACHE HIT
                total_latency = cache_lat
                return {
                    "op": op,
                    "key": key,
                    "hit": True,
                    "value": get_res["value"],
                    "node_id": node_id,
                    "latency_ms": total_latency,
                    "evicted": False,
                    "expired": False,
                    "db_read": False,
                    "db_write": False,
                }
            else:
                # CACHE MISS -> Fetch from DB
                db_val, db_lat = self.db.read(key)
                total_latency = round(cache_lat + db_lat, 3)

                # Store back in cache cluster
                set_res = self.cluster.set(key, db_val, ttl=ttl, current_time=current_time)
                # Check if this caused an eviction on the target node
                target_node = self.cluster.nodes.get(node_id) if node_id else None
                was_eviction = bool(target_node and target_node.evictions > 0)

                return {
                    "op": op,
                    "key": key,
                    "hit": False,
                    "value": db_val,
                    "node_id": node_id,
                    "latency_ms": total_latency,
                    "evicted": was_eviction,
                    "expired": False,
                    "db_read": True,
                    "db_write": False,
                }

        elif op == "SET":
            # WRITE -> Write to DB, then cache
            val_to_write = value if value is not None else f"stored_val_{key}"
            db_lat = self.db.write(key, val_to_write)
            total_latency = round(cache_lat + db_lat, 3)

            set_res = self.cluster.set(key, val_to_write, ttl=ttl, current_time=current_time)
            node_id = set_res["node_id"]

            return {
                "op": op,
                "key": key,
                "hit": False,
                "value": val_to_write,
                "node_id": node_id,
                "latency_ms": total_latency,
                "evicted": False,
                "expired": False,
                "db_read": False,
                "db_write": True,
            }

        else:
            raise ValueError(f"Unsupported operation: {op}")

    def run_simulation(
        self,
        requests: List[Tuple[str, str, Optional[Any]]],
        ttl: Optional[float] = None,
        fail_node_at_step: Optional[int] = None,
        target_failed_node: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute an entire workload stream and collect comprehensive metrics.
        Supports dynamic node failure injection at step `fail_node_at_step`.
        """
        collector = MetricsCollector()
        node_failed = False

        for step, (op, key, value) in enumerate(requests):
            # Inject node failure if configured
            if (
                fail_node_at_step is not None
                and step == fail_node_at_step
                and not node_failed
            ):
                fail_id = (
                    target_failed_node
                    if target_failed_node
                    else sorted(list(self.cluster.healthy_nodes))[0]
                )
                self.cluster.fail_node(fail_id)
                node_failed = True

            req_outcome = self.execute_request(op=op, key=key, value=value, ttl=ttl)

            collector.record_request(
                op=req_outcome["op"],
                hit=req_outcome["hit"],
                latency_ms=req_outcome["latency_ms"],
                node_id=req_outcome["node_id"],
                evicted=req_outcome["evicted"],
                expired=req_outcome["expired"],
                db_read=req_outcome["db_read"],
                db_write=req_outcome["db_write"],
            )

        summary = collector.summary()
        summary["cluster_state"] = self.cluster.stats()
        return summary
