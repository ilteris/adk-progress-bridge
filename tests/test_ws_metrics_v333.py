import pytest
from backend.app.main import app, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX, MAX_CONCURRENT_TASKS

from fastapi.testclient import TestClient

import time

def test_health_v333_metrics():
    """Verify that v333 specific metrics are present in health check."""
    with TestClient(app) as client:
        # First call to initialize throughput
        client.get("/health")
        time.sleep(1.1) # Wait for throughput window
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        
        assert data["version"] == APP_VERSION
        assert "git_commit" in data
        
        # Check for throughput
        assert "ws_throughput_bps" in data
        assert "received" in data["ws_throughput_bps"]
        assert "sent" in data["ws_throughput_bps"]
        
        # Check for context switches
        assert "context_switches" in data
        assert "voluntary" in data["context_switches"]
        assert "involuntary" in data["context_switches"]
        
        # Check for task success rate
        assert "task_success_rate_percent" in data
        assert isinstance(data["task_success_rate_percent"], (int, float))

def test_prometheus_v333_metrics():
    """Verify that v333 metrics are exposed in Prometheus format."""
    with TestClient(app) as client:
        response = client.get("/metrics")
        assert response.status_code == 200
        content = response.text
        
        assert "adk_ws_throughput_received_bps" in content
        assert "adk_ws_throughput_sent_bps" in content
        assert "adk_context_switches_voluntary" in content
        assert "adk_context_switches_involuntary" in content
        assert f'adk_build_info{{git_commit="{GIT_COMMIT}",version="{APP_VERSION}"}}' in content

def test_version_v333():
    """Verify version endpoint returns v333 information."""
    with TestClient(app) as client:
        response = client.get("/version")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == APP_VERSION
        assert "git_commit" in data
