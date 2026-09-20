"""
Unit tests for O(1) LRU Cache implementation.
"""

import pytest
from core.lru_cache import LRUCache


def test_lru_invalid_capacity():
    with pytest.raises(ValueError):
        LRUCache(0)
    with pytest.raises(ValueError):
        LRUCache(-5)


def test_lru_basic_put_get():
    cache = LRUCache(capacity=2)
    assert cache.capacity == 2
    assert cache.size == 0

    assert cache.get("a") is None

    # Insert "a"
    evicted = cache.put("a", 100)
    assert evicted is None
    assert cache.size == 1
    node_a = cache.get("a")
    assert node_a is not None
    assert node_a.value == 100

    # Insert "b"
    evicted = cache.put("b", 200)
    assert evicted is None
    assert cache.size == 2
    assert cache.is_full()

    # Verify both accessible
    assert cache.get("a").value == 100
    assert cache.get("b").value == 200


def test_lru_eviction_order():
    # Cache capacity 2: insert A, then B -> [B, A]
    cache = LRUCache(capacity=2)
    cache.put("A", 1)
    cache.put("B", 2)

    # Insert C -> A should be evicted (least recently used)
    evicted = cache.put("C", 3)
    assert evicted == ("A", 1)
    assert cache.get("A") is None
    assert cache.get("B").value == 2
    assert cache.get("C").value == 3


def test_lru_recency_update_on_get():
    # Cache capacity 2: insert A, then B -> [B, A]
    cache = LRUCache(capacity=2)
    cache.put("A", 1)
    cache.put("B", 2)

    # Access A -> moves A to head: [A, B]
    assert cache.get("A").value == 1

    # Insert C -> B should now be evicted!
    evicted = cache.put("C", 3)
    assert evicted == ("B", 2)
    assert cache.get("B") is None
    assert cache.get("A").value == 1
    assert cache.get("C").value == 3


def test_lru_overwrite_existing_key():
    cache = LRUCache(capacity=2)
    cache.put("A", 1)
    cache.put("B", 2)

    # Overwrite A with new value
    evicted = cache.put("A", 999)
    assert evicted is None
    assert cache.size == 2
    assert cache.get("A").value == 999

    # Now A is most recently used. Inserting C should evict B.
    evicted = cache.put("C", 3)
    assert evicted == ("B", 2)
    assert cache.get("A").value == 999
    assert cache.get("C").value == 3


def test_lru_delete_and_clear():
    cache = LRUCache(capacity=3)
    cache.put("A", 1)
    cache.put("B", 2)
    cache.put("C", 3)

    assert cache.delete("B") is True
    assert cache.size == 2
    assert cache.get("B") is None
    assert cache.delete("NON_EXISTENT") is False

    cache.clear()
    assert cache.size == 0
    assert cache.get("A") is None
    assert cache.get("C") is None


def test_lru_capacity_one():
    cache = LRUCache(capacity=1)
    evicted = cache.put("A", 1)
    assert evicted is None
    assert cache.get("A").value == 1

    evicted = cache.put("B", 2)
    assert evicted == ("A", 1)
    assert cache.get("A") is None
    assert cache.get("B").value == 2
