import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX

def test_process_cmdline_audit_tool_ws():
    """
    Verifies that the new process_cmdline_audit tool works over WebSocket.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Handshake
        resp = websocket.receive_json()
        assert resp["type"] == "connected"

        # 2. Start process_cmdline_audit
        websocket.send_text(json.dumps({
            "type": "start",
            "tool_name": "process_cmdline_audit",
            "args": {"samples": 2},
            "request_id": "req-v663"
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
        assert any("Sampling process command line" in p["payload"]["step"] for p in progress_events)
        assert resp["payload"]["status"] == "audit_complete"
        assert "final_cmdline" in resp["payload"]

def test_v663_metadata():
    """
    Verifies that the system reports correct v663 Supreme Apex metadata.
    """
    client = TestClient(app)
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "2.8.9"
    assert data["git_commit"] == "v663-supreme-apex-adele-verification"
    assert "v663 SUPREME APEX" in data["status"]
