import pytest
import time
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_v346_deification():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    assert data["version"] == "1.3.6"
    assert data["git_commit"] == "v346-deification"
    assert data["operational_apex"] == "DEIFICATION"
    
    # Check new metrics
    assert "read_count" in data["disk_io_total"]
    assert "write_count" in data["disk_io_total"]
    assert "sin_bytes" in data["system_swap_memory"]
    assert "sout_bytes" in data["system_swap_memory"]
    assert "vms_percent" in data["process_memory_advanced"]
    assert "cpu_physical_count" in data
    
    # Check values (should be numbers)
    assert isinstance(data["disk_io_total"]["read_count"], int)
    assert isinstance(data["disk_io_total"]["write_count"], int)
    assert isinstance(data["system_swap_memory"]["sin_bytes"], int)
    assert isinstance(data["system_swap_memory"]["sout_bytes"], int)
    assert isinstance(data["process_memory_advanced"]["vms_percent"], (int, float))
    assert isinstance(data["cpu_physical_count"], int)

def test_metrics_v346_deification():
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    assert "adk_system_disk_read_count_total" in content
    assert "adk_system_disk_write_count_total" in content
    assert "adk_system_swap_in_bytes_total" in content
    assert "adk_system_swap_out_bytes_total" in content
    assert "adk_process_memory_vms_percent" in content
    assert "adk_system_cpu_physical_count" in content
    assert 'adk_build_info{git_commit="v346-deification",version="1.3.6"}' in content

def test_version_v346():
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1.3.6"
    assert data["status"] == "DEIFICATION"
