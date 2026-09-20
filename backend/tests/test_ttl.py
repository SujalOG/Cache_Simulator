"""
Unit tests for TTL (Time-To-Live) expiration and lazy eviction.
"""

from core.cache_node import CacheNode


def test_ttl_hit_before_expiry():
    node = CacheNode("node-1", capacity=10, policy="lru")
    # Store key with 10s TTL at simulated virtual timestamp 1000.0
    node.set("session:user1", "auth_token_xyz", ttl=10.0, current_time=1000.0)

    # Lookup at 1005.0s (within TTL)
    val = node.get("session:user1", current_time=1005.0)
    assert val == "auth_token_xyz"
    assert node.hits == 1
    assert node.misses == 0
    assert node.expired == 0


def test_ttl_miss_and_lazy_eviction_after_expiry():
    node = CacheNode("node-1", capacity=10, policy="lru")
    node.set("temp_code", 123456, ttl=5.0, current_time=100.0)

    # Key exists in storage
    assert node.size == 1

    # Lookup after expiration (timestamp 106.0 > 105.0)
    val = node.get("temp_code", current_time=106.0)
    assert val is None
    assert node.hits == 0
    assert node.misses == 1
    assert node.expired == 1

    # Lazily evicted from storage
    assert node.size == 0


def test_ttl_lfu_node():
    node = CacheNode("node-2", capacity=10, policy="lfu")
    node.set("k1", "v1", ttl=20.0, current_time=50.0)

    assert node.get("k1", current_time=60.0) == "v1"
    assert node.hits == 1

    # Expired lookup at 80.0
    assert node.get("k1", current_time=80.0) is None
    assert node.expired == 1
    assert node.misses == 1
