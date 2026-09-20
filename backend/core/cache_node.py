"""
CacheNode represents an individual cache server instance in the cluster.
It wraps either an LRU or LFU cache engine, manages TTL expiration,
tracks node-level performance metrics, and supports failure state simulation.
"""

import time
from typing import Any, Optional, Dict, Union
from core.lru_cache import LRUCache
from core.lfu_cache import LFUCache


class CacheNode:
    """
    Physical cache node handling storage, TTL checks, metric gathering, and failure simulation.
    """

    def __init__(
        self,
        node_id: str,
        capacity: int,
        policy: str = "lru"
    ) -> None:
        self.node_id: str = node_id
        self.capacity: int = capacity
        self.policy: str = policy.lower()
        self.status: str = "active"  # "active" or "failed"

        # Initialize underlying cache engine
        if self.policy == "lru":
            self._cache: Union[LRUCache, LFUCache] = LRUCache(capacity)
        elif self.policy == "lfu":
            self._cache = LFUCache(capacity)
        else:
            raise ValueError(f"Unsupported eviction policy: {policy}. Must be 'lru' or 'lfu'.")

        # Performance metrics
        self.hits: int = 0
        self.misses: int = 0
        self.evictions: int = 0
        self.expired: int = 0
        self.gets: int = 0
        self.sets: int = 0
        self.deletes: int = 0

    @property
    def is_active(self) -> bool:
        """Check if node is currently operational."""
        return self.status == "active"

    @property
    def size(self) -> int:
        """Current number of items held in the node's cache."""
        return self._cache.size

    def fail(self) -> None:
        """Simulate node failure / crash."""
        self.status = "failed"

    def recover(self) -> None:
        """Recover node to active status."""
        self.status = "active"

    def get(self, key: Any, current_time: Optional[float] = None) -> Optional[Any]:
        """
        Look up key on this node.
        Handles TTL expiration lazily: if the item exists but has expired,
        it is evicted, counted as expired, and treated as a cache miss.
        """
        self.gets += 1

        if not self.is_active:
            self.misses += 1
            return None

        node = self._cache.get(key)
        if node is None:
            self.misses += 1
            return None

        now = current_time if current_time is not None else time.time()
        if node.is_expired(now):
            # Expired: remove lazily and count as expired & miss
            self._cache.delete(key)
            self.expired += 1
            self.misses += 1
            return None

        self.hits += 1
        return node.value

    def set(
        self,
        key: Any,
        value: Any,
        ttl: Optional[float] = None,
        current_time: Optional[float] = None
    ) -> bool:
        """
        Store key-value pair with optional TTL (seconds).
        Returns True if stored successfully, False if node is failed.
        """
        self.sets += 1

        if not self.is_active:
            return False

        now = current_time if current_time is not None else time.time()
        expiry = (now + ttl) if (ttl is not None and ttl > 0) else None

        evicted = self._cache.put(key, value, expiry=expiry)
        if evicted is not None:
            self.evictions += 1

        return True

    def delete(self, key: Any) -> bool:
        """
        Remove key from this node.
        Returns True if deleted, False otherwise.
        """
        self.deletes += 1
        if not self.is_active:
            return False
        return self._cache.delete(key)

    def contains(self, key: Any) -> bool:
        """Check if node contains key (active only)."""
        if not self.is_active:
            return False
        return self._cache.contains(key)

    def clear(self) -> None:
        """Clear all stored entries on this node."""
        self._cache.clear()

    def reset_metrics(self) -> None:
        """Reset all statistical counters."""
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.expired = 0
        self.gets = 0
        self.sets = 0
        self.deletes = 0

    def stats(self) -> Dict[str, Any]:
        """
        Return a snapshot dictionary of node metrics.
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0.0
        miss_rate = (self.misses / total_requests * 100) if total_requests > 0 else 0.0

        return {
            "node_id": self.node_id,
            "status": self.status,
            "policy": self.policy,
            "capacity": self.capacity,
            "keys_count": self.size,
            "utilization_pct": round((self.size / self.capacity) * 100, 2) if self.capacity > 0 else 0.0,
            "hits": self.hits,
            "misses": self.misses,
            "total_lookups": total_requests,
            "hit_rate_pct": round(hit_rate, 2),
            "miss_rate_pct": round(miss_rate, 2),
            "evictions": self.evictions,
            "expired": self.expired,
            "gets": self.gets,
            "sets": self.sets,
            "deletes": self.deletes,
        }

    def __repr__(self) -> str:
        return (
            f"CacheNode(id={self.node_id}, status={self.status}, "
            f"policy={self.policy}, size={self.size}/{self.capacity})"
        )
