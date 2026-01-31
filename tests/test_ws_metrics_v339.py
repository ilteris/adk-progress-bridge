import pytest
import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_v339_new_metrics():
    """Verify that v339 new metrics are present in the health check response."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    assert data["version"] == "1.2.9"
    assert data["git_commit"] == "v339-omega-plus-ultra"
    assert data["operational_apex"] == "SUPREME ABSOLUTE APEX OMEGA ULTRA"
    
    # Check v339 metrics
    assert "system_swap_memory" in data
    assert "used_bytes" in data["system_swap_memory"]
    assert "free_bytes" in data["system_swap_memory"]
    
    assert "process_io_counters" in data
    assert "read_bytes" in data["process_io_counters"]
    assert "write_bytes" in data["process_io_counters"]
    assert "read_count" in data["process_io_counters"]
    assert "write_count" in data["process_io_counters"]
    
    # Check v338 metrics (regression check)
    assert "system_cpu_usage" in data
    assert "idle_percent" in data["system_cpu_usage"]
    assert "process_cpu_usage" in data
    assert "user_seconds" in data["process_cpu_usage"]
    assert "system_seconds" in data["process_cpu_usage"]
    assert "system_memory" in data
    assert "used_bytes" in data["system_memory"]
    assert "free_bytes" in data["system_memory"]
    assert "system_network_packets" in data
    assert "sent" in data["system_network_packets"]
    assert "recv" in data["system_network_packets"]

def test_prometheus_v339_metrics():
    """Verify that v339 metrics are present in the Prometheus /metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    # v339 metrics
    assert "adk_system_swap_used_bytes" in content
    assert "adk_system_swap_free_bytes" in content
    assert "adk_process_io_read_bytes_total" in content
    assert "adk_process_io_write_bytes_total" in content
    assert "adk_process_io_read_count_total" in content
    assert "adk_process_io_write_count_total" in content
    
    # v338 metrics
    assert "adk_system_cpu_usage_idle_percent" in content
    assert "adk_process_cpu_usage_user_seconds" in content
    assert "adk_process_cpu_usage_system_seconds" in content
    assert "adk_system_memory_used_bytes" in content
    assert "adk_system_memory_free_bytes" in content
    assert "adk_system_network_packets_sent_total" in content
    assert "adk_system_network_packets_recv_total" in content
