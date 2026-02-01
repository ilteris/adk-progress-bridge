import pytest
import asyncio
import json
import time
from fastapi.testclient import TestClient
from backend.app.main import app, registry
from backend.app.bridge import ProgressPayload, progress_tool

@progress_tool(name="slow_task_sse_metrics")
async def slow_task_sse_metrics(duration: int = 5):
    yield ProgressPayload(step="Started", pct=0)
    await asyncio.sleep(duration)
    yield ProgressPayload(step="Finished", pct=100)
    yield {"result": "ok"}

@pytest.mark.asyncio
async def test_sse_metrics_periodic():
    with TestClient(app) as client:
        # Start the task
        response = client.post("/start_task/slow_task_sse_metrics", json={"args": {"duration": 5}}, headers={"X-API-Key": "test_key"})
        assert response.status_code == 200
        call_id = response.json()["call_id"]
        
        # Connect to stream
        metrics_events = []
        progress_events = []
        
        start_time = time.time()
        # In TestClient, we can just iterate over the response
        response = client.get(f"/stream/{call_id}", headers={"X-API-Key": "test_key"})
        assert response.status_code == 200
        
        for line in response.iter_lines():
            if not line:
                continue
            line_str = line
            if line_str.startswith("data: "):
                data = json.loads(line_str[6:])
                if data["type"] == "system_metrics":
                    metrics_events.append(data)
                elif data["type"] == "progress":
                    progress_events.append(data)
                elif data["type"] == "result":
                    break
            
            # Timeout if it takes too long
            if time.time() - start_time > 8:
                break

        assert len(metrics_events) > 0, "Should have received system_metrics during the 5s sleep in SSE"
        for event in metrics_events:
            assert event["call_id"] == call_id, f"system_metrics should include the correct call_id: {call_id}"
            assert "payload" in event, "system_metrics should include payload"
        
        assert any(p["payload"]["step"] == "Started" for p in progress_events)
        assert any(p["payload"]["step"] == "Finished" for p in progress_events)