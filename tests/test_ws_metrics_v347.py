import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_v347_metrics():
    """Verify that the new v347 metrics are present in the health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    assert data["version"] >= "1.3.9"
    
    # v347 Metrics
    assert "system_memory" in data
    assert "percent" in data["system_memory"]
    assert "process_open_files_count" in data
    assert "disk_io_total" in data
    assert "busy_time_ms" in data["disk_io_total"]
    assert "network_io_total" in data
    assert "interfaces_count" in data["network_io_total"]
    assert "process_threads_cpu_usage" in data
    assert "total_user_seconds" in data["process_threads_cpu_usage"]
    assert "total_system_seconds" in data["process_threads_cpu_usage"]
    
    # Check they are numbers
    assert isinstance(data["system_memory"]["percent"], (int, float))
    assert isinstance(data["process_open_files_count"], int)
    assert isinstance(data["disk_io_total"]["busy_time_ms"], int)
    assert isinstance(data["network_io_total"]["interfaces_count"], int)
    assert isinstance(data["process_threads_cpu_usage"]["total_user_seconds"], (int, float))

def test_prometheus_v347_metrics():
    """Verify that the new v347 metrics are exported to Prometheus."""
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    assert "adk_system_memory_percent" in content
    assert "adk_process_open_files_count" in content
    assert "adk_system_disk_busy_time_ms_total" in content
    assert "adk_system_network_interfaces_count" in content
    assert "adk_process_threads_total_time_user_seconds" in content
    assert "adk_process_threads_total_time_system_seconds" in content

def test_version_v347():
    """Verify version and singularity status."""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] >= "1.3.9"
    assert data["status"] in ["NIRVANA", "SINGULARITY ASCENSION", "SINGULARITY", "ENLIGHTENMENT", "APOTHEOSIS", "ULTIMA", "OMNIPRESENCE", "THE SOURCE", "THE ONE", "THE SINGULARITY", "THE OMEGA"]
