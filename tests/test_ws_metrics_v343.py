import pytest
from fastapi.testclient import TestClient
from backend.app.main import app, APP_VERSION, OPERATIONAL_APEX
import time

client = TestClient(app)

def test_v343_health_metrics():
    """Verify that v343 Beyond Singularity metrics are present in the /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    assert data["version"] == "1.3.3"
    assert data["operational_apex"] == "BEYOND SINGULARITY"
    
    # System CPU Beyond
    assert "system_cpu_usage" in data
    assert "iowait_percent" in data["system_cpu_usage"]
    assert "irq_percent" in data["system_cpu_usage"]
    assert "softirq_percent" in data["system_cpu_usage"]
    
    # System Memory Beyond
    assert "system_memory" in data
    assert "slab_bytes" in data["system_memory"]
    
    # Process Memory Beyond
    assert "process_memory_advanced" in data
    assert "lib_bytes" in data["process_memory_advanced"]
    assert "dirty_bytes" in data["process_memory_advanced"]
    
    # Process Env count
    assert "process_env_var_count" in data
    assert isinstance(data["process_env_var_count"], int)

def test_v343_prometheus_metrics():
    """Verify that v343 Beyond Singularity metrics are present in the /metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    # Check for Prometheus gauge definitions
    assert "adk_system_cpu_iowait_percent" in content
    assert "adk_system_cpu_irq_percent" in content
    assert "adk_system_cpu_softirq_percent" in content
    assert "adk_system_memory_slab_bytes" in content
    assert "adk_process_memory_lib_bytes" in content
    assert "adk_process_memory_dirty_bytes" in content
    assert "adk_process_env_var_count" in content

def test_v343_version_endpoint():
    """Verify the /version endpoint returns the new version and apex tier."""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1.3.3"
    assert data["status"] == "BEYOND SINGULARITY"
