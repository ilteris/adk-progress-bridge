import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_v349_enlightenment():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    assert data["version"] == "1.3.9"
    assert data["operational_apex"] == "ENLIGHTENMENT"
    
    # v349 Enlightenment metrics
    assert "process_cpu_usage" in data
    assert "children_user_seconds" in data["process_cpu_usage"]
    assert "children_system_seconds" in data["process_cpu_usage"]
    assert "network_io_total" in data
    assert "interfaces_down_count" in data["network_io_total"]
    assert "disk_io_total" in data
    assert "read_merged_count" in data["disk_io_total"]
    assert "write_merged_count" in data["disk_io_total"]
    
    # Check types
    assert isinstance(data["process_cpu_usage"]["children_user_seconds"], (int, float))
    assert isinstance(data["network_io_total"]["interfaces_down_count"], int)
    assert isinstance(data["disk_io_total"]["read_merged_count"], int)

def test_metrics_v349_enlightenment():
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    assert "adk_process_cpu_times_children_user_seconds" in content
    assert "adk_process_cpu_times_children_system_seconds" in content
    assert "adk_system_network_interfaces_down_count" in content
    assert "adk_system_disk_read_merged_count_total" in content
    assert "adk_system_disk_write_merged_count_total" in content

def test_version_v349():
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1.3.9"
    assert data["status"] == "ENLIGHTENMENT"
    assert data["git_commit"] == "v349-enlightenment"
