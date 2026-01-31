import pytest
from fastapi.testclient import TestClient
from backend.app.main import app, APP_VERSION, OPERATIONAL_APEX
import time

client = TestClient(app)

def test_v342_health_metrics():
    """Verify that v342 Ascension Singularity metrics are present in the /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    assert data["version"] == APP_VERSION
    assert data["operational_apex"] == OPERATIONAL_APEX
    
    # System CPU Advanced
    assert "system_cpu_usage" in data
    assert "steal_percent" in data["system_cpu_usage"]
    assert "guest_percent" in data["system_cpu_usage"]
    
    # System Memory Advanced
    assert "system_memory" in data
    assert "buffers_bytes" in data["system_memory"]
    assert "cached_bytes" in data["system_memory"]
    
    # Process Children
    assert "process_children_count" in data
    assert isinstance(data["process_children_count"], int)

def test_v342_prometheus_metrics():
    """Verify that v342 Ascension Singularity metrics are present in the /metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    # Check for Prometheus gauge definitions
    assert "adk_system_cpu_steal_percent" in content
    assert "adk_system_cpu_guest_percent" in content
    assert "adk_system_memory_buffers_bytes" in content
    assert "adk_system_memory_cached_bytes" in content
    assert "adk_system_disk_partitions_count" in content
    assert "adk_system_users_count" in content
    assert "adk_process_children_count" in content

def test_v342_version_endpoint():
    """Verify the /version endpoint returns the new version and apex tier."""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == APP_VERSION
    assert data["status"] == OPERATIONAL_APEX

def test_v342_system_users_advanced():
    """Verify system users and disk partitions count are reported correctly."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    assert "system_users_count" in data
    assert isinstance(data["system_users_count"], int)
    assert "system_disk_partitions_count" in data
    assert isinstance(data["system_disk_partitions_count"], int)
    assert data["system_disk_partitions_count"] >= 0