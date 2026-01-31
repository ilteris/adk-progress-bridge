import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_v350_apotheosis():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    assert data["version"] == "1.4.0"
    assert data["operational_apex"] == "APOTHEOSIS"
    
    # v350 Apotheosis metrics in /health
    assert "system_memory" in data
    assert "shared_bytes" in data["system_memory"]
    
    assert "process_memory_advanced" in data
    assert "pss_bytes" in data["process_memory_advanced"]
    assert "swap_bytes" in data["process_memory_advanced"]
    
    assert "network_io_total" in data
    assert "mtu_total" in data["network_io_total"]
    assert "errors_total" in data["network_io_total"]
    
    # Check types
    assert isinstance(data["system_memory"]["shared_bytes"], int)
    assert isinstance(data["process_memory_advanced"]["pss_bytes"], int)
    assert isinstance(data["process_memory_advanced"]["swap_bytes"], int)
    assert isinstance(data["network_io_total"]["mtu_total"], int)
    assert isinstance(data["network_io_total"]["errors_total"], int)

def test_metrics_v350_apotheosis():
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    assert "adk_system_memory_shared_bytes" in content
    assert "adk_process_memory_pss_bytes" in content
    assert "adk_system_network_interfaces_mtu_total" in content
    assert "adk_process_memory_swap_bytes" in content
    assert "adk_system_network_errors_total" in content

def test_version_v350():
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1.4.0"
    assert data["status"] == "APOTHEOSIS"
    assert data["git_commit"] == "v350-apotheosis"
