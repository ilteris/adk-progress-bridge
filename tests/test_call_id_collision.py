import sys
import os
import pytest
import os
from fastapi.testclient import TestClient

# Set API key for tests
os.environ["BRIDGE_API_KEY"] = "test_secret_key"
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app.main import app
from backend.app.bridge import registry

client = TestClient(app)
API_KEY = "test_secret_key"

def test_rest_call_id_collision():
    """Verify that starting a task with an existing call_id via REST returns 400 and doesn't remove original."""
    call_id = "test_collision_rest"
    
    # Ensure registry is clean
    registry.remove_task(call_id)
    
    # Start first task
    resp1 = client.post(
        "/start_task/long_audit", 
        json={"args": {"duration": 5}, "call_id": call_id},
        headers={"X-API-Key": API_KEY}
    )
    assert resp1.status_code == 200
    assert registry.get_task_no_consume(call_id) is not None
    
    # Start second task with same call_id
    resp2 = client.post(
        "/start_task/long_audit", 
        json={"args": {"duration": 5}, "call_id": call_id},
        headers={"X-API-Key": API_KEY}
    )
    assert resp2.status_code == 400
    assert "already exists" in resp2.json()["detail"]
    
    # ORIGINAL TASK SHOULD STILL BE THERE
    assert registry.get_task_no_consume(call_id) is not None

def test_websocket_call_id_collision():
    """Verify that starting a task with an existing call_id via WS returns an error message and doesn't remove original."""
    call_id = "test_collision_ws"
    # Ensure registry is clean
    registry.remove_task(call_id)

    with client.websocket_connect(f"/ws?api_key={API_KEY}") as websocket:
        
        # Start first task
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": 5},
            "call_id": call_id,
            "request_id": "req_1"
        })
        
        data1 = websocket.receive_json()
        assert data1["type"] == "task_started"
        assert registry.get_task_no_consume(call_id) is not None
        
        # Start second task with same call_id
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": 5},
            "call_id": call_id,
            "request_id": "req_2"
        })
        
        data2 = websocket.receive_json()
        while data2.get("type") == "progress":
            data2 = websocket.receive_json()
            
        assert data2["type"] == "error"
        assert "already exists" in data2["payload"]["detail"]
        assert data2["request_id"] == "req_2"

        # ORIGINAL TASK SHOULD STILL BE THERE
        # This is where it's likely to fail if the bug exists
        assert registry.get_task_no_consume(call_id) is not None