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
                assert "system_net_if_addrs_total_count_audit" in tools
                assert "system_net_if_addrs_ipv4_count_audit" in tools
                assert "system_net_if_addrs_ipv6_count_audit" in tools
                break

        # Test tool 1
        req_id = "v677_test_total_count"
        websocket.send_json({
            "type": "start",
            "tool_name": "system_net_if_addrs_total_count_audit",
            "args": {"samples": 1},
            "request_id": req_id
        })

        while True:
            data = websocket.receive_json()
            if data.get("type") == "result" and data.get("request_id") == req_id:
                assert data["payload"]["status"] == "audit_complete"
                assert "final_net_if_addrs_total_count_total" in data["payload"]
                break

        # Test tool 2
        req_id = "v677_test_ipv4_count"
        websocket.send_json({
            "type": "start",
            "tool_name": "system_net_if_addrs_ipv4_count_audit",
            "args": {"samples": 1},
            "request_id": req_id
        })

        while True:
            data = websocket.receive_json()
            if data.get("type") == "result" and data.get("request_id") == req_id:
                assert data["payload"]["status"] == "audit_complete"
                assert "final_net_if_addrs_ipv4_count_total" in data["payload"]
                break

        # Test tool 3
        req_id = "v677_test_ipv6_count"
        websocket.send_json({
            "type": "start",
            "tool_name": "system_net_if_addrs_ipv6_count_audit",
            "args": {"samples": 1},
            "request_id": req_id
        })

        while True:
            data = websocket.receive_json()
            if data.get("type") == "result" and data.get("request_id") == req_id:
                assert data["payload"]["status"] == "audit_complete"
                assert "final_net_if_addrs_ipv6_count_total" in data["payload"]
                break
