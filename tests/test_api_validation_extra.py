import sys
import os
import pytest
import asyncio
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app
from backend.app.bridge import registry

client = TestClient(app)

def test_non_generator_tool_fail():
    # Register a non-generator tool
    @registry.register(name="non_gen")
    async def non_gen_tool():
        return {"result": "oops"}

    # Attempt to start it
    response = client.post("/start_task/non_gen", headers={"X-API-Key": "test-key"})
    
    # It should fail with 400 because store_task raises TypeError
    assert response.status_code == 400
    assert "did not return an async generator" in response.json()["detail"]

@pytest.mark.asyncio
async def test_websocket_non_generator_fail():
    # Register a non-generator tool
    @registry.register(name="non_gen_ws")
    async def non_gen_tool_ws():
        return {"result": "oops"}

    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        websocket.send_json({
            "type": "start",
            "tool_name": "non_gen_ws",
            "request_id": "req-1"
        })
        
        response = websocket.receive_json()
        assert response["type"] == "error"
        assert response["request_id"] == "req-1"
        assert "did not return an async generator" in response["payload"]["detail"]
