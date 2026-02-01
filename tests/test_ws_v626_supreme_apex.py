import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX

def test_process_memory_full_info_audit_tool_ws():
    """
    Verifies that the new process_memory_full_info_audit tool works over WebSocket.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Handshake
        resp = websocket.receive_json()
        assert resp["type"] == "connected"

        # 2. Start process_memory_full_info_audit
        websocket.send_text(json.dumps({
            "type": "start",
            "tool_name": "process_memory_full_info_audit",
            "args": {"samples": 2},
            "request_id": "req-v626-mem"
        }))
        
        resp = websocket.receive_json()
        assert resp["type"] == "task_started"

        # 3. Receive progress
        while True:
            resp = websocket.receive_json()
            if resp["type"] == "result":
                break
        
        assert resp["payload"]["status"] == "audit_complete"
        assert "final_rss" in resp["payload"]

def test_process_threads_audit_tool_ws():
    """
    Verifies that the new process_threads_audit tool works over WebSocket.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Handshake
        resp = websocket.receive_json()
        assert resp["type"] == "connected"

        # 2. Start process_threads_audit
        websocket.send_text(json.dumps({
            "type": "start",
            "tool_name": "process_threads_audit",
            "args": {"samples": 2},
            "request_id": "req-v626-threads"
        }))
        
        resp = websocket.receive_json()
        assert resp["type"] == "task_started"

        # 3. Receive progress
        while True:
            resp = websocket.receive_json()
            if resp["type"] == "result":
                break
        
        assert resp["payload"]["status"] == "audit_complete"
        assert "final_thread_count" in resp["payload"]

def test_process_exe_audit_tool_ws():
    """
    Verifies that the new process_exe_audit tool works over WebSocket.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Handshake
        resp = websocket.receive_json()
        assert resp["type"] == "connected"

        # 2. Start process_exe_audit
        websocket.send_text(json.dumps({
            "type": "start",
            "tool_name": "process_exe_audit",
            "args": {"samples": 2},
            "request_id": "req-v626-exe"
        }))
        
        resp = websocket.receive_json()
        assert resp["type"] == "task_started"

        # 3. Receive progress
        while True:
            resp = websocket.receive_json()
            if resp["type"] == "result":
                break
        
        assert resp["payload"]["status"] == "audit_complete"
        assert "final_exe_path" in resp["payload"]

def test_v626_metadata():
    """
    Verifies that the system reports correct v626 Supreme Apex metadata.
    """
    client = TestClient(app)
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == APP_VERSION
    assert data["git_commit"] == GIT_COMMIT
    assert data["status"] == OPERATIONAL_APEX
