import sys
import os
import pytest
import asyncio
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app

def test_stop_sse_task_via_websocket():
    """
    Verifies that a task started via REST/SSE can be stopped via a WebSocket message.
    """
    client = TestClient(app)
    
    # 1. Start a long-running task via REST
    response = client.post("/start_task/long_audit", json={"args": {"duration": 10}})
    assert response.status_code == 200
    call_id = response.json()["call_id"]
    
    # 2. Connect via WebSocket and send a stop message for that call_id
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({
            "type": "stop",
            "call_id": call_id,
            "request_id": "cross_stop_test"
        })
        
        # 3. Verify stop_success response
        data = websocket.receive_json()
        assert data["type"] == "stop_success"
        assert data["call_id"] == call_id
        assert data["request_id"] == "cross_stop_test"
        
    # 4. Verify the task is gone from the registry
    # We can check this by trying to stream it and expecting 404
    response = client.get(f"/stream/{call_id}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_websocket_active_connections_robustness():
    """
    Verifies that the WS_ACTIVE_CONNECTIONS metric is correctly decremented
    even if an exception occurs during authentication.
    """
    from backend.app.metrics import WS_ACTIVE_CONNECTIONS
    from prometheus_client import REGISTRY
    
    client = TestClient(app)
    
    # Get initial value
    initial = WS_ACTIVE_CONNECTIONS._value.get()
    
    # Try to connect with invalid API key (if security is enabled)
    # If BRIDGE_API_KEY is set in env, this should trigger decrement
    os.environ["BRIDGE_API_KEY"] = "super-secret-key"
    
    try:
        # This should fail authentication and return
        with client.websocket_connect("/ws?api_key=wrong-key") as websocket:
            pass
    except:
        pass # Expected failure
        
    # Verify it's back to initial
    assert WS_ACTIVE_CONNECTIONS._value.get() == initial
    
    # Clean up
    del os.environ["BRIDGE_API_KEY"]
