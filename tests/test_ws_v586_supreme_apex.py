import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app

def test_v669_metadata():
    client = TestClient(app)
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "2.9.5"
    assert data["status"] == "v669 SUPREME APEX VERIFICATION ADELE"
    assert data["git_commit"] == "v669-supreme-apex-adele-verification"

@pytest.mark.asyncio
async def test_v669_ws_health_metrics():
    # Verify that get_health via WS returns the correct metadata
    from backend.app.auth import BRIDGE_API_KEY
    api_key = BRIDGE_API_KEY or "test-key"
    
    with TestClient(app).websocket_connect(f"/ws?api_key={api_key}") as websocket:
        # Handshake
        resp = websocket.receive_json()
        assert resp["type"] == "connected"
        
        # Get Health
        websocket.send_json({"type": "get_health", "request_id": "v669-test"})
        resp = websocket.receive_json()
        assert resp["type"] == "health_data"
        assert resp["request_id"] == "v669-test"
        assert resp["data"]["version"] == "2.9.5"
        assert resp["data"]["operational_apex"] == "v669 SUPREME APEX VERIFICATION ADELE"

@pytest.mark.asyncio
async def test_v669_resource_monitor_tool():
    from backend.app.auth import BRIDGE_API_KEY
    api_key = BRIDGE_API_KEY or "test-key"
    
    with TestClient(app).websocket_connect(f"/ws?api_key={api_key}") as websocket:
        # Handshake
        websocket.receive_json()
        
        # Start resource_monitor
        websocket.send_json({
            "type": "start", 
            "tool_name": "resource_monitor", 
            "args": {"iterations": 2},
            "request_id": "v669-resource-test"
        })
        
        # task_started
        resp = websocket.receive_json()
        assert resp["type"] == "task_started"
        call_id = resp["call_id"]
        
        # Receive progress updates
        for _ in range(2):
            resp = websocket.receive_json()
            assert resp["type"] == "progress"
            assert resp["call_id"] == call_id
            assert "cpu_percent" in resp["payload"]["metadata"]
            
        # Receive result
        resp = websocket.receive_json()
        assert resp["type"] == "result"
        assert resp["payload"]["status"] == "complete"

def test_v669_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "2.9.5"
    assert "last_updated_str" in data
    assert "build_timestamp" in data
