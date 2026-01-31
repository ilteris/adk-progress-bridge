import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_v356_health_metrics():
    """Verify v356 metrics are present in the health data."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    # Check version and apex
    assert data["version"] >= "1.4.6"
    assert data["operational_apex"] in ["THE OMEGA", "THE OVERLORD"]
    
    # Check process IO throughput
    assert "process_io_counters" in data
    assert "read_throughput_bps" in data["process_io_counters"]
    assert "write_throughput_bps" in data["process_io_counters"]
    
    assert isinstance(data["process_io_counters"]["read_throughput_bps"], (int, float))
    assert isinstance(data["process_io_counters"]["write_throughput_bps"], (int, float))

@pytest.mark.asyncio
async def test_v356_prometheus_metrics():
    """Verify v356 metrics are present in the /metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    assert "adk_process_io_read_throughput_bps" in content
    assert "adk_process_io_write_throughput_bps" in content

@pytest.mark.asyncio
async def test_ws_get_health_v356():
    """Verify v356 metrics are present in WebSocket get_health response."""
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({
            "type": "get_health",
            "request_id": "v356_test"
        })
        
        response = websocket.receive_json()
        assert response["type"] == "health_data"
        data = response["data"]
        
        assert "process_io_counters" in data
        assert data["process_io_counters"]["read_throughput_bps"] >= 0
        assert data["version"] >= "1.4.6"
        assert data["operational_apex"] in ["THE OMEGA", "THE OVERLORD"]