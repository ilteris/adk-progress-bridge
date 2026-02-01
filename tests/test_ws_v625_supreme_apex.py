import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX

def test_process_nice_audit_tool_ws():
    """
    Verifies that the new process_nice_audit tool works over WebSocket.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Handshake
        resp = websocket.receive_json()
        assert resp["type"] == "connected"

        # 2. Start process_nice_audit
        websocket.send_text(json.dumps({
            "type": "start",
            "tool_name": "process_nice_audit",
            "args": {"samples": 2},
            "request_id": "req-v625-nice"
        }))
        
        resp = websocket.receive_json()
        assert resp["type"] == "task_started"

        # 3. Receive progress
        while True:
            resp = websocket.receive_json()
            if resp["type"] == "result":
                break
        
        assert resp["payload"]["status"] == "audit_complete"
        assert "final_nice" in resp["payload"]

def test_process_open_files_audit_tool_ws():
    """
    Verifies that the new process_open_files_audit tool works over WebSocket.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Handshake
        resp = websocket.receive_json()
        assert resp["type"] == "connected"

        # 2. Start process_open_files_audit
        websocket.send_text(json.dumps({
            "type": "start",
            "tool_name": "process_open_files_audit",
            "args": {"samples": 2},
            "request_id": "req-v625-files"
        }))
        
        resp = websocket.receive_json()
        assert resp["type"] == "task_started"

        # 3. Receive progress
        while True:
            resp = websocket.receive_json()
            if resp["type"] == "result":
                break
        
        assert resp["payload"]["status"] == "audit_complete"
        assert "final_open_files_count" in resp["payload"]

def test_process_connections_audit_tool_ws():
    """
    Verifies that the new process_connections_audit tool works over WebSocket.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Handshake
        resp = websocket.receive_json()
        assert resp["type"] == "connected"

        # 2. Start process_connections_audit
        websocket.send_text(json.dumps({
            "type": "start",
            "tool_name": "process_connections_audit",
            "args": {"samples": 2},
            "request_id": "req-v625-conn"
        }))
        
        resp = websocket.receive_json()
        assert resp["type"] == "task_started"

        # 3. Receive progress
        while True:
            resp = websocket.receive_json()
            if resp["type"] == "result":
                break
        
        assert resp["payload"]["status"] == "audit_complete"
        assert "final_connections_count" in resp["payload"]

def test_v625_metadata():
    """
    Verifies that the system reports correct v625 Supreme Apex metadata.
    """
    client = TestClient(app)
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == APP_VERSION
    assert data["git_commit"] == GIT_COMMIT
    assert data["status"] == OPERATIONAL_APEX
