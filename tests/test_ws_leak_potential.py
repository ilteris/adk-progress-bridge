import sys
import os
import pytest
import asyncio
import time
from fastapi.testclient import TestClient
from unittest.mock import patch

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app
from backend.app.bridge import registry

async def wait_for_empty_registry(timeout=5):
    start = time.time()
    while time.time() - start < timeout:
        active = await registry.list_active_tasks()
        if len(active) == 0:
            return True
        await asyncio.sleep(0.1)
    return False

@pytest.mark.asyncio
async def test_sse_start_leak_on_immediate_disconnect():
    client = TestClient(app)
    
    # Clear registry
    await registry.cleanup_tasks()
    
    # 1. Start a task
    response = client.post("/start_task/long_audit", json={"args": {"duration": 1}}, headers={"X-API-Key": "test-key"})
    assert response.status_code == 200
    call_id = response.json()["call_id"]
    
    # Check it's in registry
    assert len(await registry.list_active_tasks()) == 1
    
    # 2. "Connect" to stream but simulate immediate failure before generator starts
    original_get_task = registry.get_task
    async def mocked_get_task(cid):
        task = await original_get_task(cid)
        if task:
            raise Exception("Simulated failure after get_task")
        return task
        
    with patch.object(registry, "get_task", side_effect=mocked_get_task):
        with pytest.raises(Exception, match="Simulated failure after get_task"):
            client.get(f"/stream/{call_id}", headers={"X-API-Key": "test-key"})
            
    # Check if cleaned up
    assert await wait_for_empty_registry(), f"Leaked SSE task found: {await registry.list_active_tasks()}"

@pytest.mark.asyncio
async def test_websocket_start_leak_on_send_failure():
    client = TestClient(app)
    await registry.cleanup_tasks()
    
    # We patch send_text to fail. safe_send_json will catch it and log it, but the start handler catches it and cleans up.
    with patch("fastapi.WebSocket.send_text", side_effect=Exception("Simulated send failure")):
        with client.websocket_connect("/ws?api_key=test-key") as websocket:
            websocket.send_json({
                "type": "start",
                "tool_name": "long_audit",
                "args": {"duration": 1}
            })
            # Wait a bit for the background tasks to process and fail
            await asyncio.sleep(0.5)
    
    # Check if cleaned up
    assert await wait_for_empty_registry(), f"Leaked WS task found: {await registry.list_active_tasks()}"