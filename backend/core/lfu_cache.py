"""
O(1) Least Frequently Used (LFU) Cache implementation.
Maintains frequency buckets using Doubly Linked Lists and tracks the minimum
frequency to achieve strict O(1) time complexity for get, put, and eviction.
Ties in frequency are broken using LRU order (least recently used within that frequency).
"""

from typing import Any, Optional, Tuple, List
from collections import defaultdict
from core.dll import DoublyLinkedList, Node


class LFUCache:
    """
    LFUCache stores key-value pairs with a strict maximum capacity.
    When full, the item accessed the least number of times is evicted.
    Ties in frequency are broken using LRU recency within the frequency bucket.
    """

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError(f"Capacity must be a positive integer, got {capacity}")
        self._capacity: int = capacity
        self._map: dict[Any, Node] = {}
        self._freq_buckets: dict[int, DoublyLinkedList] = defaultdict(DoublyLinkedList)
        self._min_freq: int = 0

    @property
    def capacity(self) -> int:
        """Maximum entries this cache can hold."""
        return self._capacity

    @property
    def size(self) -> int:
        """Current number of items in cache."""
        return len(self._map)

    @property
    def min_freq(self) -> int:
        """Current minimum frequency across all stored items."""
        return self._min_freq

    def is_full(self) -> bool:
        """Check if cache has reached its maximum capacity."""
        return len(self._map) >= self._capacity

    def _promote_frequency(self, node: Node) -> None:
        """
        Promote a node to frequency + 1.
        Unlinks node from current frequency bucket and inserts at front of new bucket.
        Updates min_freq if necessary.
        Time complexity: O(1).
        """
        curr_freq = node.freq
        curr_bucket = self._freq_buckets[curr_freq]
        curr_bucket.remove(node)

        # If current bucket was the minimum frequency and is now empty, advance min_freq
        if curr_bucket.is_empty() and self._min_freq == curr_freq:
            self._min_freq += 1

        # Advance node frequency and place at head of new frequency bucket
        node.freq += 1
        self._freq_buckets[node.freq].append_front(node)

    def get(self, key: Any) -> Optional[Node]:
        """
        Retrieve node for key, increment its frequency count, and promote it.
        Returns Node if found, or None if not present.
        Time complexity: O(1).
        """
        if key not in self._map:
            return None
        node = self._map[key]
        self._promote_frequency(node)
        return node

    def put(
        self,
        key: Any,
        value: Any,
        expiry: Optional[float] = None
    ) -> Optional[Tuple[Any, Any]]:
        """
        Insert or update a key-value pair.
        If key exists, updates value/expiry and promotes frequency.
        If full and key is new, evicts least frequently used item (LRU tie-break).
        Returns (evicted_key, evicted_value) if an eviction occurred, else None.
        Time complexity: O(1).
        """
        evicted = None

        if key in self._map:
            node = self._map[key]
            node.value = value
            node.expiry = expiry
            self._promote_frequency(node)
            return None

        # Check for eviction if at capacity
        if len(self._map) >= self._capacity:
            min_bucket = self._freq_buckets[self._min_freq]
            lfu_node = min_bucket.pop_tail()
            if lfu_node is not None:
                del self._map[lfu_node.key]
                evicted = (lfu_node.key, lfu_node.value)

        # Insert new node with frequency 1
        new_node = Node(key=key, value=value, freq=1, expiry=expiry)
        self._freq_buckets[1].append_front(new_node)
        self._map[key] = new_node
        self._min_freq = 1

        return evicted

    def delete(self, key: Any) -> bool:
        """
        Remove key from cache.
        Returns True if key was present and removed, False otherwise.
        Time complexity: O(1).
        """
        if key not in self._map:
            return False
        node = self._map.pop(key)
        bucket = self._freq_buckets[node.freq]
        bucket.remove(node)
        # If bucket was min_freq and is now empty, we might need to adjust min_freq
        if bucket.is_empty() and self._min_freq == node.freq:
            if self.size > 0:
                # Find the new lowest non-empty frequency
                self._min_freq = min(
                    f for f, b in self._freq_buckets.items() if not b.is_empty()
                )
            else:
                self._min_freq = 0
        return True

    def contains(self, key: Any) -> bool:
        """Check if key exists without modifying frequency."""
        return key in self._map

    def clear(self) -> None:
        """Clear all entries from cache."""
        self._map.clear()
        self._freq_buckets.clear()
        self._min_freq = 0

    def keys(self) -> List[Any]:
        """Return all keys currently in the cache."""
        return list(self._map.keys())

    def items(self) -> List[Tuple[Any, Any]]:
        """Return all (key, value) pairs."""
        return [(node.key, node.value) for node in self._map.values()]
