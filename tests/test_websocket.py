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
            "args": {"duration": 1},
            "request_id": "test_req_1"
        })
        
        # 2. Receive task_started (might get progress first)
        call_id = None
        for _ in range(10):
            data = websocket.receive_json()
            if data["type"] == "task_started" and data.get("request_id") == "test_req_1":
                call_id = data["call_id"]
                break
        
        assert call_id is not None
        
        # 3. Receive result (eventually)
        found_result = False
        # We might get multiple progress events
        for _ in range(20):
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
            "args": {"duration": 5},
            "request_id": "test_req_stop"
        })
        
        # 2. Receive task_started
        call_id = None
        for _ in range(10):
            data = websocket.receive_json()
            if data["type"] == "task_started" and data.get("request_id") == "test_req_stop":
                call_id = data["call_id"]
                break
        
        assert call_id is not None
        
        # 3. Send stop
        websocket.send_json({
            "type": "stop",
            "call_id": call_id,
            "request_id": "stop_req_1"
        })
        
        # 4. Wait for stop_success and cancellation message
        found_stop_success = False
        found_cancelled = False
        for _ in range(20):
            data = websocket.receive_json()
            if data["type"] == "stop_success" and data.get("request_id") == "stop_req_1":
                found_stop_success = True
            if data["type"] == "progress" and data["payload"].get("step") == "Cancelled":
                found_cancelled = True
            
            if found_stop_success and found_cancelled:
                break
        
        assert found_stop_success
        assert found_cancelled

def test_websocket_invalid_tool():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({
            "type": "start",
            "tool_name": "non_existent",
            "args": {},
            "request_id": "invalid_tool_req"
        })
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data.get("request_id") == "invalid_tool_req"
        assert "Tool not found" in data["payload"]["detail"]

def test_websocket_interactive():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Start interactive task
        websocket.send_json({
            "type": "start",
            "tool_name": "interactive_task",
            "args": {},
            "request_id": "test_req_interactive"
        })
        
        # 2. Receive task_started
        call_id = None
        for _ in range(10):
            data = websocket.receive_json()
            if data["type"] == "task_started" and data.get("request_id") == "test_req_interactive":
                call_id = data["call_id"]
                break
        
        assert call_id is not None

        found_input_request = False
        found_input_success = False
        found_result = False
        
        # Receive events until we get an input request
        for _ in range(30):
            data = websocket.receive_json()
            
            if data["type"] == "input_request":
                found_input_request = True
                assert "prompt" in data["payload"]
                
                # 3. Send input response
                websocket.send_json({
                    "type": "input",
                    "call_id": call_id,
                    "value": "yes",
                    "request_id": "input_req_1"
                })
            
            if data["type"] == "input_success" and data.get("request_id") == "input_req_1":
                found_input_success = True

            if data["type"] == "result":
                found_result = True
                assert data["payload"]["status"] == "complete"
                assert "user approval" in data["payload"]["message"]
                break
                
        assert found_input_request
        assert found_input_success
        assert found_result

def test_websocket_list_tools():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({
            "type": "list_tools",
            "request_id": "list_tools_req"
        })
        
        data = websocket.receive_json()
        assert data["type"] == "tools_list"
        assert data.get("request_id") == "list_tools_req"
        assert isinstance(data["tools"], list)
        assert "long_audit" in data["tools"]

def test_websocket_ping_pong():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({"type": "ping"})
        data = websocket.receive_json()
        assert data["type"] == "pong"

def test_websocket_invalid_json():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_text("not a json")
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "Invalid JSON" in data["payload"]["detail"]

def test_websocket_non_dict_json():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json([1, 2, 3])
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "must be a JSON object" in data["payload"]["detail"]

def test_websocket_unknown_type():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({
            "type": "unknown_message_xyz",
            "request_id": "unknown_type_req"
        })
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data.get("request_id") == "unknown_type_req"
        assert "Unknown message type" in data["payload"]["detail"]

def test_websocket_message_size_limit():
    from backend.app.main import WS_MESSAGE_SIZE_LIMIT
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Create a message slightly larger than the limit
        large_payload = "x" * (WS_MESSAGE_SIZE_LIMIT + 100)
        websocket.send_text(json.dumps({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"data": large_payload}
        }))
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "Message too large" in data["payload"]["detail"]

def test_websocket_subscribe():
    client = TestClient(app)
    # 1. Start a task via REST
    resp = client.post("/start_task/long_audit", json={"args": {"duration": 1}})
    assert resp.status_code == 200
    call_id = resp.json()["call_id"]
    
    # 2. Connect via WebSocket and subscribe
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({
            "type": "subscribe",
            "call_id": call_id,
            "request_id": "sub_req_1"
        })
        
        # 3. Receive task_started acknowledgement
        data = websocket.receive_json()
        assert data["type"] == "task_started"
        assert data["call_id"] == call_id
        assert data.get("request_id") == "sub_req_1"
        
        # 4. Receive events until result
        found_result = False
        for _ in range(20):
            data = websocket.receive_json()
            if data["type"] == "result":
                found_result = True
                assert data["call_id"] == call_id
                break
        
        assert found_result

def test_websocket_subscribe_invalid():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({
            "type": "subscribe",
            "call_id": "non-existent-id",
            "request_id": "sub_req_invalid"
        })
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data.get("request_id") == "sub_req_invalid"
        assert "Task not found" in data["payload"]["detail"]
