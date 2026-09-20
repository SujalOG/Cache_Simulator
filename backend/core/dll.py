"""
Handcrafted Doubly Linked List and Node primitives.
Used as the foundational building block for O(1) LRU and LFU cache eviction.
"""

from typing import Any, Optional


class Node:
    """
    Doubly Linked List node holding key, value, access metadata, and pointers.
    """
    __slots__ = ('key', 'value', 'freq', 'expiry', 'prev', 'next')

    def __init__(
        self,
        key: Any,
        value: Any,
        freq: int = 1,
        expiry: Optional[float] = None
    ) -> None:
        self.key = key
        self.value = value
        self.freq = freq
        self.expiry = expiry
        self.prev: Optional['Node'] = None
        self.next: Optional['Node'] = None

    def is_expired(self, current_time: float) -> bool:
        """Check if node's TTL has expired."""
        if self.expiry is None:
            return False
        return current_time >= self.expiry

    def __repr__(self) -> str:
        return f"Node(key={self.key}, value={self.value}, freq={self.freq}, expiry={self.expiry})"


class DoublyLinkedList:
    """
    Doubly Linked List with sentinel head and tail nodes.
    Guarantees O(1) insertion at front, O(1) deletion of an arbitrary node,
    and O(1) eviction of the tail node.
    """

    def __init__(self) -> None:
        self.head = Node(None, None)
        self.tail = Node(None, None)
        self.head.next = self.tail
        self.tail.prev = self.head
        self._size: int = 0

    @property
    def size(self) -> int:
        """Return the number of user nodes in the list."""
        return self._size

    def is_empty(self) -> bool:
        """Check if the list contains no user nodes."""
        return self._size == 0

    def append_front(self, node: Node) -> None:
        """
        Insert node immediately after the sentinel head (most recently used).
        Time complexity: O(1).
        """
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node
        self._size += 1

    def remove(self, node: Node) -> Node:
        """
        Unlink and remove an existing node from the list.
        Time complexity: O(1).
        """
        if node.prev is not None and node.next is not None:
            node.prev.next = node.next
            node.next.prev = node.prev
            node.prev = None
            node.next = None
            self._size -= 1
        return node

    def pop_tail(self) -> Optional[Node]:
        """
        Remove and return the node immediately before sentinel tail (least recently used).
        Returns None if list is empty.
        Time complexity: O(1).
        """
        if self.is_empty():
            return None
        lru_node = self.tail.prev
        return self.remove(lru_node)

    def __len__(self) -> int:
        return self._size

    def __iter__(self):
        """Iterate from most recently used (head.next) to least recently used (tail.prev)."""
        curr = self.head.next
        while curr and curr is not self.tail:
            yield curr
            curr = curr.next
