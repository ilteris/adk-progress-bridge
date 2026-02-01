import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX

def test_memory_leak_audit_tool_ws():
    """
    Verifies that the new memory_leak_audit tool works over WebSocket.
    """
    client = TestClient(app)
    # The server expects api_key in query params if BRIDGE_API_KEY is set.
    # In tests, it's often not set, but we follow the pattern.
    with client.websocket_connect("/ws") as websocket:
        # 1. Handshake
        resp = websocket.receive_json()
        assert resp["type"] == "connected"

        # 2. Start memory_leak_audit
        websocket.send_text(json.dumps({
            "type": "start",
            "tool_name": "memory_leak_audit",
            "args": {"samples": 2},
            "request_id": "req-v605"
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
        assert any("Sampling memory usage" in p["payload"]["step"] for p in progress_events)
        assert resp["payload"]["status"] == "audit_complete"
        assert "baseline_rss" in resp["payload"]
        assert "final_rss" in resp["payload"]

def test_v605_metadata():
    """
    Verifies that the system reports correct v605 Supreme Apex metadata.
    """
    client = TestClient(app)
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "2.3.1"
    assert data["git_commit"] == "v605-supreme-apex-adele-verification"
    assert "v605 SUPREME APEX" in data["status"]
