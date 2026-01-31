import sys
import os
import json
import pytest
import asyncio
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app

@pytest.mark.asyncio
async def test_ws_final_sanity_check():
    """
    Final sanity check for all WebSocket commands:
    1. list_tools
    2. start task
    3. ping/pong
    4. input (interactive)
    5. stop task
    """
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        # 1. list_tools
        websocket.send_json({"type": "list_tools", "request_id": "req_list"})
        data = websocket.receive_json()
        assert data["type"] == "tools_list"
        assert "long_audit" in data["tools"]
        assert data["request_id"] == "req_list"

        # 2. ping
        websocket.send_json({"type": "ping"})
        data = websocket.receive_json()
        assert data["type"] == "pong"

        # 3. start interactive task
        websocket.send_json({
            "type": "start",
            "tool_name": "interactive_task",
            "request_id": "req_start"
        })
        data = websocket.receive_json()
        assert data["type"] == "task_started"
        call_id = data["call_id"]
        
        # 4. Wait for input request
        input_req = None
        for _ in range(10):
            data = websocket.receive_json()
            if data["type"] == "input_request":
                input_req = data
                break
        assert input_req is not None
        
        # 5. provide input
        websocket.send_json({
            "type": "input",
            "call_id": call_id,
            "value": "yes",
            "request_id": "req_input"
        })
        data = websocket.receive_json()
        assert data["type"] == "input_success"
        
        # 6. Wait for result
        result = None
        for _ in range(10):
            data = websocket.receive_json()
            if data["type"] == "result":
                result = data
                break
        assert result is not None
        
        # 7. Start another task and stop it
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "request_id": "req_stop_start"
        })
        data = websocket.receive_json()
        call_id_stop = data["call_id"]
        
        websocket.send_json({
            "type": "stop",
            "call_id": call_id_stop,
            "request_id": "req_stop"
        })
        
        stop_success = False
        for _ in range(10):
            data = websocket.receive_json()
            if data["type"] == "stop_success":
                stop_success = True
                break
        assert stop_success

if __name__ == "__main__":
    pytest.main([__file__])
