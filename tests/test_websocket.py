import sys
import os
import json
import pytest
import asyncio
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app

def test_websocket_flow():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Start a task
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": 1}
        })
        
        # 2. Receive progress
        data = websocket.receive_json()
        assert data["type"] == "progress"
        assert "call_id" in data
        call_id = data["call_id"]
        
        # 3. Receive result (eventually)
        found_result = False
        # We might get multiple progress events
        for _ in range(10):
            data = websocket.receive_json()
            if data["type"] == "result":
                found_result = True
                assert data["call_id"] == call_id
                break
        
        assert found_result

def test_websocket_stop():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Start a task
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": 5}
        })
        
        # 2. Capture call_id
        data = websocket.receive_json()
        call_id = data["call_id"]
        
        # 3. Send stop
        websocket.send_json({
            "type": "stop",
            "call_id": call_id
        })
        
        # 4. Wait for cancellation message
        found_cancelled = False
        for _ in range(10):
            data = websocket.receive_json()
            if data["type"] == "progress" and data["payload"].get("step") == "Cancelled":
                found_cancelled = True
                break
            # Or if the tool yields the "Task stopped by user" message
            if data["type"] == "progress" and "stopped by user" in (data["payload"].get("log") or ""):
                found_cancelled = True
                break
        
        assert found_cancelled

def test_websocket_invalid_tool():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({
            "type": "start",
            "tool_name": "non_existent",
            "args": {}
        })
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "Tool not found" in data["payload"]["detail"]

def test_websocket_interactive():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Start interactive task
        websocket.send_json({
            "type": "start",
            "tool_name": "interactive_task",
            "args": {}
        })
        
        call_id = None
        found_input_request = False
        found_result = False
        
        # Receive events until we get an input request
        for _ in range(20):
            data = websocket.receive_json()
            if not call_id:
                call_id = data.get("call_id")
            
            if data["type"] == "input_request":
                found_input_request = True
                assert "prompt" in data["payload"]
                
                # 2. Send input response
                websocket.send_json({
                    "type": "input",
                    "call_id": call_id,
                    "value": "yes"
                })
            
            if data["type"] == "result":
                found_result = True
                assert data["payload"]["status"] == "complete"
                assert "user approval" in data["payload"]["message"]
                break
                
        assert found_input_request
        assert found_result

if __name__ == "__main__":
    # Run tests manually if executed directly
    test_websocket_flow()
    print("test_websocket_flow passed")
    test_websocket_stop()
    print("test_websocket_stop passed")
    test_websocket_invalid_tool()
    print("test_websocket_invalid_tool passed")
    test_websocket_interactive()
    print("test_websocket_interactive passed")