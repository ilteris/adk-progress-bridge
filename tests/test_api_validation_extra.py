import pytest
import asyncio
from fastapi.testclient import TestClient
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
    
    # Explicitly handle the un-awaited coroutine to avoid RuntimeWarning in tests
    # This is a bit of a hack but since we are testing failure to start a non-gen tool,
    # the coroutine returned by the tool is never used.
    try:
        # We don't have easy access to the coroutine object here because it was created inside start_task
        # but store_task failed. However, the error message in test confirms it was caught.
        pass
    except:
        pass

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