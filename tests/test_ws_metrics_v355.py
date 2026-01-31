import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_v355_health_metrics():
    """Verify v355 metrics are present in the health data."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    # Check version and apex
    assert data["version"] == "1.4.5"
    assert data["operational_apex"] == "THE SINGULARITY"
    
    # Check utilization percentages
    assert "process_resource_utilization_percent" in data
    assert "nofile" in data["process_resource_utilization_percent"]
    assert "as" in data["process_resource_utilization_percent"]
    
    assert isinstance(data["process_resource_utilization_percent"]["nofile"], float)
    assert isinstance(data["process_resource_utilization_percent"]["as"], float)

@pytest.mark.asyncio
async def test_v355_prometheus_metrics():
    """Verify v355 metrics are present in the /metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    assert "adk_process_resource_limit_nofile_utilization_percent" in content
    assert "adk_process_resource_limit_as_utilization_percent" in content

@pytest.mark.asyncio
async def test_ws_get_health_v355():
    """Verify v355 metrics are present in WebSocket get_health response."""
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({
            "type": "get_health",
            "request_id": "v355_test"
        })
        
        response = websocket.receive_json()
        assert response["type"] == "health_data"
        data = response["data"]
        
        assert "process_resource_utilization_percent" in data
        assert data["version"] == "1.4.5"
        assert data["operational_apex"] == "THE SINGULARITY"
