from fastapi.testclient import TestClient
from backend.app.main import app, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX
import pytest
import json

def test_ws_v677_new_tools():
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        # Handshake
        data = websocket.receive_json()
        assert data["type"] == "connected"

        # List tools
        websocket.send_json({"type": "list_tools", "request_id": "v677_list"})
        
        while True:
            data = websocket.receive_json()
            if data["type"] == "tools_list":
                tools = data["tools"]
                assert "system_cpu_freq_max_avg_audit" in tools
                assert "system_memory_shared_audit" in tools
                assert "system_memory_slab_audit" in tools
                break

        # Test tool 1
        req_id = "v677_test_cpu_freq_max"
        websocket.send_json({
            "type": "start",
            "tool_name": "system_cpu_freq_max_avg_audit",
            "args": {"samples": 1},
            "request_id": req_id
        })

        while True:
            data = websocket.receive_json()
            if data.get("type") == "result" and data.get("request_id") == req_id:
                assert data["payload"]["status"] == "audit_complete"
                assert "final_cpu_freq_max_avg" in data["payload"]
                break

        # Test tool 2
        req_id = "v677_test_memory_shared"
        websocket.send_json({
            "type": "start",
            "tool_name": "system_memory_shared_audit",
            "args": {"samples": 1},
            "request_id": req_id
        })

        while True:
            data = websocket.receive_json()
            if data.get("type") == "result" and data.get("request_id") == req_id:
                assert data["payload"]["status"] == "audit_complete"
                assert "final_memory_shared" in data["payload"]
                break

        # Test tool 3
        req_id = "v677_test_memory_slab"
        websocket.send_json({
            "type": "start",
            "tool_name": "system_memory_slab_audit",
            "args": {"samples": 1},
            "request_id": req_id
        })

        while True:
            data = websocket.receive_json()
            if data.get("type") == "result" and data.get("request_id") == req_id:
                assert data["payload"]["status"] == "audit_complete"
                assert "final_memory_slab" in data["payload"]
                break