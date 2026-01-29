import time
import sys
import os
import json
import pytest
import asyncio
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set API key for tests before importing app
API_KEY = "test_secret_key"
os.environ["BRIDGE_API_KEY"] = API_KEY

from backend.app.main import app
from backend.app.bridge import registry

def test_websocket_marks_consumed():
    """
    Verifies that starting a task via WebSocket marks it as 'consumed' 
    in the registry to prevent it from being reaped by the stale cleanup loop.
    """
    client = TestClient(app)
    with client.websocket_connect(f"/ws?api_key={API_KEY}") as websocket:
        # 1. Start a task
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": 1},
            "request_id": "test_req_consumed"
        })
        
        # 2. Receive task_started message to get call_id
        call_id = None
        for _ in range(10):
            data = websocket.receive_json()
            if data["type"] == "task_started" and data.get("request_id") == "test_req_consumed":
                call_id = data["call_id"]
                break
        
        assert call_id is not None
        
        # 3. Check registry state directly
        task_data = registry.get_task_no_consume(call_id)
        assert task_data is not None
        assert task_data["consumed"] is True, "WebSocket task should be marked as consumed immediately"

def test_websocket_not_reaped_by_cleanup():
    """
    Verifies that a WebSocket task is NOT reaped by cleanup_stale_tasks.
    """
    client = TestClient(app)
    with client.websocket_connect(f"/ws?api_key={API_KEY}") as websocket:
        # 1. Start a task
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": 10},
            "request_id": "test_req_no_reap"
        })
        
        # 2. Receive task_started message
        call_id = None
        for _ in range(10):
            data = websocket.receive_json()
            if data["type"] == "task_started" and data.get("request_id") == "test_req_no_reap":
                call_id = data["call_id"]
                break
        
        assert call_id is not None
        
        # 3. Trigger cleanup with 0 seconds age (everything not consumed is stale)
        async def run_cleanup():
            await registry.cleanup_stale_tasks(max_age_seconds=-1) # Everything not consumed is stale
            
        asyncio.run(run_cleanup())
        
        # 4. Verify task still exists in registry
        task_data = registry.get_task_no_consume(call_id)
        assert task_data is not None, "WebSocket task should NOT have been reaped by cleanup"

def test_websocket_disconnect_cleans_up_all_tasks():
    """
    Verifies that if a WebSocket client disconnects while multiple tasks 
    are running, all those tasks are properly cancelled and removed 
    from the registry.
    """
    client = TestClient(app)
    call_ids = []
    
    with client.websocket_connect(f"/ws?api_key={API_KEY}") as websocket:
        # Start 3 tasks
        for i in range(3):
            websocket.send_json({
                "type": "start",
                "tool_name": "long_audit",
                "args": {"duration": 10},
                "request_id": f"req_{i}"
            })
            
            # Receive task_started
            found_start = False
            for _ in range(10):
                data = websocket.receive_json()
                if data["type"] == "task_started" and data.get("request_id") == f"req_{i}":
                    call_ids.append(data["call_id"])
                    found_start = True
                    break
            assert found_start
        
        assert len(call_ids) == 3
        
        # Verify they are in registry
        for cid in call_ids:
            assert registry.get_task_no_consume(cid) is not None
            
        # Disconnect by exiting 'with' block
    
    # Wait a bit for tasks to be cancelled in the background
    time.sleep(0.5)
    
    # Verify they are removed from registry
    for cid in call_ids:
        assert registry.get_task_no_consume(cid) is None, f"Task {cid} should have been cleaned up on disconnect"

if __name__ == "__main__":
    # Manual run
    pytest.main([__file__])
