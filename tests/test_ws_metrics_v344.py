import pytest
import time
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_v344_transcendence():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    # Version might be newer
    assert data["version"] >= "1.3.4"
    
    # Check new metrics
    assert "uss_bytes" in data["process_memory_advanced"]
    assert "wired_bytes" in data["system_memory"]
    assert "process_nice_value" in data
    assert "process_uptime_seconds" in data
    
    # Check values (should be numbers)
    assert isinstance(data["process_memory_advanced"]["uss_bytes"], (int, float))
    assert isinstance(data["system_memory"]["wired_bytes"], (int, float))
    assert isinstance(data["process_nice_value"], int)
    assert isinstance(data["process_uptime_seconds"], (int, float))

def test_metrics_v344_transcendence():
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    assert "adk_process_memory_uss_bytes" in content
    assert "adk_system_memory_wired_bytes" in content
    assert "adk_process_nice_value" in content
    assert "adk_process_uptime_seconds" in content
    # Flexible version check
    assert 'adk_build_info{' in content
    assert 'version="1.' in content

def test_version_v344():
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] >= "1.3.4"