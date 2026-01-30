import sys
import os
import pytest
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set API key for tests before importing app
API_KEY = "test_secret_key"
os.environ["BRIDGE_API_KEY"] = API_KEY

from backend.app.main import app
from backend.app.bridge import registry

client = TestClient(app)
headers = {"X-API-Key": API_KEY}

def test_non_generator_tool_fail():
    # Register a non-generator tool
    @registry.register(name="non_gen")
    async def non_gen_tool():
        return {"result": "oops"}

    # Attempt to start it
    response = client.post("/start_task/non_gen", headers=headers)

    # It should fail with 400 because store_task raises TypeError
    assert response.status_code == 400
    assert "did not return an async generator" in str(response.json()["detail"])

@pytest.mark.asyncio
async def test_websocket_non_generator_fail():
    # Register a non-generator tool
    @registry.register(name="non_gen_ws")
    async def non_gen_tool_ws():
        return {"result": "oops"}

    with client.websocket_connect(f"/ws?api_key={API_KEY}") as websocket:
        websocket.send_json({
            "type": "start",
            "tool_name": "non_gen_ws",
            "request_id": "req-1"
        })

        response = websocket.receive_json()
        assert response["type"] == "error"
        # Check if the error message is present in payload (it might be a string or a dict with detail)
        payload = response["payload"]
        if isinstance(payload, dict) and "detail" in payload:
            payload = payload["detail"]
        assert "did not return an async generator" in str(payload)
