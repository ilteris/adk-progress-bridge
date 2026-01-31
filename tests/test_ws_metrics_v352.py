import sys
import os
import json
import pytest
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app

@pytest.mark.asyncio
async def test_websocket_get_health_v352():
    """
    Tests that getting health data over WebSocket works in v352 OMNIPRESENCE.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        req_id = "health_req_v352"
        websocket.send_json({
            "type": "get_health",
            "request_id": req_id
        })
        
        data = websocket.receive_json()
        assert data["type"] == "health_data"
        assert "data" in data
        health = data["data"]
        assert health["status"] == "healthy"
        assert health["version"] >= "1.4.2"
        assert len(health["git_commit"]) > 0
        assert len(health["operational_apex"]) > 0
        assert data["request_id"] == req_id

        # Check for new v352 metrics
        assert "system_process_count" in health
        
        assert "system_cpu_usage" in health
        assert "load_1m_percent" in health["system_cpu_usage"]
        
        assert "system_memory" in health
        assert "available_percent" in health["system_memory"]
        
        assert "process_memory_advanced" in health
        assert "pss_percent" in health["process_memory_advanced"]

@pytest.mark.asyncio
async def test_prometheus_metrics_v352():
    """
    Tests that new v352 Prometheus metrics are present.
    """
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    assert "adk_system_process_count" in content
    assert "adk_process_memory_pss_percent" in content
    assert "adk_system_cpu_load_1m_percent" in content
    assert "adk_system_memory_available_percent" in content

@pytest.mark.asyncio
async def test_version_v352():
    """
    Tests that /version returns the correct v352 info.
    """
    client = TestClient(app)
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] >= "1.4.2"
    assert len(data["git_commit"]) > 0
    assert len(data["status"]) > 0