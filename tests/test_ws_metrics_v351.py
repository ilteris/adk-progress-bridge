import sys
import os
import json
import pytest
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app

@pytest.mark.asyncio
async def test_websocket_get_health():
    """
    Tests that getting health data over WebSocket works in v351 ULTIMA and beyond.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        req_id = "health_req_1"
        websocket.send_json({
            "type": "get_health",
            "request_id": req_id
        })
        
        data = websocket.receive_json()
        assert data["type"] == "health_data"
        assert "data" in data
        health = data["data"]
        assert health["status"] == "healthy"
        assert health["version"] >= "1.4.1"
        assert data["request_id"] == req_id

        # Check for new v351 metrics in the nested structure
        assert "network_io_total" in health
        assert "speed_total_mbps" in health["network_io_total"]
        assert "duplex_full_count" in health["network_io_total"]
        
        assert "process_memory_advanced" in health
        assert "uss_percent" in health["process_memory_advanced"]

@pytest.mark.asyncio
async def test_prometheus_metrics_v351():
    """
    Tests that new v351 Prometheus metrics are present.
    """
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    assert "adk_system_network_interfaces_speed_total_mbps" in content
    assert "adk_system_network_interfaces_duplex_full_count" in content
    assert "adk_process_memory_uss_percent" in content

@pytest.mark.asyncio
async def test_version_v351():
    """
    Tests that /version returns the correct info.
    """
    client = TestClient(app)
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] >= "1.4.1"
    assert "status" in data