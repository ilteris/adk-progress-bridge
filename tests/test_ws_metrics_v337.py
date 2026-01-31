import pytest
from fastapi.testclient import TestClient
from backend.app.main import app, APP_VERSION, GIT_COMMIT

client = TestClient(app)

def test_v337_metrics_in_prometheus_format():
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    # Check for v337 Supreme Apex Ultra Millennium Omega metrics
    assert "adk_system_load_5m" in content
    assert "adk_system_load_15m" in content
    assert "adk_process_memory_rss_bytes" in content
    assert "adk_process_memory_vms_bytes" in content
    assert "adk_system_memory_total_bytes" in content
    assert "adk_system_cpu_usage_user_percent" in content
    assert "adk_system_cpu_usage_system_percent" in content
    assert "adk_system_uptime_seconds" in content

def test_v337_metrics_in_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    assert data["version"] == APP_VERSION
    assert data["git_commit"] == GIT_COMMIT
    assert data["operational_apex"] == "SUPREME ABSOLUTE APEX OMEGA"
    
    # Check v337 specific fields
    assert "system_load_5m" in data
    assert "system_load_15m" in data
    assert "memory_rss_bytes" in data
    assert "memory_vms_bytes" in data
    assert "system_memory" in data
    assert "total_bytes" in data["system_memory"]
    assert "system_cpu_usage" in data
    assert "user_percent" in data["system_cpu_usage"]
    assert "system_percent" in data["system_cpu_usage"]
    assert "system_uptime_seconds" in data

def test_v337_version_endpoint():
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == APP_VERSION
    assert data["git_commit"] == GIT_COMMIT
    assert data["status"] == "SUPREME ABSOLUTE APEX OMEGA"
