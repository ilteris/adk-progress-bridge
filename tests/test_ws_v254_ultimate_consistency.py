import pytest
import json
import time
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.bridge import PROTOCOL_VERSION

def check_consistency(data, msg_type=None):
    """Helper to verify common fields are present in the response."""
    if msg_type:
        assert data["type"] == msg_type
    assert "protocol_version" in data, f"protocol_version missing in {data.get('type', 'unknown')} message"
    assert data["protocol_version"] == PROTOCOL_VERSION
    assert "timestamp" in data, f"timestamp missing in {data.get('type', 'unknown')} message"
    assert isinstance(data["timestamp"], (int, float))

def test_ws_v254_ping_pong_consistency():
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        websocket.send_json({"type": "ping"})
        data = websocket.receive_json()
        check_consistency(data, "pong")

def test_ws_v254_list_tools_consistency():
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        websocket.send_json({"type": "list_tools", "request_id": "req-list"})
        data = websocket.receive_json()
        check_consistency(data, "tools_list")
        assert data["request_id"] == "req-list"
        assert isinstance(data["tools"], list)

def test_ws_v254_full_flow_consistency():
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        # 1. Start task
        websocket.send_json({
            "type": "start", 
            "tool_name": "interactive_task", 
            "request_id": "req-start"
        })
        
        # 2. Receive task_started
        data = websocket.receive_json()
        check_consistency(data, "task_started")
        assert data["request_id"] == "req-start"
        call_id = data["call_id"]
        
        # 3. Receive progress (Analyzing situation)
        data = websocket.receive_json()
        check_consistency(data, "progress")
        assert data["call_id"] == call_id
        
        # 4. Receive input_request
        data = websocket.receive_json()
        check_consistency(data, "input_request")
        assert data["call_id"] == call_id
        
        # 5. Provide input
        websocket.send_json({
            "type": "input", 
            "call_id": call_id, 
            "value": "yes", 
            "request_id": "req-input"
        })
        
        # 6. Receive input_success
        data = websocket.receive_json()
        check_consistency(data, "input_success")
        assert data["request_id"] == "req-input"
        
        # 7. Receive progress (Finalizing)
        data = websocket.receive_json()
        check_consistency(data, "progress")
        assert data["payload"]["step"] == "Finalizing"

        # 8. Receive result
        data = websocket.receive_json()
        check_consistency(data, "result")
        assert data["call_id"] == call_id

def test_ws_v254_stop_consistency():
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        # Start
        websocket.send_json({"type": "start", "tool_name": "long_audit", "request_id": "req-1"})
        websocket.receive_json() # task_started
        
        # Stop
        websocket.send_json({"type": "stop", "call_id": "some-id", "request_id": "req-stop"})
        
        # If it was a bogus ID, we get an error, but it should still be consistent
        data = websocket.receive_json()
        if data["type"] == "error":
            check_consistency(data)
            assert data["request_id"] == "req-stop"

def test_ws_v254_unknown_type_consistency():
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        websocket.send_json({"type": "bogus", "request_id": "req-bogus"})
        data = websocket.receive_json()
        check_consistency(data, "error")
        assert "Unknown message type" in data["payload"]["detail"]
        assert data["request_id"] == "req-bogus"

def test_ws_v254_invalid_json_consistency():
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        websocket.send_text("not json")
        data = websocket.receive_json()
        check_consistency(data, "error")
        assert "Invalid JSON" in data["payload"]["detail"]