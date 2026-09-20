"""
Unit tests for CacheCluster, multi-node request routing, and failover behavior.
"""

from distributed.cluster import CacheCluster


def test_cluster_initialization():
    cluster = CacheCluster(num_nodes=3, capacity_per_node=50, policy="lru", vnodes=100)
    assert cluster.node_count == 3
    assert len(cluster.healthy_nodes) == 3
    assert len(cluster.failed_nodes) == 0

    stats = cluster.stats()
    summary = stats["cluster_summary"]
    assert summary["total_nodes"] == 3
    assert summary["healthy_nodes"] == 3
    assert summary["total_capacity"] == 150
    assert summary["total_keys_stored"] == 0


def test_cluster_get_set_routing():
    cluster = CacheCluster(num_nodes=3, capacity_per_node=10, policy="lru", vnodes=50)

    # Store multiple keys
    res1 = cluster.set("product:101", {"name": "Laptop", "price": 1200})
    res2 = cluster.set("product:102", {"name": "Mouse", "price": 25})

    assert res1["success"] is True
    assert res1["node_id"] in cluster.healthy_nodes
    assert res2["success"] is True
    assert res2["node_id"] in cluster.healthy_nodes

    # Lookup
    get1 = cluster.get("product:101")
    assert get1["found"] is True
    assert get1["value"]["name"] == "Laptop"
    assert get1["node_id"] == res1["node_id"]

    get_missing = cluster.get("non_existent_key")
    assert get_missing["found"] is False
    assert get_missing["value"] is None


def test_cluster_node_failure_and_failover():
    cluster = CacheCluster(num_nodes=3, capacity_per_node=10, policy="lru", vnodes=100)

    # Populate a key and determine its owner
    key = "user:404"
    set_res = cluster.set(key, "data_payload")
    initial_owner = set_res["node_id"]

    # Verify lookup succeeds on initial owner
    get_res = cluster.get(key)
    assert get_res["found"] is True
    assert get_res["node_id"] == initial_owner

    # Fail the owner node
    cluster.fail_node(initial_owner)
    assert initial_owner in cluster.failed_nodes
    assert initial_owner not in cluster.healthy_nodes

    # Subsequent lookup for the same key must route to healthy successor (clockwise failover)
    failover_get = cluster.get(key)
    # The successor does not have this key yet -> cache miss
    assert failover_get["found"] is False
    assert failover_get["node_id"] != initial_owner
    assert failover_get["node_id"] in cluster.healthy_nodes

    # Recover the node
    cluster.recover_node(initial_owner)
    assert initial_owner in cluster.healthy_nodes
    # Now key routes back to the recovered node, which still has the data in its memory!
    recovered_get = cluster.get(key)
    assert recovered_get["found"] is True
    assert recovered_get["node_id"] == initial_owner


def test_cluster_stats_aggregation():
    cluster = CacheCluster(num_nodes=3, capacity_per_node=2, policy="lru")

    # Insert items to trigger evictions
    for i in range(10):
        cluster.set(f"k_{i}", f"val_{i}")

    stats = cluster.stats()
    summary = stats["cluster_summary"]
    assert summary["total_sets"] == 10
    # Total stored keys cannot exceed total capacity 6 (3 nodes * 2)
    assert summary["total_keys_stored"] <= 6
    assert summary["total_evictions"] >= 4
