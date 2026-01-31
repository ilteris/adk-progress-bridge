import pytest
from backend.app.main import app, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX, MAX_CONCURRENT_TASKS

import asyncio
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health_v340_ultimate_metrics():
    """Verify that v340 ultimate metrics are present in the health check response."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    assert data["version"] == APP_VERSION
    assert data["git_commit"] == GIT_COMMIT
    assert data["operational_apex"] == OPERATIONAL_APEX
    
    # Check v340 metrics
    assert "process_cpu_usage" in data
    assert "percent" in data["process_cpu_usage"]
    
    assert "network_io_total" in data
    assert "errin" in data["network_io_total"]
    assert "errout" in data["network_io_total"]
    assert "dropin" in data["network_io_total"]
    assert "dropout" in data["network_io_total"]
    
    assert "system_memory" in data
    assert "active_bytes" in data["system_memory"]
    assert "inactive_bytes" in data["system_memory"]
    
    # Check v339 metrics (regression check)
    assert "system_swap_memory" in data
    assert "used_bytes" in data["system_swap_memory"]
    assert "free_bytes" in data["system_swap_memory"]
    
    assert "process_io_counters" in data
    assert "read_bytes" in data["process_io_counters"]
    assert "write_bytes" in data["process_io_counters"]
    assert "read_count" in data["process_io_counters"]
    assert "write_count" in data["process_io_counters"]

def test_prometheus_v340_metrics():
    """Verify that v340 metrics are present in the Prometheus /metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    # v340 metrics
    assert "adk_process_cpu_percent_total" in content
    assert "adk_system_network_errors_in_total" in content
    assert "adk_system_network_errors_out_total" in content
    assert "adk_system_network_drops_in_total" in content
    assert "adk_system_network_drops_out_total" in content
    assert "adk_system_memory_active_bytes" in content
    assert "adk_system_memory_inactive_bytes" in content
    
    # v339 metrics
    assert "adk_system_swap_used_bytes" in content
    assert "adk_system_swap_free_bytes" in content
    assert "adk_process_io_read_bytes_total" in content
    assert "adk_process_io_write_bytes_total" in content
    assert "adk_process_io_read_count_total" in content
    assert "adk_process_io_write_count_total" in content