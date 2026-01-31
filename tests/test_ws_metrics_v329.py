import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from backend.app.main import app

def test_ws_metrics_v329_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "ws_bytes_received" in data
    assert "ws_bytes_sent" in data
    assert data["version"] == "1.1.9"
    assert data["git_commit"] == "v329-apex"

@pytest.mark.asyncio
async def test_ws_metrics_v329_execution():
    from backend.app.main import app
    from fastapi.testclient import TestClient
    
    # We use a real websocket client for this
    with TestClient(app).websocket_connect("/ws?api_key=dev-secret-key") as websocket:
        websocket.send_json({"type": "ping", "request_id": "r1"})
        data = websocket.receive_json()
        assert data["type"] == "pong"
        
        websocket.send_json({"type": "list_tools", "request_id": "r2"})
        data = websocket.receive_json()
        assert data["type"] == "tools_list"
    
    # Now check metrics
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    metrics_text = response.text
    
    assert "adk_ws_request_latency_seconds" in metrics_text
    assert "adk_ws_connection_duration_seconds" in metrics_text
    assert "adk_ws_bytes_received_total" in metrics_text
    assert "adk_ws_bytes_sent_total" in metrics_text
    
    # Check that bytes are greater than 0
    health_response = client.get("/health")
    health_data = health_response.json()
    assert health_data["ws_bytes_received"] > 0
    assert health_data["ws_bytes_sent"] > 0

def test_ws_metrics_v329_version():
    client = TestClient(app)
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json()["version"] == "1.1.9"
