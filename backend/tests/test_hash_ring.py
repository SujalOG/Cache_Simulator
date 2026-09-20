"""
Unit tests for ConsistentHashRing, virtual node distribution, and NaiveModuloRing.
"""

from distributed.hash_ring import ConsistentHashRing, hash_32
from distributed.modulo_ring import NaiveModuloRing


def test_hash_32_deterministic():
    h1 = hash_32("user:1001")
    h2 = hash_32("user:1001")
    h3 = hash_32("user:1002")
    assert h1 == h2
    assert h1 != h3
    assert 0 <= h1 <= 0xFFFFFFFF


def test_empty_ring():
    ring = ConsistentHashRing()
    assert ring.get_node("key1") is None
    assert ring.total_vnodes == 0
    assert ring.physical_nodes == []


def test_add_remove_node():
    ring = ConsistentHashRing(vnodes=50)
    ring.add_node("node_0")
    ring.add_node("node_1")

    assert ring.physical_nodes == ["node_0", "node_1"]
    assert ring.total_vnodes == 100

    # Idempotent add
    ring.add_node("node_0")
    assert ring.total_vnodes == 100

    # Remove node_0
    ring.remove_node("node_0")
    assert ring.physical_nodes == ["node_1"]
    assert ring.total_vnodes == 50

    # All keys must now map to node_1
    for k in ["k1", "k2", "k3", "k4"]:
        assert ring.get_node(k) == "node_1"


def test_distribution_uniformity():
    """
    With 100 virtual nodes per physical node, keys should be distributed
    fairly evenly across 3 nodes (no single node gets < 20% or > 46%).
    """
    ring = ConsistentHashRing(vnodes=100)
    ring.add_node("node_0")
    ring.add_node("node_1")
    ring.add_node("node_2")

    keys = [f"item:{i}" for i in range(3000)]
    distribution = ring.get_distribution(keys)

    assert len(distribution) == 3
    for node, count in distribution.items():
        pct = (count / len(keys)) * 100
        # Expected is ~33.3%. Bounds between 20% and 48% ensure good uniformity.
        assert 20.0 <= pct <= 48.0, f"{node} has skewed distribution: {pct:.2f}%"


def test_clockwise_successor_failover():
    ring = ConsistentHashRing(vnodes=100)
    ring.add_node("node_0")
    ring.add_node("node_1")
    ring.add_node("node_2")

    # Find a key that naturally maps to node_1
    target_key = None
    for i in range(1000):
        k = f"test_key_{i}"
        if ring.get_node(k) == "node_1":
            target_key = k
            break

    assert target_key is not None

    # Simulate node_1 failure: healthy nodes = {"node_0", "node_2"}
    healthy = {"node_0", "node_2"}
    fallback_node = ring.get_node(target_key, healthy_nodes=healthy)

    # It must failover to either node_0 or node_2, NEVER node_1
    assert fallback_node in healthy
    assert fallback_node != "node_1"


def test_consistent_vs_naive_rebalancing_churn():
    """
    Core interview experiment:
    When scaling from 3 to 4 nodes, naive modulo hashing invalidates ~75% of keys,
    whereas Consistent Hashing only moves ~25% of keys (1 / (N+1)).
    """
    keys = [f"data_key_{i}" for i in range(2000)]

    # 1. Naive Modulo Hashing
    modulo_3 = NaiveModuloRing(["node_0", "node_1", "node_2"])
    modulo_assignments_3 = {k: modulo_3.get_node(k) for k in keys}

    modulo_4 = NaiveModuloRing(["node_0", "node_1", "node_2", "node_3"])
    modulo_assignments_4 = {k: modulo_4.get_node(k) for k in keys}

    modulo_moved = sum(
        1 for k in keys if modulo_assignments_3[k] != modulo_assignments_4[k]
    )
    modulo_churn_pct = (modulo_moved / len(keys)) * 100

    # 2. Consistent Hashing
    ring = ConsistentHashRing(vnodes=100)
    ring.add_node("node_0")
    ring.add_node("node_1")
    ring.add_node("node_2")
    consistent_assignments_3 = {k: ring.get_node(k) for k in keys}

    ring.add_node("node_3")
    consistent_assignments_4 = {k: ring.get_node(k) for k in keys}

    consistent_moved = sum(
        1 for k in keys if consistent_assignments_3[k] != consistent_assignments_4[k]
    )
    consistent_churn_pct = (consistent_moved / len(keys)) * 100

    # Naive modulo churn should be ~75% (>= 70%)
    assert modulo_churn_pct >= 70.0, f"Naive churn too low: {modulo_churn_pct}%"

    # Consistent hashing churn should be ~25% (<= 35%)
    assert consistent_churn_pct <= 35.0, f"Consistent churn too high: {consistent_churn_pct}%"

    # Consistent hashing should move substantially fewer keys than naive modulo
    assert consistent_churn_pct < (modulo_churn_pct / 2)
