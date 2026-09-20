"""
Unit tests for CacheNode lifecycle, metrics, and failure handling.
"""

import pytest
from core.cache_node import CacheNode


def test_cache_node_unsupported_policy():
    with pytest.raises(ValueError):
        CacheNode("node-err", capacity=10, policy="fifo")


def test_cache_node_metrics_calculation():
    node = CacheNode("node-1", capacity=3, policy="lru")
    assert node.is_active

    # Insert 3 items (fills capacity)
    node.set("k1", "v1")
    node.set("k2", "v2")
    node.set("k3", "v3")
    assert node.sets == 3
    assert node.evictions == 0

    # Eviction on 4th item
    node.set("k4", "v4")
    assert node.evictions == 1
    assert node.size == 3

    # Hits and misses
    assert node.get("k4") == "v4"  # hit
    assert node.get("k1") is None    # miss (was evicted)
    assert node.hits == 1
    assert node.misses == 1

    stats = node.stats()
    assert stats["node_id"] == "node-1"
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["hit_rate_pct"] == 50.0
    assert stats["miss_rate_pct"] == 50.0
    assert stats["evictions"] == 1
    assert stats["utilization_pct"] == 100.0


def test_cache_node_failure_and_recovery():
    node = CacheNode("node-1", capacity=5, policy="lru")
    node.set("k1", "v1")

    # Node fails
    node.fail()
    assert not node.is_active
    assert node.status == "failed"

    # Gets and Sets on failed node fail gracefully
    assert node.get("k1") is None
    assert node.set("k2", "v2") is False
    assert node.delete("k1") is False

    # Node recovers
    node.recover()
    assert node.is_active
    assert node.status == "active"
    assert node.get("k1") == "v1"


def test_cache_node_reset_metrics():
    node = CacheNode("node-1", capacity=5, policy="lru")
    node.set("k1", "v1")
    node.get("k1")
    node.get("missing")
    assert node.hits == 1
    assert node.misses == 1

    node.reset_metrics()
    assert node.hits == 0
    assert node.misses == 0
    assert node.gets == 0
    assert node.size == 1  # data retained
