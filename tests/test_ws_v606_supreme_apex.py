import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX

def test_swap_memory_audit_tool_ws():
    """
    Verifies that the new swap_memory_audit tool works over WebSocket.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Handshake
        resp = websocket.receive_json()
        assert resp["type"] == "connected"

        # 2. Start swap_memory_audit
        websocket.send_text(json.dumps({
            "type": "start",
            "tool_name": "swap_memory_audit",
            "args": {"samples": 2},
            "request_id": "req-v666"
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
        assert any("Sampling swap memory" in p["payload"]["step"] for p in progress_events)
        assert resp["payload"]["status"] == "audit_complete"
        assert "final_percent" in resp["payload"]

def test_v666_metadata():
    """
    Verifies that the system reports correct v666 Supreme Apex metadata.
    """
    client = TestClient(app)
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "2.9.2"
    assert data["git_commit"] == "v666-supreme-apex-adele-verification"
    assert "v666 SUPREME APEX" in data["status"]
