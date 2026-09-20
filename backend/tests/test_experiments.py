"""
Unit tests for the 6 Canonical Experiments.
"""

from simulator.experiments import ExperimentSuite


def test_experiment_1_lru_vs_lfu():
    res = ExperimentSuite.experiment_1_lru_vs_lfu(
        num_requests=300,
        num_keys=50,
        capacity_per_node=10
    )
    assert res["experiment_id"] == "lru_vs_lfu"
    assert "lru" in res and "lfu" in res
    assert "interview_insights" in res
    assert 0 <= res["lru"]["hit_rate_pct"] <= 100
    assert 0 <= res["lfu"]["hit_rate_pct"] <= 100


def test_experiment_2_workload_patterns():
    res = ExperimentSuite.experiment_2_workload_patterns(
        num_requests=300,
        num_keys=50,
        capacity_per_node=10
    )
    assert res["experiment_id"] == "workload_patterns"
    assert "hot_keys" in res["patterns"]
    assert "random" in res["patterns"]
    assert "sequential" in res["patterns"]


def test_experiment_3_node_scaling():
    res = ExperimentSuite.experiment_3_node_scaling(
        nodes_list=[1, 2, 3],
        num_requests=300,
        num_keys=50,
        capacity_per_node=10
    )
    assert res["experiment_id"] == "node_scaling"
    assert len(res["scaling"]) == 3
    assert res["scaling"][0]["nodes"] == 1
    assert res["scaling"][2]["nodes"] == 3


def test_experiment_4_consistent_vs_modulo():
    res = ExperimentSuite.experiment_4_consistent_vs_modulo(
        num_keys=500,
        initial_nodes=3,
        final_nodes=4
    )
    assert res["experiment_id"] == "consistent_vs_modulo"
    assert "naive_modulo" in res
    assert "consistent_hashing" in res
    # Consistent hashing should move substantially fewer keys
    assert res["consistent_hashing"]["churn_pct"] < res["naive_modulo"]["churn_pct"]


def test_experiment_5_node_failure():
    res = ExperimentSuite.experiment_5_node_failure(
        num_requests=400,
        num_keys=60,
        capacity_per_node=15
    )
    assert res["experiment_id"] == "node_failure"
    assert "healthy_cluster" in res
    assert "failed_cluster" in res
    assert res["failed_cluster"]["failed_node"] == "node_1"


def test_experiment_6_simulator_vs_redis():
    res = ExperimentSuite.experiment_6_simulator_vs_redis(
        num_requests=200,
        num_keys=40,
        capacity=15
    )
    assert res["experiment_id"] == "simulator_vs_redis"
    assert "simulator" in res
    assert "redis" in res
    assert "available" in res["redis"]
