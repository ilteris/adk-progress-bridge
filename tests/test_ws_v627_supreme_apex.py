import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX

def test_process_terminal_audit_tool_ws():
    """
    Verifies that the new process_terminal_audit tool works over WebSocket.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Handshake
        resp = websocket.receive_json()
        assert resp["type"] == "connected"

        # 2. Start process_terminal_audit
        websocket.send_text(json.dumps({
            "type": "start",
            "tool_name": "process_terminal_audit",
            "args": {"samples": 2},
            "request_id": "req-v650-terminal"
        }))
        
        resp = websocket.receive_json()
        assert resp["type"] == "task_started"

        # 3. Receive progress
        while True:
            resp = websocket.receive_json()
            if resp["type"] == "result":
                break
        
        assert resp["payload"]["status"] == "audit_complete"
        assert "final_terminal" in resp["payload"]

def test_process_ionice_extended_audit_tool_ws():
    """
    Verifies that the new process_ionice_extended_audit tool works over WebSocket.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Handshake
        resp = websocket.receive_json()
        assert resp["type"] == "connected"

        # 2. Start process_ionice_extended_audit
        websocket.send_text(json.dumps({
            "type": "start",
            "tool_name": "process_ionice_extended_audit",
            "args": {"samples": 2},
            "request_id": "req-v650-ionice"
        }))
        
        resp = websocket.receive_json()
        assert resp["type"] == "task_started"

        # 3. Receive progress
        while True:
            resp = websocket.receive_json()
            if resp["type"] == "result":
                break
        
        assert resp["payload"]["status"] == "audit_complete"
        assert "final_ionice" in resp["payload"]

def test_process_rlimit_audit_tool_ws():
    """
    Verifies that the new process_rlimit_audit tool works over WebSocket.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Handshake
        resp = websocket.receive_json()
        assert resp["type"] == "connected"

        # 2. Start process_rlimit_audit
        websocket.send_text(json.dumps({
            "type": "start",
            "tool_name": "process_rlimit_audit",
            "args": {"samples": 2},
            "request_id": "req-v650-rlimit"
        }))
        
        resp = websocket.receive_json()
        assert resp["type"] == "task_started"

        # 3. Receive progress
        while True:
            resp = websocket.receive_json()
            if resp["type"] == "result":
                break
        
        assert resp["payload"]["status"] == "audit_complete"
        assert "limits_count" in resp["payload"]

def test_v650_metadata():
    """
    Verifies that the system reports correct v650 Supreme Apex metadata.
    """
    client = TestClient(app)
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == APP_VERSION
    assert data["git_commit"] == GIT_COMMIT
    assert data["status"] == OPERATIONAL_APEX
