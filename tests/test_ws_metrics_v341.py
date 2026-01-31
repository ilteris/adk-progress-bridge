import pytest
from fastapi.testclient import TestClient
from backend.app.main import app, APP_VERSION, OPERATIONAL_APEX
import time

client = TestClient(app)

def test_v341_health_metrics():
    """Verify that v341 God Tier metrics are present in the /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    assert data["version"] == APP_VERSION
    assert data["operational_apex"] == OPERATIONAL_APEX
    
    # System CPU Stats
    assert "system_cpu_stats" in data
    assert "interrupts" in data["system_cpu_stats"]
    assert "soft_interrupts" in data["system_cpu_stats"]
    assert "syscalls" in data["system_cpu_stats"]
    
    # Process Memory Advanced
    assert "process_memory_advanced" in data
    assert "shared_bytes" in data["process_memory_advanced"]
    assert "text_bytes" in data["process_memory_advanced"]
    assert "data_bytes" in data["process_memory_advanced"]
    
    # Process Num Threads
    assert "process_num_threads" in data
    assert isinstance(data["process_num_threads"], int)

def test_v341_prometheus_metrics():
    """Verify that v341 God Tier metrics are present in the /metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    # Check for Prometheus gauge definitions
    assert "adk_system_cpu_interrupts_total" in content
    assert "adk_system_cpu_soft_interrupts_total" in content
    assert "adk_system_cpu_syscalls_total" in content
    assert "adk_process_memory_shared_bytes" in content
    assert "adk_process_memory_text_bytes" in content
    assert "adk_process_memory_data_bytes" in content
    assert "adk_process_num_threads" in content

def test_v341_version_endpoint():
    """Verify the /version endpoint returns the new version and apex tier."""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == APP_VERSION
    assert data["status"] == OPERATIONAL_APEX