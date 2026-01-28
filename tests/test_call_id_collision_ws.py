import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.bridge import registry

@pytest.mark.asyncio
async def test_ws_call_id_collision_does_not_remove_existing_task():
    """
    Test that starting a task with an existing call_id via WebSocket 
    returns an error but DOES NOT remove the existing task.
    """
    with TestClient(app) as client:
        with client.websocket_connect("/ws?api_key=test-key") as websocket:
            # 1. Start a task with a specific call_id
            call_id = "test-collision-id"
            websocket.send_json({
                "type": "start",
                "tool_name": "long_audit",
                "call_id": call_id,
                "request_id": "req-1"
            })
            
            # Wait for confirmation
            resp1 = websocket.receive_json()
            assert resp1["type"] == "task_started"
            assert resp1["call_id"] == call_id
            
            # Verify it's in registry
            assert call_id in registry._active_tasks
            
            # 2. Try to start another task with the SAME call_id
            websocket.send_json({
                "type": "start",
                "tool_name": "long_audit",
                "call_id": call_id,
                "request_id": "req-2"
            })
            
            # Drain messages until we get the error or timeout
            # We expect at least one progress message because the first task is running
            error_received = False
            for _ in range(10):
                resp = websocket.receive_json()
                if resp.get("type") == "error" and resp.get("request_id") == "req-2":
                    assert "already exists" in resp["payload"]["detail"]
                    error_received = True
                    break
            
            assert error_received, "Did not receive error for duplicate call_id"
            
            # 3. CRITICAL: The original task should STILL be in the registry
            assert call_id in registry._active_tasks, "Original task was erroneously removed from registry!"
            
            # Cleanup
            websocket.send_json({
                "type": "stop",
                "call_id": call_id,
                "request_id": "req-3"
            })
            
            # Drain stop success
            stopped = False
            for _ in range(10):
                resp = websocket.receive_json()
                if resp.get("type") == "stop_success":
                    stopped = True
                    break
            assert stopped