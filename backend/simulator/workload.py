"""
Workload Generator for Distributed Cache Simulation.
Generates realistic request traffic including:
1. Random (Uniform) distribution
2. Hot Keys (Zipfian / Power Law distribution, YCSB standard)
3. Sequential access (cache thrashing / sweep)
Configurable read/write ratios, key pool size, and request volume.
"""

import bisect
import random
from typing import List, Tuple, Any, Optional


class ZipfSampler:
    """
    Fast Zipfian (Power Law) generator using precomputed Cumulative Distribution Function (CDF).
    Generates indices in range [0, n-1] according to P(k) proportional to 1 / (k+1)^alpha.
    """

    def __init__(self, n: int, alpha: float = 0.99) -> None:
        self.n = max(1, n)
        self.alpha = max(0.01, alpha)

        # Compute unnormalized probabilities
        probs = [1.0 / ((i + 1) ** self.alpha) for i in range(self.n)]
        sum_probs = sum(probs)

        # Build CDF
        self.cdf: List[float] = []
        cumulative = 0.0
        for p in probs:
            cumulative += p / sum_probs
            self.cdf.append(cumulative)
        self.cdf[-1] = 1.0  # Guard against floating-point inaccuracy

    def sample(self) -> int:
        """Draw an index from the Zipfian distribution in O(log n) time."""
        u = random.random()
        idx = bisect.bisect_right(self.cdf, u)
        return min(idx, self.n - 1)


class WorkloadGenerator:
    """
    Generates streams of cache operations: List of (operation, key, value).
    """

    SUPPORTED_PATTERNS = ("random", "hot_keys", "sequential")

    @classmethod
    def generate(
        cls,
        pattern: str = "hot_keys",
        num_requests: int = 10000,
        num_unique_keys: int = 1000,
        read_ratio: float = 0.8,
        zipf_alpha: float = 0.99,
        key_prefix: str = "item:"
    ) -> List[Tuple[str, str, Optional[Any]]]:
        """
        Generate a list of (operation, key, value) requests.
        - operation: 'GET' or 'SET'
        - key: string key (e.g. 'item:42')
        - value: simulated payload string for SET, None for GET
        """
        pattern = pattern.lower()
        if pattern not in cls.SUPPORTED_PATTERNS:
            raise ValueError(
                f"Unsupported workload pattern: {pattern}. "
                f"Must be one of {cls.SUPPORTED_PATTERNS}"
            )

        keys_pool = [f"{key_prefix}{i}" for i in range(num_unique_keys)]
        requests: List[Tuple[str, str, Optional[Any]]] = []

        if pattern == "hot_keys":
            zipf = ZipfSampler(n=num_unique_keys, alpha=zipf_alpha)
            for _ in range(num_requests):
                key_idx = zipf.sample()
                key = keys_pool[key_idx]
                is_read = random.random() < read_ratio
                op = "GET" if is_read else "SET"
                val = None if is_read else f"val_{key}"
                requests.append((op, key, val))

        elif pattern == "random":
            for _ in range(num_requests):
                key = random.choice(keys_pool)
                is_read = random.random() < read_ratio
                op = "GET" if is_read else "SET"
                val = None if is_read else f"val_{key}"
                requests.append((op, key, val))

        elif pattern == "sequential":
            for i in range(num_requests):
                key = keys_pool[i % num_unique_keys]
                is_read = random.random() < read_ratio
                op = "GET" if is_read else "SET"
                val = None if is_read else f"val_{key}"
                requests.append((op, key, val))

        return requests
