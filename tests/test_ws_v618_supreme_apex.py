import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX

def test_process_num_threads_audit_tool_ws():
    """
    Verifies that the new process_num_threads_audit tool (v660) works over WebSocket.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Handshake
        resp = websocket.receive_json()
        assert resp["type"] == "connected"

        # 2. Start process_num_threads_audit
        websocket.send_text(json.dumps({
            "type": "start",
            "tool_name": "process_num_threads_audit",
            "args": {"samples": 2},
            "request_id": "req-v660"
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
        assert any("Sampling thread count" in p["payload"]["step"] for p in progress_events)
        assert resp["payload"]["status"] == "audit_complete"
        assert "final_num_threads" in resp["payload"]

def test_v660_metadata():
    """
    Verifies that the system reports correct v660 Supreme Apex metadata.
    """
    client = TestClient(app)
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "2.8.6"
    assert data["git_commit"] == "v660-supreme-apex-adele-verification"
    assert "v660 SUPREME APEX" in data["status"]
