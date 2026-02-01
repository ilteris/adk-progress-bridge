import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app

def test_v672_metadata():
    client = TestClient(app)
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "2.9.8"
    assert data["status"] == "v672 SUPREME APEX VERIFICATION ADELE"
    assert data["git_commit"] == "v672-supreme-apex-adele-verification"

@pytest.mark.asyncio
async def test_v672_ws_health_metrics():
    # Verify that get_health via WS returns the correct metadata
    from backend.app.auth import BRIDGE_API_KEY
    
    # Use BRIDGE_API_KEY if it's set, otherwise use "test-key" or similar if the app defaults to something
    api_key = BRIDGE_API_KEY or "test-key"
    
    with TestClient(app).websocket_connect(f"/ws?api_key={api_key}") as websocket:
        # Handshake
        resp = websocket.receive_json()
        assert resp["type"] == "connected"
        
        # Get Health
        websocket.send_json({"type": "get_health", "request_id": "v672-test"})
        resp = websocket.receive_json()
        assert resp["type"] == "health_data"
        assert resp["request_id"] == "v672-test"
        assert resp["data"]["version"] == "2.9.8"
        assert resp["data"]["operational_apex"] == "v672 SUPREME APEX VERIFICATION ADELE"

def test_v672_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "2.9.8"
    assert "last_updated_str" in data
    assert "build_timestamp" in data