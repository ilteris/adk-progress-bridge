import pytest
import time
from fastapi.testclient import TestClient
from backend.app.main import app, APP_VERSION, GIT_COMMIT

client = TestClient(app)

def test_health_v335_metrics():
    """Verify that v335 supreme metrics are present in health check."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    # Version checks - Use imported constants for resilience
    assert data["version"] == APP_VERSION
    assert data["git_commit"] == GIT_COMMIT
    assert data["operational_apex"] == "SUPREME ABSOLUTE APEX OMEGA ULTRA"
    
    # New metrics in v335
    assert "cpu_count" in data
    assert "boot_time_seconds" in data
    assert "swap_memory_usage_percent" in data
    assert "network_io_total" in data
    assert "bytes_sent" in data["network_io_total"]
    assert "bytes_recv" in data["network_io_total"]
    
    # Verify types
    assert isinstance(data["cpu_count"], int)
    assert isinstance(data["boot_time_seconds"], (int, float))
    assert isinstance(data["swap_memory_usage_percent"], (int, float))
    assert isinstance(data["network_io_total"]["bytes_sent"], int)
    assert isinstance(data["network_io_total"]["bytes_recv"], int)

def test_prometheus_v335_metrics():
    """Verify that v335 supreme metrics are present in Prometheus /metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    assert "adk_system_cpu_count" in content
    assert "adk_system_boot_time_seconds" in content
    assert "adk_swap_memory_usage_percent" in content
    assert "adk_system_network_bytes_sent" in content
    assert "adk_system_network_bytes_recv" in content
    
    # Verify build info - Use imported constants for resilience
    assert f'adk_build_info{{git_commit="{GIT_COMMIT}",version="{APP_VERSION}"}}' in content

def test_version_v335():
    """Verify version endpoint."""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == APP_VERSION
    assert data["git_commit"] == GIT_COMMIT
    assert data["status"] == "SUPREME ABSOLUTE APEX OMEGA ULTRA"