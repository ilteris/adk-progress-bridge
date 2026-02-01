import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
import time

@pytest.mark.asyncio
async def test_ws_v660_new_tools():
    """
    SUPREME APEX VERIFICATION v660:
    Verify the 3 new focused audit tools are present and functional.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        # Handshake
        data = websocket.receive_json()
        assert data["type"] == "connected"

        # List tools to verify presence
        websocket.send_json({"type": "list_tools", "request_id": "v660_list"})
        
        found_tools = False
        for _ in range(100):
            data = websocket.receive_json()
            if data["type"] == "tools_list":
                tools = data["tools"]
                assert "system_net_io_dropout_focused_audit" in tools
                assert "system_swap_memory_sin_focused_audit" in tools
                assert "system_swap_memory_sout_focused_audit" in tools
                found_tools = True
                break
        assert found_tools

        # Test one tool via WS
        req_id = "v660_test_dropout"
        websocket.send_json({
            "type": "start",
            "tool_name": "system_net_io_dropout_focused_audit",
            "args": {"samples": 1},
            "request_id": req_id
        })

        # Wait for result
        found_result = False
        for _ in range(200):
            data = websocket.receive_json()
            # print(f"Received: {data.get('type')} for {data.get('request_id')}")
            if data.get("type") == "result" and data.get("request_id") == req_id:
                assert data["payload"]["status"] == "audit_complete"
                found_result = True
                break
            if data.get("type") == "error" and data.get("request_id") == req_id:
                pytest.fail(f"Tool failed: {data['payload']}")
        
        assert found_result
