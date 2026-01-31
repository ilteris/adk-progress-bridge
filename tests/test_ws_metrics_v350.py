import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_v350_apotheosis():
    """Verify Apotheosis tier metrics in health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    assert data["version"] >= "1.4.0"
    assert len(data["operational_apex"]) > 0
    
    # v350 Metrics
    assert "system_memory" in data
    assert "shared_bytes" in data["system_memory"]
    assert "process_memory_advanced" in data
    assert "pss_bytes" in data["process_memory_advanced"]
    assert "swap_bytes" in data["process_memory_advanced"]
    assert "network_io_total" in data
    assert "mtu_total" in data["network_io_total"]
    assert "errors_total" in data["network_io_total"]

def test_prometheus_v350_metrics():
    """Verify Apotheosis tier metrics in Prometheus."""
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    assert "adk_system_memory_shared_bytes" in content
    assert "adk_process_memory_pss_bytes" in content
    assert "adk_system_network_interfaces_mtu_total" in content
    assert "adk_process_memory_swap_bytes" in content
    assert "adk_system_network_errors_total" in content

def test_version_v350():
    """Verify Apotheosis status in version endpoint."""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] >= "1.4.0"
    assert len(data["status"]) > 0
