import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX

def test_process_memory_percent_audit_tool_ws():
    """
    Verifies that the process_memory_percent_audit tool (v620) works over WebSocket.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Handshake
        resp = websocket.receive_json()
        assert resp["type"] == "connected"

        # 2. Start process_memory_percent_audit
        websocket.send_text(json.dumps({
            "type": "start",
            "tool_name": "process_memory_percent_audit",
            "args": {"samples": 2},
            "request_id": "req-v620"
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
        assert any("Sampling memory percent" in p["payload"]["step"] for p in progress_events)
        assert resp["payload"]["status"] == "audit_complete"
        assert "final_memory_percent" in resp["payload"]

def test_v620_metadata_baseline():
    """
    Verifies the metadata baseline for v620.
    Note: We've moved to v620 in the current code, but we check if the baseline tools are present.
    """
    client = TestClient(app)
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    # If we are in v620 session, version will be 2.5.3
    assert data["version"] == "2.5.3"
