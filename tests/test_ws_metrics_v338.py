import pytest
from backend.app.main import app, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX, MAX_CONCURRENT_TASKS

from fastapi.testclient import TestClient

client = TestClient(app)

def test_v338_metrics_in_prometheus_format():
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    # Check for v338 Supreme Apex Ultra Millennium Omega Plus metrics
    assert "adk_system_cpu_usage_idle_percent" in content
    assert "adk_process_cpu_usage_user_seconds" in content
    assert "adk_process_cpu_usage_system_seconds" in content
    assert "adk_system_memory_used_bytes" in content
    assert "adk_system_memory_free_bytes" in content
    assert "adk_system_network_packets_sent_total" in content
    assert "adk_system_network_packets_recv_total" in content

def test_v338_metrics_in_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    assert data["version"] == APP_VERSION
    assert data["git_commit"] == GIT_COMMIT
    assert data["operational_apex"] == OPERATIONAL_APEX
    
    # Check v338 specific fields
    assert "system_cpu_idle_percent" in data
    assert "process_cpu_usage" in data
    assert "user_seconds" in data["process_cpu_usage"]
    assert "system_seconds" in data["process_cpu_usage"]
    assert "system_memory_extended" in data
    assert "used_bytes" in data["system_memory_extended"]
    assert "free_bytes" in data["system_memory_extended"]
    assert "system_network_packets" in data
    assert "sent" in data["system_network_packets"]
    assert "recv" in data["system_network_packets"]

def test_v338_version_endpoint():
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == APP_VERSION
    assert data["git_commit"] == GIT_COMMIT
