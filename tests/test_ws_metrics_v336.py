import pytest
from backend.app.main import app, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX, MAX_CONCURRENT_TASKS

import time
import os
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health_v336_metrics():
    """Verify that v336 supreme apex ultra millennium metrics are present in health check."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    # Version checks
    assert data["version"] == APP_VERSION
    assert data["git_commit"] == GIT_COMMIT
    assert data["operational_apex"] == OPERATIONAL_APEX
    
    # New metrics in v336
    assert "cpu_frequency_current_mhz" in data
    assert "disk_io_total" in data
    assert "read_bytes" in data["disk_io_total"]
    assert "write_bytes" in data["disk_io_total"]
    assert "process_connections_count" in data
    assert "system_load_1m" in data
    
    # Verify types
    assert isinstance(data["cpu_frequency_current_mhz"], (int, float))
    assert isinstance(data["disk_io_total"]["read_bytes"], int)
    assert isinstance(data["disk_io_total"]["write_bytes"], int)
    assert isinstance(data["process_connections_count"], int)
    assert isinstance(data["system_load_1m"], (int, float))

def test_prometheus_v336_metrics():
    """Verify that v336 metrics are present in Prometheus /metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    assert "adk_system_cpu_frequency_current_mhz" in content
    assert "adk_system_disk_read_bytes_total" in content
    assert "adk_system_disk_write_bytes_total" in content
    assert "adk_process_connections_count" in content
    assert "adk_system_load_1m" in content
    
    # Verify build info
    assert f'adk_build_info{{git_commit="{GIT_COMMIT}",version="{APP_VERSION}"}}' in content

def test_version_v336():
    """Verify version endpoint."""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == APP_VERSION
    assert data["git_commit"] == GIT_COMMIT
    assert data["status"] == OPERATIONAL_APEX
