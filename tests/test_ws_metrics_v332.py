import pytest
from backend.app.main import app, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX, MAX_CONCURRENT_TASKS

from fastapi.testclient import TestClient

def test_ws_metrics_v332_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "memory_percent" in data
    assert "cpu_usage_percent" in data
    assert "open_fds" in data
    assert "thread_count" in data
    assert data["version"] == APP_VERSION
    assert data["git_commit"] == GIT_COMMIT
    assert data["open_fds"] >= 0
    assert data["thread_count"] > 0

def test_ws_metrics_v332_prometheus():
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    metrics_text = response.text
    assert "adk_memory_percent" in metrics_text
    assert "adk_cpu_usage_percent" in metrics_text
    assert "adk_open_fds" in metrics_text
    assert "adk_thread_count" in metrics_text
    assert "adk_peak_active_ws_connections" in metrics_text

def test_ws_metrics_v332_version():
    client = TestClient(app)
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json()["version"] == APP_VERSION