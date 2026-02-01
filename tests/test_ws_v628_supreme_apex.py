import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX

def test_process_cpu_num_audit_tool_ws():
    """
    Verifies that the new process_cpu_num_audit tool works over WebSocket.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Handshake
        resp = websocket.receive_json()
        assert resp["type"] == "connected"

        # 2. Start process_cpu_num_audit
        websocket.send_text(json.dumps({
            "type": "start",
            "tool_name": "process_cpu_num_audit",
            "args": {"samples": 2},
            "request_id": "req-v650-cpu-num"
        }))
        
        resp = websocket.receive_json()
        assert resp["type"] == "task_started"

        # 3. Receive progress
        while True:
            resp = websocket.receive_json()
            if resp["type"] == "result":
                break
        
        assert resp["payload"]["status"] == "audit_complete"
        assert "final_cpu_num" in resp["payload"]

def test_system_net_io_counters_audit_tool_ws():
    """
    Verifies that the new system_net_io_counters_audit tool works over WebSocket.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Handshake
        resp = websocket.receive_json()
        assert resp["type"] == "connected"

        # 2. Start system_net_io_counters_audit
        websocket.send_text(json.dumps({
            "type": "start",
            "tool_name": "system_net_io_counters_audit",
            "args": {"samples": 2},
            "request_id": "req-v650-net-io"
        }))
        
        resp = websocket.receive_json()
        assert resp["type"] == "task_started"

        # 3. Receive progress
        while True:
            resp = websocket.receive_json()
            if resp["type"] == "result":
                break
        
        assert resp["payload"]["status"] == "audit_complete"
        assert "final_counters" in resp["payload"]

def test_system_users_audit_tool_ws():
    """
    Verifies that the new system_users_audit tool works over WebSocket.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Handshake
        resp = websocket.receive_json()
        assert resp["type"] == "connected"

        # 2. Start system_users_audit
        websocket.send_text(json.dumps({
            "type": "start",
            "tool_name": "system_users_audit",
            "args": {"samples": 2},
            "request_id": "req-v650-users"
        }))
        
        resp = websocket.receive_json()
        assert resp["type"] == "task_started"

        # 3. Receive progress
        while True:
            resp = websocket.receive_json()
            if resp["type"] == "result":
                break
        
        assert resp["payload"]["status"] == "audit_complete"
        assert "final_user_count" in resp["payload"]

def test_v650_metadata():
    """
    Verifies that the system reports correct v650 Supreme Apex metadata.
    """
    client = TestClient(app)
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "2.7.6"
    assert data["git_commit"] == "v650-supreme-apex-adele-verification"
    assert data["status"] == "v650 SUPREME APEX VERIFICATION ADELE"
