"""
Suite of 6 Canonical Distributed Caching Experiments.
Each experiment provides structured comparative telemetry alongside
in-depth system design interview insights.
"""

from typing import Dict, Any, List
from distributed.cluster import CacheCluster
from distributed.hash_ring import ConsistentHashRing
from distributed.modulo_ring import NaiveModuloRing
from simulator.engine import SimulationEngine
from simulator.workload import WorkloadGenerator
from simulator.redis_client import RedisBenchmarkRunner


class ExperimentSuite:
    """
    Runner for the 6 canonical system design caching experiments.
    """

    @staticmethod
    def experiment_1_lru_vs_lfu(
        num_requests: int = 10000,
        num_keys: int = 1500,
        capacity_per_node: int = 150,
        pattern: str = "hot_keys"
    ) -> Dict[str, Any]:
        """
        Experiment 1: LRU vs LFU under identical workload.
        """
        requests = WorkloadGenerator.generate(
            pattern=pattern,
            num_requests=num_requests,
            num_unique_keys=num_keys,
            read_ratio=0.85
        )

        # 1. Run with LRU
        cluster_lru = CacheCluster(num_nodes=3, capacity_per_node=capacity_per_node, policy="lru")
        engine_lru = SimulationEngine(cluster=cluster_lru)
        metrics_lru = engine_lru.run_simulation(requests)

        # 2. Run with LFU
        cluster_lfu = CacheCluster(num_nodes=3, capacity_per_node=capacity_per_node, policy="lfu")
        engine_lfu = SimulationEngine(cluster=cluster_lfu)
        metrics_lfu = engine_lfu.run_simulation(requests)

        insights = (
            "Under skewed/hot-key workloads (Zipfian), LFU generally outperforms LRU by preserving "
            "frequently accessed keys even if they experience temporary pauses in traffic. "
            "However, LFU suffers from 'cache pollution' when previously hot keys lose popularity, "
            "as their high frequency counts make them difficult to evict. LRU adapts faster to working set shifts."
        )

        return {
            "experiment_id": "lru_vs_lfu",
            "name": "LRU vs LFU Eviction Performance",
            "workload": {"requests": num_requests, "unique_keys": num_keys, "pattern": pattern},
            "lru": {
                "hit_rate_pct": metrics_lru["hit_rate_pct"],
                "miss_rate_pct": metrics_lru["miss_rate_pct"],
                "evictions": metrics_lru["evictions"],
                "avg_latency_ms": metrics_lru["latency"]["avg_ms"],
                "p95_latency_ms": metrics_lru["latency"]["p95_ms"],
            },
            "lfu": {
                "hit_rate_pct": metrics_lfu["hit_rate_pct"],
                "miss_rate_pct": metrics_lfu["miss_rate_pct"],
                "evictions": metrics_lfu["evictions"],
                "avg_latency_ms": metrics_lfu["latency"]["avg_ms"],
                "p95_latency_ms": metrics_lfu["latency"]["p95_ms"],
            },
            "interview_insights": insights
        }

    @staticmethod
    def experiment_2_workload_patterns(
        num_requests: int = 10000,
        num_keys: int = 1500,
        capacity_per_node: int = 150
    ) -> Dict[str, Any]:
        """
        Experiment 2: Access Pattern Comparison (Random vs Hot-Keys vs Sequential).
        """
        results = {}
        patterns = ["hot_keys", "random", "sequential"]

        for pat in patterns:
            reqs = WorkloadGenerator.generate(
                pattern=pat,
                num_requests=num_requests,
                num_unique_keys=num_keys,
                read_ratio=0.85
            )
            cluster = CacheCluster(num_nodes=3, capacity_per_node=capacity_per_node, policy="lru")
            engine = SimulationEngine(cluster=cluster)
            m = engine.run_simulation(reqs)
            results[pat] = {
                "hit_rate_pct": m["hit_rate_pct"],
                "miss_rate_pct": m["miss_rate_pct"],
                "evictions": m["evictions"],
                "avg_latency_ms": m["latency"]["avg_ms"],
                "p95_latency_ms": m["latency"]["p95_ms"],
            }

        insights = (
            "Cache efficacy heavily depends on temporal and spatial locality. "
            "Hot-Key workloads (Zipfian) exhibit high hit rates because a small subset of keys receives the vast majority of traffic. "
            "Uniform Random workloads degrade hit rates to roughly (Capacity / Unique Keys). "
            "Sequential scans cause severe cache thrashing, completely flushing hot data out of cache."
        )

        return {
            "experiment_id": "workload_patterns",
            "name": "Access Pattern Comparison (Locality vs Thrashing)",
            "patterns": results,
            "interview_insights": insights
        }

    @staticmethod
    def experiment_3_node_scaling(
        nodes_list: List[int] = None,
        num_requests: int = 10000,
        num_keys: int = 2500,
        capacity_per_node: int = 200
    ) -> Dict[str, Any]:
        """
        Experiment 3: Scaling cluster nodes (1, 2, 3, 4 nodes).
        """
        nodes_to_test = nodes_list or [1, 2, 3, 4]
        scaling_results = []

        requests = WorkloadGenerator.generate(
            pattern="hot_keys",
            num_requests=num_requests,
            num_unique_keys=num_keys,
            read_ratio=0.85
        )

        for n_nodes in nodes_to_test:
            cluster = CacheCluster(num_nodes=n_nodes, capacity_per_node=capacity_per_node, policy="lru")
            engine = SimulationEngine(cluster=cluster)
            m = engine.run_simulation(requests)
            scaling_results.append({
                "nodes": n_nodes,
                "total_capacity": n_nodes * capacity_per_node,
                "hit_rate_pct": m["hit_rate_pct"],
                "evictions": m["evictions"],
                "avg_latency_ms": m["latency"]["avg_ms"],
                "p95_latency_ms": m["latency"]["p95_ms"],
                "load_std_dev": m["load_std_dev"]
            })

        insights = (
            "Horizontal scaling expands total cluster capacity, allowing a larger working set "
            "to fit in memory and diminishing evictions. Consistent hashing distributes traffic evenly "
            "across nodes, reducing memory pressure on individual instances."
        )

        return {
            "experiment_id": "node_scaling",
            "name": "Horizontal Cluster Scaling (1 to 4 Nodes)",
            "scaling": scaling_results,
            "interview_insights": insights
        }

    @staticmethod
    def experiment_4_consistent_vs_modulo(
        num_keys: int = 5000,
        initial_nodes: int = 3,
        final_nodes: int = 4
    ) -> Dict[str, Any]:
        """
        Experiment 4: Rebalancing Churn: Consistent Hashing vs Naive Modulo.
        """
        keys = [f"entity:{i}" for i in range(num_keys)]

        # 1. Naive Modulo
        modulo_init = NaiveModuloRing([f"node_{i}" for i in range(initial_nodes)])
        mod_assign_1 = {k: modulo_init.get_node(k) for k in keys}

        modulo_scaled = NaiveModuloRing([f"node_{i}" for i in range(final_nodes)])
        mod_assign_2 = {k: modulo_scaled.get_node(k) for k in keys}

        mod_moved = sum(1 for k in keys if mod_assign_1[k] != mod_assign_2[k])
        mod_churn_pct = round((mod_moved / num_keys) * 100, 2)

        # 2. Consistent Hashing
        ring = ConsistentHashRing(vnodes=100)
        for i in range(initial_nodes):
            ring.add_node(f"node_{i}")
        ch_assign_1 = {k: ring.get_node(k) for k in keys}

        for i in range(initial_nodes, final_nodes):
            ring.add_node(f"node_{i}")
        ch_assign_2 = {k: ring.get_node(k) for k in keys}

        ch_moved = sum(1 for k in keys if ch_assign_1[k] != ch_assign_2[k])
        ch_churn_pct = round((ch_moved / num_keys) * 100, 2)

        insights = (
            f"When scaling from {initial_nodes} to {final_nodes} nodes: "
            f"Naive modulo invalidates {mod_churn_pct}% of keys (~(N-1)/N), causing catastrophic "
            f"cache stampedes and overwhelming the backing database. "
            f"Consistent Hashing only relocates {ch_churn_pct}% of keys (~1/(N+1)), keeping the vast "
            f"majority of the cache intact."
        )

        return {
            "experiment_id": "consistent_vs_modulo",
            "name": "Key Rebalancing Churn on Cluster Scale-Out",
            "keys_tested": num_keys,
            "initial_nodes": initial_nodes,
            "final_nodes": final_nodes,
            "naive_modulo": {
                "keys_moved": mod_moved,
                "churn_pct": mod_churn_pct,
            },
            "consistent_hashing": {
                "keys_moved": ch_moved,
                "churn_pct": ch_churn_pct,
            },
            "interview_insights": insights
        }

    @staticmethod
    def experiment_5_node_failure(
        num_requests: int = 10000,
        num_keys: int = 1500,
        capacity_per_node: int = 200
    ) -> Dict[str, Any]:
        """
        Experiment 5: Node Crash Simulation & Clockwise Successor Failover.
        """
        cluster = CacheCluster(num_nodes=3, capacity_per_node=capacity_per_node, policy="lru")
        engine = SimulationEngine(cluster=cluster)

        requests = WorkloadGenerator.generate(
            pattern="hot_keys",
            num_requests=num_requests,
            num_unique_keys=num_keys,
            read_ratio=0.85
        )

        # Baseline run with all 3 nodes healthy
        metrics_healthy = engine.run_simulation(requests)

        # Failure run: node_1 crashes midway at request 5,000
        cluster_with_failure = CacheCluster(num_nodes=3, capacity_per_node=capacity_per_node, policy="lru")
        engine_with_failure = SimulationEngine(cluster=cluster_with_failure)
        metrics_failed = engine_with_failure.run_simulation(
            requests,
            fail_node_at_step=num_requests // 2,
            target_failed_node="node_1"
        )

        insights = (
            "When a node fails, clockwise successor routing redirects its traffic to healthy nodes. "
            "Because the successor node initially lacks those keys, a sudden burst of cold cache misses occurs, "
            "surging traffic to the simulated database before stabilizing as the successor re-populates."
        )

        return {
            "experiment_id": "node_failure",
            "name": "Node Failure & Clockwise Failover Cascades",
            "healthy_cluster": {
                "hit_rate_pct": metrics_healthy["hit_rate_pct"],
                "avg_latency_ms": metrics_healthy["latency"]["avg_ms"],
                "p95_latency_ms": metrics_healthy["latency"]["p95_ms"],
                "db_reads": metrics_healthy["db_reads"],
            },
            "failed_cluster": {
                "failed_node": "node_1",
                "failure_point_request": num_requests // 2,
                "hit_rate_pct": metrics_failed["hit_rate_pct"],
                "avg_latency_ms": metrics_failed["latency"]["avg_ms"],
                "p95_latency_ms": metrics_failed["latency"]["p95_ms"],
                "db_reads": metrics_failed["db_reads"],
                "node_distribution": metrics_failed["node_distribution"],
            },
            "interview_insights": insights
        }

    @staticmethod
    def experiment_6_simulator_vs_redis(
        num_requests: int = 5000,
        num_keys: int = 1000,
        capacity: int = 200
    ) -> Dict[str, Any]:
        """
        Experiment 6: Simulator vs Real Redis baseline comparison.
        """
        requests = WorkloadGenerator.generate(
            pattern="hot_keys",
            num_requests=num_requests,
            num_unique_keys=num_keys,
            read_ratio=0.85
        )

        # Simulator run
        cluster = CacheCluster(num_nodes=3, capacity_per_node=capacity // 3 + 1, policy="lru")
        engine = SimulationEngine(cluster=cluster)
        sim_metrics = engine.run_simulation(requests)

        # Real Redis run
        runner = RedisBenchmarkRunner()
        redis_metrics = runner.run_workload(requests, policy="allkeys-lru")

        insights = (
            "This experiment juxtaposes our custom pure-Python implementation against production Redis. "
            "Redis is implemented in C with event loops (ae.c) and direct network socket I/O. "
            "The comparison highlights algorithmic parity (eviction trends and hit rates) "
            "while illustrating real-world networking socket latency differences."
        )

        return {
            "experiment_id": "simulator_vs_redis",
            "name": "Simulator vs Production Redis Baseline",
            "simulator": {
                "hit_rate_pct": sim_metrics["hit_rate_pct"],
                "evictions": sim_metrics["evictions"],
                "avg_latency_ms": sim_metrics["latency"]["avg_ms"],
                "p95_latency_ms": sim_metrics["latency"]["p95_ms"],
            },
            "redis": redis_metrics,
            "interview_insights": insights
        }
