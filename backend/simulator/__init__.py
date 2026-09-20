"""
Simulation Engine & Experiment Lab
Contains simulation execution, workload generation, and real-world benchmarking:
- db.py: Simulated backing database with realistic read latency
- workload.py: Zipfian (Power Law), Random, and Sequential workload generators
- metrics.py: Detailed metrics collection (Hits/Misses, Latency percentiles, Node load)
- engine.py: Hybrid deterministic simulation runner
- redis_client.py: Live Redis benchmark runner using connection pooling
- experiments.py: Suite of 6 canonical system design experiments
"""
