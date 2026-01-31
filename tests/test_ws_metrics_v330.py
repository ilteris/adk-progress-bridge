import pytest
from fastapi.testclient import TestClient
from backend.app.main import app, APP_VERSION, GIT_COMMIT

def test_ws_metrics_v330_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "memory_percent" in data
    assert data["version"] == APP_VERSION
    assert data["git_commit"] == GIT_COMMIT

def test_ws_metrics_v330_prometheus():
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    metrics_text = response.text
    assert "adk_memory_percent" in metrics_text
    assert "adk_total_tasks_started_total" in metrics_text

def test_ws_metrics_v330_version():
    client = TestClient(app)
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json()["version"] == APP_VERSION