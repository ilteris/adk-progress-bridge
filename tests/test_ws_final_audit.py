import sys
import os
import json
import pytest
import asyncio
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app

def test_ws_rapid_start_stop_stress():
    """
    Stress test by rapidly starting and stopping tasks over WebSocket.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        for i in range(10):
            req_id = f"stress_start_{i}"
            websocket.send_json({
                "type": "start",
                "tool_name": "long_audit",
                "args": {"duration": 10},
                "request_id": req_id
            })
            
            # Immediately send stop for the task we just started
            # We need the call_id first, which we get from task_started
            call_id = None
            for _ in range(5):
                data = websocket.receive_json()
                if data["type"] == "task_started" and data.get("request_id") == req_id:
                    call_id = data["call_id"]
                    break
            
            if call_id:
                websocket.send_json({
                    "type": "stop",
                    "call_id": call_id,
                    "request_id": f"stress_stop_{i}"
                })
                
                # Verify stop_success
                found_stop = False
                for _ in range(10):
                    data = websocket.receive_json()
                    if data["type"] == "stop_success" and data.get("request_id") == f"stress_stop_{i}":
                        found_stop = True
                        break
                assert found_stop

def test_ws_large_args_validation():
    """
    Tests that the WebSocket endpoint handles large arguments correctly.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Create a large args dictionary using a tool that accepts **kwargs
        large_args = {"data": "x" * 10000, "meta": "y" * 5000}
        
        websocket.send_json({
            "type": "start",
            "tool_name": "large_payload_tool",
            "args": large_args,
            "request_id": "large_args_req"
        })
        
        data = websocket.receive_json()
        assert data["type"] == "task_started"
        assert data.get("request_id") == "large_args_req"

def test_ws_multiple_pings_sequence():
    """
    Tests that the server can handle multiple pings in rapid succession.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        for _ in range(20):
            websocket.send_json({"type": "ping"})
            data = websocket.receive_json()
            assert data["type"] == "pong"

def test_ws_input_unsolicited():
    """
    Tests that providing input for a task that is NOT waiting for input returns an error.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Start a normal (non-interactive) task
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": 5},
            "request_id": "normal_task"
        })
        
        data = websocket.receive_json()
        while data["type"] != "task_started":
            data = websocket.receive_json()
        call_id = data["call_id"]
        
        # 2. Provide unsolicited input
        req_id = "unsolicited_input"
        websocket.send_json({
            "type": "input",
            "call_id": call_id,
            "value": "surprise!",
            "request_id": req_id
        })
        
        # 3. Loop until we find the error response for our input command
        found_error = False
        for _ in range(10):
            data = websocket.receive_json()
            if data["type"] == "error" and data.get("request_id") == req_id:
                found_error = True
                assert "No task waiting for input" in data["payload"]["detail"]
                break
        
        assert found_error

def test_ws_malformed_json_recovery():
    """
    Tests that the WebSocket connection remains healthy after receiving malformed JSON.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Send malformed JSON
        websocket.send_text("{ invalid json")
        data = websocket.receive_json()
        assert data["type"] == "error"
        
        # 2. Send valid command immediately
        websocket.send_json({"type": "ping"})
        data = websocket.receive_json()
        assert data["type"] == "pong"
        
        # 3. Start a tool
        websocket.send_json({
            "type": "start",
            "tool_name": "security_scan",
            "request_id": "recovery_start"
        })
        data = websocket.receive_json()
        assert data["type"] == "task_started"

def test_ws_null_request_id_robustness():
    """
    Tests that the server handles messages with null or missing request_id gracefully.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Null request_id
        websocket.send_json({
            "type": "ping",
            "request_id": None
        })
        data = websocket.receive_json()
        assert data["type"] == "pong"
        
        # Missing request_id for list_tools
        websocket.send_json({
            "type": "list_tools"
        })
        data = websocket.receive_json()
        assert data["type"] == "tools_list"
        assert data.get("request_id") is None
