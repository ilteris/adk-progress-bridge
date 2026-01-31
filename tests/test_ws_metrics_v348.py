import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_v348_nirvana():
    """Verify Nirvana tier metrics in health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    assert data["version"] >= "1.3.9"
    assert data["operational_apex"] in ["NIRVANA", "ENLIGHTENMENT", "APOTHEOSIS", "ULTIMA", "OMNIPRESENCE", "THE SOURCE", "THE ONE"]
    
    # v348 Metrics
    assert "system_disk_io_times_ms" in data
    assert "read_time" in data["system_disk_io_times_ms"]
    assert "write_time" in data["system_disk_io_times_ms"]
    assert "process_memory_maps_count" in data
    assert "system_network_interfaces_up_count" in data
    assert "process_context_switches_total" in data

def test_prometheus_v348_metrics():
    """Verify Nirvana tier metrics in Prometheus."""
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    assert "adk_system_disk_read_time_ms_total" in content
    assert "adk_system_disk_write_time_ms_total" in content
    assert "adk_process_memory_maps_count" in content
    assert "adk_system_network_interfaces_up_count" in content
    assert "adk_process_context_switches_total" in content

def test_version_v348():
    """Verify Nirvana status in version endpoint."""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] >= "1.3.9"
    assert data["status"] in ["NIRVANA", "ENLIGHTENMENT", "APOTHEOSIS", "ULTIMA", "OMNIPRESENCE", "THE SOURCE", "THE ONE"]