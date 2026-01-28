import sys
import os
import pytest
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app

def test_websocket_metrics_increment():
    client = TestClient(app)
    
    # 1. Verify initial metrics
    res = client.get("/metrics")
    initial_count = 0
    for line in res.text.split('\n'):
        if 'adk_tasks_total{status="success",tool_name="long_audit"}' in line:
            try:
                initial_count = float(line.split()[-1])
            except (ValueError, IndexError):
                initial_count = 0
            break

    # 2. Run a task via WebSocket
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": 1},
            "request_id": "metrics_test"
        })
        
        # Consume all messages until result
        found_result = False
        for _ in range(30):
            data = websocket.receive_json()
            if data["type"] == "error":
                pytest.fail(f"Received error from WebSocket: {data['payload']['detail']}")
            if data["type"] == "result":
                found_result = True
                break
        
        assert found_result

    # 3. Verify metrics incremented
    res = client.get("/metrics")
    final_count = 0
    found_progress = False
    for line in res.text.split('\n'):
        if 'adk_tasks_total{status="success",tool_name="long_audit"}' in line:
            final_count = float(line.split()[-1])
        if 'adk_task_progress_steps_total{tool_name="long_audit"}' in line:
            found_progress = True
    
    assert final_count == initial_count + 1
    assert found_progress