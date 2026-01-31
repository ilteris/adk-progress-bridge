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

def test_websocket_active_connections_metric():
    client = TestClient(app)
    
    # 1. Verify initial active connections is 0 or what it was
    res = client.get("/metrics")
    initial_ws_count = 0
    for line in res.text.split('\n'):
        if 'adk_ws_active_connections' in line and not line.startswith('#'):
            initial_ws_count = float(line.split()[-1])
            break
            
    # 2. Connect and check metric
    with client.websocket_connect("/ws") as websocket:
        res = client.get("/metrics")
        during_ws_count = 0
        for line in res.text.split('\n'):
            if 'adk_ws_active_connections' in line and not line.startswith('#'):
                during_ws_count = float(line.split()[-1])
                break
        
        assert during_ws_count == initial_ws_count + 1
        
        # 3. Connect another one
        with client.websocket_connect("/ws") as websocket2:
            res = client.get("/metrics")
            two_ws_count = 0
            for line in res.text.split('\n'):
                if 'adk_ws_active_connections' in line and not line.startswith('#'):
                    two_ws_count = float(line.split()[-1])
                    break
            assert two_ws_count == initial_ws_count + 2
            
    # 4. Disconnect and check metric is back to initial
    res = client.get("/metrics")
    final_ws_count = 0
    for line in res.text.split('\n'):
        if 'adk_ws_active_connections' in line and not line.startswith('#'):
            final_ws_count = float(line.split()[-1])
            break
            
    assert final_ws_count == initial_ws_count
