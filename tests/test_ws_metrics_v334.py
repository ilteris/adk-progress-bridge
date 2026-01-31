
import pytest
import time
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_v334_metrics():
    """Verify that v334 supreme metrics are present in health check."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    # Version checks
    assert data["version"] == "1.2.4"
    assert data["git_commit"] == "v334-supreme"
    
    # New metrics in v334
    assert "disk_usage_percent" in data
    assert "system_memory_available_bytes" in data
    assert "page_faults" in data
    assert "minor" in data["page_faults"]
    assert "major" in data["page_faults"]
    
    # Verify types
    assert isinstance(data["disk_usage_percent"], (int, float))
    assert isinstance(data["system_memory_available_bytes"], int)
    assert isinstance(data["page_faults"]["minor"], int)
    assert isinstance(data["page_faults"]["major"], int)

def test_prometheus_v334_metrics():
    """Verify that v334 supreme metrics are present in Prometheus /metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    assert "adk_disk_usage_percent" in content
    assert "adk_system_memory_available_bytes" in content
    assert "adk_page_faults_minor" in content
    assert "adk_page_faults_major" in content
    
    # Verify build info
    assert 'adk_build_info{git_commit="v334-supreme",version="1.2.4"}' in content

def test_version_v334():
    """Verify version endpoint."""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1.2.4"
    assert data["git_commit"] == "v334-supreme"
