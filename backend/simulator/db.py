"""
Simulated Backing Database.
Acts as the persistent backing store behind the cache layer.
Simulates realistic database read and write latencies (e.g., 15-30ms)
with natural variance.
"""

import random
from typing import Any, Dict, Optional, Tuple


class SimulatedDatabase:
    """
    In-memory persistent database simulating disk/network latency.
    """

    def __init__(
        self,
        base_read_latency_ms: float = 20.0,
        read_latency_std_ms: float = 4.0,
        base_write_latency_ms: float = 25.0,
        write_latency_std_ms: float = 5.0
    ) -> None:
        self.base_read_latency_ms = base_read_latency_ms
        self.read_latency_std_ms = read_latency_std_ms
        self.base_write_latency_ms = base_write_latency_ms
        self.write_latency_std_ms = write_latency_std_ms

        self._store: Dict[str, Any] = {}
        self.queries_count: int = 0
        self.writes_count: int = 0

    def seed(self, initial_data: Dict[str, Any]) -> None:
        """Seed the database with initial key-value records."""
        self._store.update(initial_data)

    def _sample_latency(self, mean: float, std: float, min_val: float = 5.0) -> float:
        """Sample latency from normal distribution clipped to a minimum value."""
        sampled = random.gauss(mean, std)
        return round(max(min_val, sampled), 3)

    def read(self, key: str) -> Tuple[Any, float]:
        """
        Fetch value from persistent storage.
        If key does not exist yet, generates a simulated record and stores it.
        Returns: (value, latency_ms)
        """
        self.queries_count += 1
        latency = self._sample_latency(self.base_read_latency_ms, self.read_latency_std_ms)

        if key not in self._store:
            # Auto-generate simulated database record
            self._store[key] = f"db_val_{key}"

        return self._store[key], latency

    def write(self, key: str, value: Any) -> float:
        """
        Write or update value in persistent storage.
        Returns: latency_ms
        """
        self.writes_count += 1
        latency = self._sample_latency(self.base_write_latency_ms, self.write_latency_std_ms)
        self._store[key] = value
        return latency

    def contains(self, key: str) -> bool:
        """Check if key exists in storage without adding latency."""
        return key in self._store

    def size(self) -> int:
        """Total records in backing store."""
        return len(self._store)

    def reset(self) -> None:
        """Reset database store and counters."""
        self._store.clear()
        self.queries_count = 0
        self.writes_count = 0
