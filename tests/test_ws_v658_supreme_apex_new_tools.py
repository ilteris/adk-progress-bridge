from fastapi.testclient import TestClient
from backend.app.main import app
import pytest
import json

def test_ws_v659_new_tools():
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        print("\n[CLIENT] Connected to WS")
        # Handshake
        data = websocket.receive_json()
        print(f"[CLIENT] Received: {data['type']}")
        assert data["type"] == "connected"

        # List tools
        print("[CLIENT] Sending list_tools")
        websocket.send_json({"type": "list_tools", "request_id": "v659_list"})
        
        while True:
            data = websocket.receive_json()
            print(f"[CLIENT] Received: {data.get('type')} {data.get('request_id')}")
            if data["type"] == "tools_list":
                tools = data["tools"]
                assert "system_net_io_dropin_total_audit" in tools
                break

        # Test tool
        req_id = "v659_test_dropin_total"
        print(f"[CLIENT] Starting tool {req_id}")
        websocket.send_json({
            "type": "start",
            "tool_name": "system_net_io_dropin_total_audit",
            "args": {"samples": 1},
            "request_id": req_id
        })

        # Wait for result
        print("[CLIENT] Waiting for messages...")
        while True:
            try:
                data = websocket.receive_json()
                print(f"[CLIENT] Received: {data.get('type')} for req {data.get('request_id')} | payload keys: {list(data.get('payload', {}).keys()) if isinstance(data.get('payload'), dict) else 'N/A'}")
                
                if data.get("type") == "result" and data.get("request_id") == req_id:
                    print("[CLIENT] Got result!")
                    assert data["payload"]["status"] == "audit_complete"
                    break
                if data.get("type") == "error":
                    print(f"[CLIENT] Got error: {data}")
                    pytest.fail(f"Tool failed: {data['payload']}")
                if data.get("type") == "task_started":
                    print(f"[CLIENT] Task started: {data.get('call_id')}")
            except Exception as e:
                print(f"[CLIENT] Exception during receive: {e}")
                raise
        print("[CLIENT] Test finished successfully")
