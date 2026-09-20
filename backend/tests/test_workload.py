"""
Unit tests for WorkloadGenerator and ZipfSampler.
"""

import pytest
from simulator.workload import WorkloadGenerator, ZipfSampler


def test_zipf_sampler_skew():
    """
    Verify Zipfian distribution produces strong skew towards low-indexed keys.
    Top 20% of keys should capture >= 60% of accesses for alpha=0.99.
    """
    n = 100
    sampler = ZipfSampler(n=n, alpha=0.99)
    samples = [sampler.sample() for _ in range(5000)]

    top_20_count = sum(1 for s in samples if s < 20)
    top_20_pct = (top_20_count / len(samples)) * 100
    assert top_20_pct >= 55.0, f"Zipf skew lower than expected: {top_20_pct}%"


def test_workload_generator_patterns():
    for pattern in ["random", "hot_keys", "sequential"]:
        reqs = WorkloadGenerator.generate(
            pattern=pattern,
            num_requests=500,
            num_unique_keys=50,
            read_ratio=0.8
        )
        assert len(reqs) == 500
        get_count = sum(1 for op, _, _ in reqs if op == "GET")
        set_count = sum(1 for op, _, _ in reqs if op == "SET")
        assert get_count + set_count == 500
        # Around 80% should be GET (allow normal binomial distribution leeway)
        assert 320 <= get_count <= 460


def test_workload_generator_invalid_pattern():
    with pytest.raises(ValueError):
        WorkloadGenerator.generate(pattern="non_existent_pattern")
