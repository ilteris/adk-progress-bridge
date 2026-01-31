import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from backend.app.main import app, registry
from backend.app.bridge import ProgressPayload, progress_tool

@progress_tool(name="slow_task_metrics")
async def slow_task_metrics(duration: int = 5):
    yield ProgressPayload(step="Started", pct=0)
    await asyncio.sleep(duration)
    yield ProgressPayload(step="Finished", pct=100)
    yield {"result": "ok"}

@pytest.mark.asyncio
async def test_ws_metrics_periodic():
    from fastapi.testclient import TestClient
    from backend.app.main import app
    
    with TestClient(app) as client:
        with client.websocket_connect("/ws?api_key=test_key") as websocket:
            # Start a task that sleeps for 5 seconds
            websocket.send_json({
                "type": "start",
                "tool_name": "slow_task_metrics",
                "args": {"duration": 5},
                "request_id": "req1"
            })
            
            # 1. task_started
            resp = websocket.receive_json()
            assert resp["type"] == "task_started"
            call_id = resp["call_id"]
            
            # 2. progress (Started)
            resp = websocket.receive_json()
            assert resp["type"] == "progress"
            
            # Now the task is sleeping for 5 seconds.
            # We expect system_metrics to arrive after ~3 seconds.
            
            metrics_events = []
            start_time = asyncio.get_event_loop().time()
            
            # Wait up to 6 seconds for metrics or completion
            while asyncio.get_event_loop().time() - start_time < 6:
                try:
                    resp = websocket.receive_json()
                    if resp["type"] == "system_metrics":
                        metrics_events.append(resp)
                    elif resp["type"] == "progress" and resp["payload"]["step"] == "Finished":
                        pass
                    elif resp["type"] == "result":
                        break
                except Exception:
                    break
            
            assert len(metrics_events) > 0, "Should have received system_metrics during the 5s sleep"
            for event in metrics_events:
                assert event["call_id"] == call_id, f"system_metrics should include the correct call_id: {call_id}"
                assert "payload" in event, "system_metrics should include payload"
