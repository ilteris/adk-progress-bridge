import pytest
import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.bridge import registry, progress_tool, ProgressPayload

@pytest.mark.asyncio
async def test_ws_non_dict_result():
    @progress_tool(name="non_dict_tool")
    async def non_dict_tool():
        yield ProgressPayload(step="test", pct=50)
        yield "Final String Result"

    from fastapi.testclient import TestClient
    with TestClient(app) as client:
        with client.websocket_connect("/ws?api_key=test-key") as websocket:
            websocket.send_json({"type": "start", "tool_name": "non_dict_tool"})
            
            # task_started
            msg = websocket.receive_json()
            assert msg["type"] == "task_started"
            
            # progress
            msg = websocket.receive_json()
            assert msg["type"] == "progress"
            
            # result
            msg = websocket.receive_json()
            assert msg["type"] == "result"
            assert msg["payload"] == "Final String Result"
