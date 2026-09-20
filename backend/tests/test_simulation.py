"""
Unit tests for SimulatedDatabase, MetricsCollector, and SimulationEngine.
"""

from simulator.db import SimulatedDatabase
from simulator.metrics import MetricsCollector
from simulator.engine import SimulationEngine
from distributed.cluster import CacheCluster


def test_simulated_database():
    db = SimulatedDatabase(base_read_latency_ms=15.0, base_write_latency_ms=20.0)
    assert db.size() == 0

    val, lat = db.read("user:101")
    assert val == "db_val_user:101"
    assert lat >= 5.0
    assert db.size() == 1
    assert db.queries_count == 1

    write_lat = db.write("user:101", "custom_val")
    assert write_lat >= 5.0
    assert db.writes_count == 1

    val2, _ = db.read("user:101")
    assert val2 == "custom_val"


def test_metrics_collector():
    collector = MetricsCollector()
    collector.record_request(op="GET", hit=True, latency_ms=1.0, node_id="node_0")
    collector.record_request(op="GET", hit=False, latency_ms=20.0, node_id="node_1", db_read=True)
    collector.record_request(op="SET", hit=False, latency_ms=18.0, node_id="node_0", db_write=True)

    summary = collector.summary()
    assert summary["total_requests"] == 3
    assert summary["hits"] == 1
    assert summary["misses"] == 1
    assert summary["hit_rate_pct"] == 50.0
    assert summary["miss_rate_pct"] == 50.0
    assert summary["db_reads"] == 1
    assert summary["db_writes"] == 1
    assert summary["latency"]["p50_ms"] == 18.0
    assert summary["latency"]["avg_ms"] == 13.0


def test_simulation_engine_execution():
    cluster = CacheCluster(num_nodes=3, capacity_per_node=50, policy="lru")
    engine = SimulationEngine(cluster=cluster)

    # 1. First GET to key "prod:1" will miss (DB fetch) and cache it
    req1 = [("GET", "prod:1", None)]
    res1 = engine.run_simulation(req1)
    assert res1["hits"] == 0
    assert res1["misses"] == 1
    assert res1["db_reads"] == 1

    # 2. Second GET to key "prod:1" must be a CACHE HIT
    req2 = [("GET", "prod:1", None)]
    res2 = engine.run_simulation(req2)
    assert res2["hits"] == 1
    assert res2["misses"] == 0
    assert res2["db_reads"] == 0
    assert res2["latency"]["avg_ms"] < 5.0  # Fast in-memory hit
