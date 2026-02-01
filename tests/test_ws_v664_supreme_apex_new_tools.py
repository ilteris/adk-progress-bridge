from fastapi.testclient import TestClient
from backend.app.main import app
import pytest
import json

def test_ws_v668_new_tools():
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        # Handshake
        data = websocket.receive_json()
        assert data["type"] == "connected"

        # List tools
        websocket.send_json({"type": "list_tools", "request_id": "v668_list"})
        
        while True:
            data = websocket.receive_json()
            if data["type"] == "tools_list":
                tools = data["tools"]
                assert "system_cpu_times_user_total_audit" in tools
                assert "system_cpu_times_system_total_audit" in tools
                assert "system_cpu_times_idle_total_audit" in tools
                break

        # Test tool 1
        req_id = "v668_test_user_total"
        websocket.send_json({
            "type": "start",
            "tool_name": "system_cpu_times_user_total_audit",
            "args": {"samples": 1},
            "request_id": req_id
        })

        while True:
            data = websocket.receive_json()
            if data.get("type") == "result" and data.get("request_id") == req_id:
                assert data["payload"]["status"] == "audit_complete"
                assert "final_user_time_total" in data["payload"]
                break

        # Test tool 2
        req_id = "v668_test_system_total"
        websocket.send_json({
            "type": "start",
            "tool_name": "system_cpu_times_system_total_audit",
            "args": {"samples": 1},
            "request_id": req_id
        })

        while True:
            data = websocket.receive_json()
            if data.get("type") == "result" and data.get("request_id") == req_id:
                assert data["payload"]["status"] == "audit_complete"
                assert "final_system_time_total" in data["payload"]
                break

        # Test tool 3
        req_id = "v668_test_idle_total"
        websocket.send_json({
            "type": "start",
            "tool_name": "system_cpu_times_idle_total_audit",
            "args": {"samples": 1},
            "request_id": req_id
        })

        while True:
            data = websocket.receive_json()
            if data.get("type") == "result" and data.get("request_id") == req_id:
                assert data["payload"]["status"] == "audit_complete"
                assert "final_idle_time_total" in data["payload"]
                break
