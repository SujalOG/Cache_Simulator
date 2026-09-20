"""
Consistent Hash Ring implementation with Virtual Nodes.
Uses a 32-bit deterministic MD5 integer space [0, 2^32 - 1] and binary search (bisect)
for O(log(V * N)) key-to-node lookups.
Supports clockwise successor failover when nodes are unhealthy.
"""

import bisect
import hashlib
from typing import List, Dict, Optional, Set, Any


def hash_32(key: str) -> int:
    """
    Deterministic 32-bit hash using MD5.
    Returns an integer in the range [0, 2^32 - 1].
    """
    digest = hashlib.md5(str(key).encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


class ConsistentHashRing:
    """
    Consistent Hash Ring mapping arbitrary keys to physical nodes.
    Each physical node is replicated across multiple virtual node positions
    to ensure uniform key distribution and minimize rebalancing variance.
    """

    def __init__(self, vnodes: int = 100) -> None:
        if vnodes <= 0:
            raise ValueError(f"vnodes must be a positive integer, got {vnodes}")
        self.vnodes: int = vnodes
        self._ring: List[int] = []  # Sorted list of virtual node hash integers
        self._ring_to_node: Dict[int, str] = {}  # Map: virtual hash -> physical node_id
        self._nodes: Set[str] = set()  # Set of physical node IDs

    @property
    def physical_nodes(self) -> List[str]:
        """Return sorted list of active physical node IDs."""
        return sorted(list(self._nodes))

    @property
    def total_vnodes(self) -> int:
        """Total number of virtual nodes on the ring."""
        return len(self._ring)

    def add_node(self, node_id: str) -> None:
        """
        Add a physical node to the ring by placing its virtual nodes.
        """
        if node_id in self._nodes:
            return  # Node already present

        self._nodes.add(node_id)
        for i in range(self.vnodes):
            vnode_key = f"{node_id}#vnode_{i}"
            h = hash_32(vnode_key)
            # Avoid collision on hash ring
            while h in self._ring_to_node:
                h = (h + 1) & 0xFFFFFFFF
            self._ring_to_node[h] = node_id
            bisect.insort(self._ring, h)

    def remove_node(self, node_id: str) -> None:
        """
        Remove a physical node and all its virtual nodes from the ring.
        """
        if node_id not in self._nodes:
            return

        self._nodes.remove(node_id)
        # Rebuild ring without the removed node's virtual nodes
        new_ring = []
        new_ring_to_node = {}
        for h, owner in self._ring_to_node.items():
            if owner != node_id:
                new_ring.append(h)
                new_ring_to_node[h] = owner

        self._ring = sorted(new_ring)
        self._ring_to_node = new_ring_to_node

    def get_node(
        self,
        key: str,
        healthy_nodes: Optional[Set[str]] = None
    ) -> Optional[str]:
        """
        Map a key to the designated physical node on the ring using clockwise lookup.
        If healthy_nodes is provided, performs Clockwise Successor Failover:
        skips any unhealthy nodes and routes to the next healthy node on the ring.
        Time complexity: O(log(total_vnodes)).
        """
        if not self._ring:
            return None

        # Determine effective set of eligible nodes
        effective_healthy = (
            healthy_nodes if healthy_nodes is not None else self._nodes
        )
        if not effective_healthy:
            return None

        h = hash_32(key)
        idx = bisect.bisect_right(self._ring, h)

        # Walk clockwise from idx until we find a virtual node belonging to a healthy physical node
        total_ring_len = len(self._ring)
        for step in range(total_ring_len):
            current_idx = (idx + step) % total_ring_len
            vnode_hash = self._ring[current_idx]
            owner_node = self._ring_to_node[vnode_hash]
            if owner_node in effective_healthy:
                return owner_node

        return None

    def get_distribution(
        self,
        keys: List[str],
        healthy_nodes: Optional[Set[str]] = None
    ) -> Dict[str, int]:
        """
        Calculate key distribution counts across physical nodes for a given list of keys.
        """
        counts: Dict[str, int] = {node_id: 0 for node_id in self._nodes}
        for k in keys:
            assigned = self.get_node(k, healthy_nodes=healthy_nodes)
            if assigned is not None:
                counts[assigned] = counts.get(assigned, 0) + 1
        return counts

    def clear(self) -> None:
        """Clear all nodes from the ring."""
        self._ring.clear()
        self._ring_to_node.clear()
        self._nodes.clear()
