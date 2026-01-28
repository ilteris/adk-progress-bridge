import pytest
import os
from fastapi.testclient import TestClient

# Set API key for tests
os.environ["BRIDGE_API_KEY"] = "test_secret_key"
from backend.app.main import app

client = TestClient(app)
API_KEY = "test_secret_key"

def test_rest_call_id_collision():
    """Verify that starting a task with an existing call_id via REST returns 400."""
    call_id = "test_collision_rest"
    
    # Start first task
    resp1 = client.post(
        "/start_task/long_audit", 
        json={"args": {"duration": 5}, "call_id": call_id},
        headers={"X-API-Key": API_KEY}
    )
    assert resp1.status_code == 200
    
    # Start second task with same call_id
    resp2 = client.post(
        "/start_task/long_audit", 
        json={"args": {"duration": 5}, "call_id": call_id},
        headers={"X-API-Key": API_KEY}
    )
    assert resp2.status_code == 400
    assert "already exists" in resp2.json()["detail"]

def test_websocket_call_id_collision():
    """Verify that starting a task with an existing call_id via WS returns an error message."""
    with client.websocket_connect(f"/ws?api_key={API_KEY}") as websocket:
        call_id = "test_collision_ws"
        
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
        
        # Start second task with same call_id
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": 5},
            "call_id": call_id,
            "request_id": "req_2"
        })
        
        data2 = websocket.receive_json()
        # We might get a progress update from the first task, so we loop until we get the error or another task_started (which would be wrong)
        while data2.get("type") == "progress":
            data2 = websocket.receive_json()
            
        assert data2["type"] == "error"
        assert "already exists" in data2["payload"]["detail"]
        assert data2["request_id"] == "req_2"
