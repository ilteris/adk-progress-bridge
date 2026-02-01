import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX

def test_network_connections_audit_tool_ws():
    """
    Verifies that the new network_connections_audit tool works over WebSocket.
    """
    client = TestClient(app)
    # The server expects api_key in query params if BRIDGE_API_KEY is set.
    # In tests, it's often not set, but we follow the pattern.
    with client.websocket_connect("/ws") as websocket:
        # 1. Handshake
        resp = websocket.receive_json()
        assert resp["type"] == "connected"

        # 2. Start network_connections_audit
        websocket.send_text(json.dumps({
            "type": "start",
            "tool_name": "network_connections_audit",
            "args": {"samples": 2},
            "request_id": "req-v674"
        }))
        
        resp = websocket.receive_json()
        assert resp["type"] == "task_started"
        call_id = resp["call_id"]

        # 3. Receive progress
        progress_events = []
        while True:
            resp = websocket.receive_json()
            if resp["type"] == "result":
                break
            if resp["type"] == "progress":
                progress_events.append(resp)
        
        assert len(progress_events) >= 2
        assert any("Sampling network connections" in p["payload"]["step"] for p in progress_events)
        assert resp["payload"]["status"] == "audit_complete"
        assert "final_connection_count" in resp["payload"]

def test_v674_metadata():
    """
    Verifies that the system reports correct v674 Supreme Apex metadata.
    """
    client = TestClient(app)
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "2.10.0"
    assert data["git_commit"] == "v674-supreme-apex-adele-verification"
    assert "v674 SUPREME APEX" in data["status"]