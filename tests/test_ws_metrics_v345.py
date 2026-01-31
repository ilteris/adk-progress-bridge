import pytest
import time
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_v345_omnipotence():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    assert data["version"] >= "1.3.5"
    
    # Check new metrics
    assert "context_switches" in data["system_cpu_stats"]
    assert "system_network_connections_count" in data
    assert "affinity_count" in data["process_cpu_usage"]
    assert "total" in data["page_faults"]
    
    # Check values (should be numbers)
    assert isinstance(data["system_cpu_stats"]["context_switches"], (int, float))
    assert isinstance(data["system_network_connections_count"], int)
    assert isinstance(data["process_cpu_usage"]["affinity_count"], int)
    assert isinstance(data["page_faults"]["total"], (int, float))

def test_metrics_v345_omnipotence():
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    assert "adk_system_cpu_context_switches_total" in content
    assert "adk_system_network_connections_count" in content
    assert "adk_process_cpu_affinity_count" in content
    assert "adk_process_memory_page_faults_total" in content
    assert 'adk_build_info{' in content
    assert 'version="1.3.' in content

def test_version_v345():
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] >= "1.3.5"