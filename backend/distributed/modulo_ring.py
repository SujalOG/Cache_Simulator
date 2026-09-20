"""
Naive Modulo Hashing Ring implementation.
Maps keys to nodes using standard modulo arithmetic: hash(key) % N.
Used as a direct baseline against Consistent Hashing to demonstrate
why naive hashing causes catastrophic cache invalidation (N-1)/N during cluster scaling.
"""

from typing import List, Dict, Optional
from distributed.hash_ring import hash_32


class NaiveModuloRing:
    """
    Naive Modulo Hash router: key -> nodes[hash(key) % N].
    """

    def __init__(self, nodes: Optional[List[str]] = None) -> None:
        self._nodes: List[str] = sorted(list(nodes)) if nodes else []

    @property
    def physical_nodes(self) -> List[str]:
        return list(self._nodes)

    def add_node(self, node_id: str) -> None:
        if node_id not in self._nodes:
            self._nodes.append(node_id)
            self._nodes.sort()

    def remove_node(self, node_id: str) -> None:
        if node_id in self._nodes:
            self._nodes.remove(node_id)

    def get_node(self, key: str) -> Optional[str]:
        """
        Map key using hash(key) % N.
        """
        if not self._nodes:
            return None
        h = hash_32(key)
        idx = h % len(self._nodes)
        return self._nodes[idx]

    def get_distribution(self, keys: List[str]) -> Dict[str, int]:
        counts = {node_id: 0 for node_id in self._nodes}
        for k in keys:
            assigned = self.get_node(k)
            if assigned is not None:
                counts[assigned] = counts.get(assigned, 0) + 1
        return counts
