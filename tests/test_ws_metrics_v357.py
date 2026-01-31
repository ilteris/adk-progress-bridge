import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_v357_health_metrics():
    """Verify v357 metrics are present in the health data."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    # Check version and apex
    assert data["version"] >= "1.4.7"
    assert len(data["operational_apex"]) > 0
    
    # Check system disk IO throughput
    assert "disk_io_total" in data
    assert "read_throughput_bps" in data["disk_io_total"]
    assert "write_throughput_bps" in data["disk_io_total"]
    
    # Check system network throughput
    assert "network_io_total" in data
    assert "read_throughput_bps" in data["network_io_total"]
    assert "write_throughput_bps" in data["network_io_total"]
    assert "recv_throughput_bps" in data["network_io_total"]
    assert "sent_throughput_bps" in data["network_io_total"]
    
    assert isinstance(data["disk_io_total"]["read_throughput_bps"], (int, float))
    assert isinstance(data["network_io_total"]["recv_throughput_bps"], (int, float))

@pytest.mark.asyncio
async def test_v357_prometheus_metrics():
    """Verify v357 metrics are present in the /metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    assert "adk_system_disk_read_throughput_bps" in content
    assert "adk_system_disk_write_throughput_bps" in content
    assert "adk_system_network_throughput_recv_bps" in content
    assert "adk_system_network_throughput_sent_bps" in content

@pytest.mark.asyncio
async def test_ws_get_health_v357():
    """Verify v357 metrics are present in WebSocket get_health response."""
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({
            "type": "get_health",
            "request_id": "v357_test"
        })
        
        response = websocket.receive_json()
        assert response["type"] == "health_data"
        data = response["data"]
        
        assert "disk_io_total" in data
        assert data["disk_io_total"]["read_throughput_bps"] >= 0
        assert "network_io_total" in data
        assert data["network_io_total"]["recv_throughput_bps"] >= 0
        
        assert data["version"] >= "1.4.7"
        assert len(data["operational_apex"]) > 0
