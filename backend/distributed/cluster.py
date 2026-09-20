"""
CacheCluster coordinates multiple CacheNode instances using a ConsistentHashRing.
Manages request routing, node addition/removal, node failure injection,
and aggregated cluster metrics.
"""

import math
from typing import Any, Dict, List, Optional, Set
from core.cache_node import CacheNode
from distributed.hash_ring import ConsistentHashRing


class CacheCluster:
    """
    Distributed Cache Cluster coordinator.
    Routes keys to healthy physical nodes using Consistent Hashing with Virtual Nodes.
    Handles node failure via Clockwise Successor Failover.
    """

    def __init__(
        self,
        num_nodes: int = 3,
        capacity_per_node: int = 1000,
        policy: str = "lru",
        vnodes: int = 100
    ) -> None:
        self.capacity_per_node: int = capacity_per_node
        self.default_policy: str = policy.lower()
        self.vnodes: int = vnodes

        self.nodes: Dict[str, CacheNode] = {}
        self.ring: ConsistentHashRing = ConsistentHashRing(vnodes=vnodes)

        # Initialize requested number of nodes
        for i in range(num_nodes):
            node_id = f"node_{i}"
            self.add_node(node_id=node_id, capacity=capacity_per_node, policy=self.default_policy)

    @property
    def node_count(self) -> int:
        """Total number of registered physical nodes."""
        return len(self.nodes)

    @property
    def healthy_nodes(self) -> Set[str]:
        """Set of node IDs that are currently active."""
        return {node_id for node_id, node in self.nodes.items() if node.is_active}

    @property
    def failed_nodes(self) -> Set[str]:
        """Set of node IDs that are currently marked failed."""
        return {node_id for node_id, node in self.nodes.items() if not node.is_active}

    def add_node(
        self,
        node_id: str,
        capacity: Optional[int] = None,
        policy: Optional[str] = None
    ) -> CacheNode:
        """
        Add a new physical node to the cluster and register it on the hash ring.
        """
        cap = capacity if capacity is not None else self.capacity_per_node
        pol = policy if policy is not None else self.default_policy

        node = CacheNode(node_id=node_id, capacity=cap, policy=pol)
        self.nodes[node_id] = node
        self.ring.add_node(node_id)
        return node

    def remove_node(self, node_id: str) -> Optional[CacheNode]:
        """
        Remove a physical node from the cluster and unregister it from the hash ring.
        """
        if node_id not in self.nodes:
            return None

        self.ring.remove_node(node_id)
        return self.nodes.pop(node_id)

    def fail_node(self, node_id: str) -> bool:
        """
        Simulate node crash.
        The node is marked failed; the hash ring routes traffic to its clockwise successor.
        """
        if node_id not in self.nodes:
            return False
        self.nodes[node_id].fail()
        return True

    def recover_node(self, node_id: str) -> bool:
        """
        Recover a previously failed node back to active status.
        """
        if node_id not in self.nodes:
            return False
        self.nodes[node_id].recover()
        return True

    def route_key(self, key: str) -> Optional[str]:
        """
        Determine which healthy node owns the given key using clockwise successor failover.
        """
        return self.ring.get_node(key, healthy_nodes=self.healthy_nodes)

    def get(
        self,
        key: str,
        current_time: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Route GET request to the responsible healthy node.
        Returns result dictionary containing:
        - found: bool (True for cache hit, False for miss)
        - value: Any (stored value or None)
        - node_id: Optional[str] (node that serviced the request)
        """
        target_node_id = self.route_key(key)
        if target_node_id is None:
            return {"found": False, "value": None, "node_id": None}

        node = self.nodes[target_node_id]
        val = node.get(key, current_time=current_time)
        return {
            "found": (val is not None),
            "value": val,
            "node_id": target_node_id
        }

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
        current_time: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Route SET request to the responsible healthy node.
        """
        target_node_id = self.route_key(key)
        if target_node_id is None:
            return {"success": False, "node_id": None}

        node = self.nodes[target_node_id]
        success = node.set(key, value, ttl=ttl, current_time=current_time)
        return {
            "success": success,
            "node_id": target_node_id
        }

    def delete(self, key: str) -> Dict[str, Any]:
        """
        Route DELETE request to the responsible healthy node.
        """
        target_node_id = self.route_key(key)
        if target_node_id is None:
            return {"success": False, "node_id": None}

        node = self.nodes[target_node_id]
        success = node.delete(key)
        return {
            "success": success,
            "node_id": target_node_id
        }

    def clear(self) -> None:
        """Clear all nodes in the cluster."""
        for node in self.nodes.values():
            node.clear()

    def reset_metrics(self) -> None:
        """Reset statistical metrics across all nodes."""
        for node in self.nodes.values():
            node.reset_metrics()

    def stats(self) -> Dict[str, Any]:
        """
        Return comprehensive aggregate and per-node metrics for the entire cluster.
        """
        node_stats = [node.stats() for node in self.nodes.values()]

        total_hits = sum(ns["hits"] for ns in node_stats)
        total_misses = sum(ns["misses"] for ns in node_stats)
        total_evictions = sum(ns["evictions"] for ns in node_stats)
        total_expired = sum(ns["expired"] for ns in node_stats)
        total_gets = sum(ns["gets"] for ns in node_stats)
        total_sets = sum(ns["sets"] for ns in node_stats)
        total_keys = sum(ns["keys_count"] for ns in node_stats)
        total_capacity = sum(ns["capacity"] for ns in node_stats)

        total_lookups = total_hits + total_misses
        hit_rate = (total_hits / total_lookups * 100) if total_lookups > 0 else 0.0
        miss_rate = (total_misses / total_lookups * 100) if total_lookups > 0 else 0.0

        # Calculate standard deviation of keys and requests across nodes to measure balance
        active_count = len(self.healthy_nodes)
        if active_count > 1:
            mean_keys = total_keys / len(node_stats)
            variance_keys = sum((ns["keys_count"] - mean_keys) ** 2 for ns in node_stats) / len(node_stats)
            std_dev_keys = math.sqrt(variance_keys)

            mean_reqs = total_lookups / len(node_stats)
            variance_reqs = sum((ns["total_lookups"] - mean_reqs) ** 2 for ns in node_stats) / len(node_stats)
            std_dev_reqs = math.sqrt(variance_reqs)
        else:
            std_dev_keys = 0.0
            std_dev_reqs = 0.0

        return {
            "cluster_summary": {
                "total_nodes": len(self.nodes),
                "healthy_nodes": len(self.healthy_nodes),
                "failed_nodes": len(self.failed_nodes),
                "total_capacity": total_capacity,
                "total_keys_stored": total_keys,
                "total_lookups": total_lookups,
                "total_hits": total_hits,
                "total_misses": total_misses,
                "hit_rate_pct": round(hit_rate, 2),
                "miss_rate_pct": round(miss_rate, 2),
                "total_evictions": total_evictions,
                "total_expired": total_expired,
                "total_gets": total_gets,
                "total_sets": total_sets,
                "balance_std_dev_keys": round(std_dev_keys, 2),
                "balance_std_dev_requests": round(std_dev_reqs, 2),
            },
            "nodes": node_stats
        }
