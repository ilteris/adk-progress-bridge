import pytest
import asyncio
import json
import pytest_asyncio
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_v353_health_metrics():
    """Verify v353 metrics are present in the health data."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    # Check CPU cores
    assert "cores" in data["system_cpu_usage"]
    assert isinstance(data["system_cpu_usage"]["cores"], list)
    
    # Check disk partitions
    assert "partitions_usage_percent" in data["disk_io_total"]
    assert isinstance(data["disk_io_total"]["partitions_usage_percent"], dict)
    
    # Check network interfaces
    assert "per_interface" in data["network_io_total"]
    assert isinstance(data["network_io_total"]["per_interface"], dict)

@pytest.mark.asyncio
async def test_v353_prometheus_metrics():
    """Verify v353 metrics are present in the /metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    assert "adk_system_cpu_cores_usage_percent" in content
    assert "adk_system_disk_partitions_usage_percent" in content
    assert "adk_system_network_interfaces_bytes_sent_total" in content
    assert "adk_system_network_interfaces_bytes_recv_total" in content

@pytest.mark.asyncio
async def test_ws_get_health_v353():
    """Verify v353 metrics are present in WebSocket get_health response."""
    with client.websocket_connect("/ws") as websocket:
        # Auth usually handled by verify_api_key_ws which might be mocked or using a key
        # In test environment, we might need to skip auth or provide a key
        websocket.send_json({
            "type": "get_health",
            "request_id": "v353_test"
        })
        
        response = websocket.receive_json()
        assert response["type"] == "health_data"
        assert response["request_id"] == "v353_test"
        data = response["data"]
        
        assert "cores" in data["system_cpu_usage"]
        assert "partitions_usage_percent" in data["disk_io_total"]
        assert "per_interface" in data["network_io_total"]
