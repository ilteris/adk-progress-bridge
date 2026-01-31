import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_v354_health_metrics():
    """Verify v354 metrics are present in the health data."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    # Check load percentages
    assert "load_5m_percent" in data["system_cpu_usage"]
    assert "load_15m_percent" in data["system_cpu_usage"]
    
    # Check resource limits
    assert "process_resource_limits" in data
    assert "nofile_soft" in data["process_resource_limits"]
    assert "nofile_hard" in data["process_resource_limits"]

@pytest.mark.asyncio
async def test_v354_prometheus_metrics():
    """Verify v354 metrics are present in the /metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    assert "adk_system_load_5m_percent" in content
    assert "adk_system_load_15m_percent" in content
    assert "adk_process_resource_limit_nofile_soft" in content
    assert "adk_process_resource_limit_nofile_hard" in content

@pytest.mark.asyncio
async def test_ws_get_health_v354():
    """Verify v354 metrics are present in WebSocket get_health response."""
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({
            "type": "get_health",
            "request_id": "v354_test"
        })
        
        response = websocket.receive_json()
        assert response["type"] == "health_data"
        data = response["data"]
        
        assert "load_5m_percent" in data["system_cpu_usage"]
        assert "process_resource_limits" in data
