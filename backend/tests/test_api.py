"""
Integration tests for Flask REST API endpoints.
"""

import json
import pytest
from app import app


@pytest.fixture
def client():
    """Create Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_api_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "healthy"
    assert "redis_connected" in data


def test_api_simulate_success(client):
    payload = {
        "policy": "lru",
        "nodes": 3,
        "capacity_per_node": 100,
        "requests": 500,
        "unique_keys": 50,
        "workload_pattern": "hot_keys",
        "read_ratio": 0.8
    }
    response = client.post(
        "/api/simulate",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["total_requests"] == 500
    assert "hit_rate_pct" in data
    assert "latency" in data
    assert "node_distribution" in data
    assert len(data["node_distribution"]) == 3


def test_api_simulate_with_failure(client):
    payload = {
        "policy": "lru",
        "nodes": 3,
        "capacity_per_node": 100,
        "requests": 400,
        "unique_keys": 50,
        "fail_at_request": 200,
        "failed_node_id": "node_0"
    }
    response = client.post(
        "/api/simulate",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    cluster_summary = data["cluster_state"]["cluster_summary"]
    assert cluster_summary["failed_nodes"] == 1
    assert cluster_summary["healthy_nodes"] == 2


def test_api_simulate_validation_errors(client):
    # Invalid policy
    res1 = client.post("/api/simulate", data=json.dumps({"policy": "invalid"}), content_type="application/json")
    assert res1.status_code == 400

    # Invalid nodes count
    res2 = client.post("/api/simulate", data=json.dumps({"nodes": 0}), content_type="application/json")
    assert res2.status_code == 400

    # Invalid workload pattern
    res3 = client.post("/api/simulate", data=json.dumps({"workload_pattern": "magic"}), content_type="application/json")
    assert res3.status_code == 400


def test_api_experiments_list(client):
    response = client.get("/api/experiments/list")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "experiments" in data
    assert len(data["experiments"]) == 6


def test_api_experiments_run_success(client):
    payload = {
        "experiment_id": "lru_vs_lfu",
        "params": {
            "requests": 200,
            "keys": 40,
            "capacity": 10
        }
    }
    response = client.post(
        "/api/experiments/run",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["experiment_id"] == "lru_vs_lfu"
    assert "lru" in data
    assert "lfu" in data


def test_api_experiments_run_invalid_id(client):
    payload = {"experiment_id": "unknown_experiment"}
    response = client.post(
        "/api/experiments/run",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 404


def test_api_experiments_run_missing_id(client):
    response = client.post(
        "/api/experiments/run",
        data=json.dumps({}),
        content_type="application/json"
    )
    assert response.status_code == 400
