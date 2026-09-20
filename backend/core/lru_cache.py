"""
O(1) Least Recently Used (LRU) Cache implementation.
Combines a Hash Map for O(1) key lookups with a Doubly Linked List
for O(1) recency ordering and eviction.
"""

from typing import Any, Optional, Tuple, List
from core.dll import DoublyLinkedList, Node


class LRUCache:
    """
    LRUCache stores key-value pairs with a strict maximum capacity.
    When capacity is reached, the least recently accessed item is evicted.
    """

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError(f"Capacity must be a positive integer, got {capacity}")
        self._capacity: int = capacity
        self._map: dict[Any, Node] = {}
        self._dll: DoublyLinkedList = DoublyLinkedList()

    @property
    def capacity(self) -> int:
        """Maximum number of entries this cache can hold."""
        return self._capacity

    @property
    def size(self) -> int:
        """Current number of items in cache."""
        return len(self._map)

    def is_full(self) -> bool:
        """Check if cache has reached its maximum capacity."""
        return len(self._map) >= self._capacity

    def get(self, key: Any) -> Optional[Node]:
        """
        Retrieve the node for key and mark it as most recently used.
        Returns the Node if found, or None if not present.
        Time complexity: O(1).
        """
        if key not in self._map:
            return None
        node = self._map[key]
        self._dll.remove(node)
        self._dll.append_front(node)
        return node

    def put(
        self,
        key: Any,
        value: Any,
        expiry: Optional[float] = None
    ) -> Optional[Tuple[Any, Any]]:
        """
        Insert or update a key-value pair.
        Marks the key as most recently used.
        If cache is full and key is new, evicts the least recently used item.
        Returns (evicted_key, evicted_value) if an eviction occurred, else None.
        Time complexity: O(1).
        """
        evicted = None

        if key in self._map:
            # Update existing node
            node = self._map[key]
            node.value = value
            node.expiry = expiry
            self._dll.remove(node)
            self._dll.append_front(node)
            return None

        # Check for eviction if at capacity
        if len(self._map) >= self._capacity:
            tail_node = self._dll.pop_tail()
            if tail_node is not None:
                del self._map[tail_node.key]
                evicted = (tail_node.key, tail_node.value)

        # Insert new node at head
        new_node = Node(key=key, value=value, expiry=expiry)
        self._dll.append_front(new_node)
        self._map[key] = new_node

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
        self._dll.remove(node)
        return True

    def contains(self, key: Any) -> bool:
        """Check if key is in cache without modifying recency."""
        return key in self._map

    def clear(self) -> None:
        """Clear all entries from cache."""
        self._map.clear()
        self._dll = DoublyLinkedList()

    def keys(self) -> List[Any]:
        """Return list of keys in order from most to least recently used."""
        return [node.key for node in self._dll]

    def values(self) -> List[Any]:
        """Return list of values in order from most to least recently used."""
        return [node.value for node in self._dll]

    def items(self) -> List[Tuple[Any, Any]]:
        """Return list of (key, value) pairs from most to least recently used."""
        return [(node.key, node.value) for node in self._dll]
