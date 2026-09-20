"""
Unit tests for O(1) LFU Cache implementation.
"""

import pytest
from core.lfu_cache import LFUCache


def test_lfu_invalid_capacity():
    with pytest.raises(ValueError):
        LFUCache(0)
    with pytest.raises(ValueError):
        LFUCache(-1)


def test_lfu_basic_put_get():
    cache = LFUCache(capacity=2)
    assert cache.capacity == 2
    assert cache.size == 0

    assert cache.get("a") is None

    evicted = cache.put("a", 10)
    assert evicted is None
    assert cache.size == 1
    assert cache.min_freq == 1

    node_a = cache.get("a")
    assert node_a is not None
    assert node_a.value == 10
    assert node_a.freq == 2
    assert cache.min_freq == 2


def test_lfu_eviction_by_frequency():
    cache = LFUCache(capacity=2)
    cache.put("A", 1)
    cache.put("B", 2)

    # Access A multiple times so its frequency becomes 3
    cache.get("A")
    cache.get("A")

    # B has frequency 1, A has frequency 3
    # Inserting C (capacity 2) should evict B (lowest frequency)
    evicted = cache.put("C", 3)
    assert evicted == ("B", 2)
    assert cache.get("B") is None
    assert cache.get("A").value == 1
    assert cache.get("C").value == 3


def test_lfu_tie_breaking_via_lru():
    """
    When multiple keys share the minimum frequency,
    the least recently used one must be evicted.
    """
    cache = LFUCache(capacity=2)
    # Insert A then B. Both have frequency 1.
    cache.put("A", 1)
    cache.put("B", 2)

    # B was inserted after A, so A is the least recently used in frequency bucket 1.
    # Inserting C should evict A.
    evicted = cache.put("C", 3)
    assert evicted == ("A", 1)
    assert cache.get("A") is None
    assert cache.get("B").value == 2
    assert cache.get("C").value == 3


def test_lfu_tie_breaking_with_equal_higher_frequency():
    """
    Test tie-breaking when both keys have frequency 2.
    """
    cache = LFUCache(capacity=2)
    cache.put("A", 1)
    cache.put("B", 2)

    # Access A then B -> both have frequency 2.
    # Recency within bucket 2: B is MRU, A is LRU.
    cache.get("A")  # freq 2
    cache.get("B")  # freq 2

    # Insert C -> A should be evicted because both A and B have freq 2, but A was accessed earlier.
    evicted = cache.put("C", 3)
    assert evicted == ("A", 1)
    assert cache.get("A") is None
    assert cache.get("B").value == 2
    assert cache.get("C").value == 3


def test_lfu_overwrite_promotes_frequency():
    cache = LFUCache(capacity=2)
    cache.put("A", 1)
    cache.put("B", 2)

    # Overwrite A -> should update value and promote frequency from 1 to 2
    cache.put("A", 999)
    assert cache.get("A").value == 999  # now freq 3

    # B still has freq 1 -> inserting C should evict B
    evicted = cache.put("C", 3)
    assert evicted == ("B", 2)
    assert cache.get("B") is None
    assert cache.get("A").value == 999


def test_lfu_delete_and_clear():
    cache = LFUCache(capacity=3)
    cache.put("A", 1)
    cache.put("B", 2)
    cache.put("C", 3)

    assert cache.delete("B") is True
    assert cache.size == 2
    assert cache.get("B") is None
    assert cache.delete("NOT_FOUND") is False

    cache.clear()
    assert cache.size == 0
    assert cache.min_freq == 0
    assert cache.get("A") is None
