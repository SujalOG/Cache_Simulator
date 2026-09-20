"""
Flask REST API for Distributed Cache Simulator.
Exposes endpoints to configure and run ad-hoc simulations, execute the 6 canonical
system design benchmark experiments, and check system/Redis health.
"""

import os
from typing import Any, Dict
from flask import Flask, request, jsonify
from flask_cors import CORS

from distributed.cluster import CacheCluster
from simulator.engine import SimulationEngine
from simulator.workload import WorkloadGenerator
from simulator.experiments import ExperimentSuite
from simulator.redis_client import RedisBenchmarkRunner

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing for React dashboard

redis_runner = RedisBenchmarkRunner()


@app.route("/api/health", methods=["GET"])
def health_check():
    """System health check and Redis connectivity inspection."""
    is_redis_up = redis_runner.is_available()
    return jsonify({
        "status": "healthy",
        "service": "Distributed Cache Simulator API",
        "version": "1.0.0",
        "redis_connected": is_redis_up,
        "redis_host": f"{redis_runner.host}:{redis_runner.port}"
    }), 200


@app.route("/api/simulate", methods=["POST"])
def simulate():
    """
    Run an ad-hoc custom cache simulation.
    Accepts custom parameters:
    - policy: 'lru' | 'lfu' (default 'lru')
    - nodes: int (1 to 10, default 3)
    - capacity_per_node: int (default 500)
    - vnodes: int (default 100)
    - requests: int (default 10000)
    - unique_keys: int (default 1000)
    - workload_pattern: 'hot_keys' | 'random' | 'sequential' (default 'hot_keys')
    - read_ratio: float (default 0.8)
    - zipf_alpha: float (default 0.99)
    - ttl: float | None (default None)
    - failed_node_id: str | None (default None)
    - fail_at_request: int | None (default None)
    """
    data = request.get_json(silent=True) or {}

    try:
        policy = str(data.get("policy", "lru")).lower()
        if policy not in ("lru", "lfu"):
            return jsonify({"error": "policy must be 'lru' or 'lfu'"}), 400

        num_nodes = int(data.get("nodes", 3))
        if not (1 <= num_nodes <= 10):
            return jsonify({"error": "nodes must be between 1 and 10"}), 400

        capacity_per_node = int(data.get("capacity_per_node", 500))
        if capacity_per_node <= 0:
            return jsonify({"error": "capacity_per_node must be positive"}), 400

        vnodes = int(data.get("vnodes", 100))
        if vnodes <= 0:
            return jsonify({"error": "vnodes must be positive"}), 400

        num_requests = int(data.get("requests", 10000))
        if not (1 <= num_requests <= 100000):
            return jsonify({"error": "requests must be between 1 and 100,000"}), 400

        num_keys = int(data.get("unique_keys", 1000))
        if num_keys <= 0:
            return jsonify({"error": "unique_keys must be positive"}), 400

        workload_pattern = str(data.get("workload_pattern", "hot_keys")).lower()
        if workload_pattern not in WorkloadGenerator.SUPPORTED_PATTERNS:
            return jsonify({
                "error": f"workload_pattern must be one of {WorkloadGenerator.SUPPORTED_PATTERNS}"
            }), 400

        read_ratio = float(data.get("read_ratio", 0.8))
        if not (0.0 <= read_ratio <= 1.0):
            return jsonify({"error": "read_ratio must be between 0.0 and 1.0"}), 400

        zipf_alpha = float(data.get("zipf_alpha", 0.99))
        ttl = float(data["ttl"]) if data.get("ttl") is not None else None

        failed_node_id = data.get("failed_node_id")
        fail_at_request = int(data["fail_at_request"]) if data.get("fail_at_request") is not None else None

        # Build cluster and engine
        cluster = CacheCluster(
            num_nodes=num_nodes,
            capacity_per_node=capacity_per_node,
            policy=policy,
            vnodes=vnodes
        )
        engine = SimulationEngine(cluster=cluster)

        # Generate workload
        workload = WorkloadGenerator.generate(
            pattern=workload_pattern,
            num_requests=num_requests,
            num_unique_keys=num_keys,
            read_ratio=read_ratio,
            zipf_alpha=zipf_alpha
        )

        # Execute simulation
        results = engine.run_simulation(
            requests=workload,
            ttl=ttl,
            fail_node_at_step=fail_at_request,
            target_failed_node=failed_node_id
        )

        results["simulation_config"] = {
            "policy": policy,
            "num_nodes": num_nodes,
            "capacity_per_node": capacity_per_node,
            "vnodes": vnodes,
            "requests": num_requests,
            "unique_keys": num_keys,
            "workload_pattern": workload_pattern,
            "read_ratio": read_ratio,
            "zipf_alpha": zipf_alpha,
            "ttl": ttl,
            "failed_node_id": failed_node_id,
            "fail_at_request": fail_at_request,
        }

        return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


EXPERIMENTS_METADATA = [
    {
        "id": "lru_vs_lfu",
        "name": "Experiment 1: LRU vs LFU",
        "description": "Compares hit rates, latency, and evictions between LRU and LFU under identical skewed workloads.",
    },
    {
        "id": "workload_patterns",
        "name": "Experiment 2: Workload Access Patterns",
        "description": "Analyzes how Hot-Keys (Zipfian), Random (Uniform), and Sequential scanning affect cache performance.",
    },
    {
        "id": "node_scaling",
        "name": "Experiment 3: Cluster Node Scaling",
        "description": "Measures capacity growth, hit rates, and load distribution as nodes scale horizontally from 1 to 4.",
    },
    {
        "id": "consistent_vs_modulo",
        "name": "Experiment 4: Consistent Hashing vs Naive Modulo",
        "description": "Measures cache invalidation churn when adding nodes to prove why consistent hashing prevents cache stampedes.",
    },
    {
        "id": "node_failure",
        "name": "Experiment 5: Node Crash & Successor Failover",
        "description": "Simulates a node failure midway through execution to observe clockwise successor rerouting and DB cold misses.",
    },
    {
        "id": "simulator_vs_redis",
        "name": "Experiment 6: Simulator vs Production Redis",
        "description": "Direct side-by-side benchmarking of our custom Python cache engine against a real-world Redis server.",
    },
]


@app.route("/api/experiments/list", methods=["GET"])
def list_experiments():
    """List all available canonical benchmark experiments."""
    return jsonify({"experiments": EXPERIMENTS_METADATA}), 200


@app.route("/api/experiments/run", methods=["POST"])
def run_experiment():
    """
    Run one of the 6 canonical system design experiments.
    Body: {"experiment_id": "...", "params": {...}}
    """
    data = request.get_json(silent=True) or {}
    exp_id = data.get("experiment_id")
    params = data.get("params") or {}

    if not exp_id:
        return jsonify({"error": "Missing 'experiment_id' parameter"}), 400

    try:
        if exp_id == "lru_vs_lfu":
            res = ExperimentSuite.experiment_1_lru_vs_lfu(
                num_requests=int(params.get("requests", 10000)),
                num_keys=int(params.get("keys", 1500)),
                capacity_per_node=int(params.get("capacity", 150)),
                pattern=str(params.get("pattern", "hot_keys"))
            )
        elif exp_id == "workload_patterns":
            res = ExperimentSuite.experiment_2_workload_patterns(
                num_requests=int(params.get("requests", 10000)),
                num_keys=int(params.get("keys", 1500)),
                capacity_per_node=int(params.get("capacity", 150))
            )
        elif exp_id == "node_scaling":
            res = ExperimentSuite.experiment_3_node_scaling(
                nodes_list=params.get("nodes", [1, 2, 3, 4]),
                num_requests=int(params.get("requests", 10000)),
                num_keys=int(params.get("keys", 2500)),
                capacity_per_node=int(params.get("capacity", 200))
            )
        elif exp_id == "consistent_vs_modulo":
            res = ExperimentSuite.experiment_4_consistent_vs_modulo(
                num_keys=int(params.get("keys", 5000)),
                initial_nodes=int(params.get("initial_nodes", 3)),
                final_nodes=int(params.get("final_nodes", 4))
            )
        elif exp_id == "node_failure":
            res = ExperimentSuite.experiment_5_node_failure(
                num_requests=int(params.get("requests", 10000)),
                num_keys=int(params.get("keys", 1500)),
                capacity_per_node=int(params.get("capacity", 200))
            )
        elif exp_id == "simulator_vs_redis":
            res = ExperimentSuite.experiment_6_simulator_vs_redis(
                num_requests=int(params.get("requests", 5000)),
                num_keys=int(params.get("keys", 1000)),
                capacity=int(params.get("capacity", 200))
            )
        else:
            return jsonify({
                "error": f"Unknown experiment_id '{exp_id}'. Must be one of {[e['id'] for e in EXPERIMENTS_METADATA]}"
            }), 404

        return jsonify(res), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
