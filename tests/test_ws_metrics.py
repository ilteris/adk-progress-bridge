import sys
import os
import json
import pytest
from fastapi.testclient import TestClient

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set API key for tests before importing app
API_KEY = "test_secret_key"
os.environ["BRIDGE_API_KEY"] = API_KEY

from backend.app.main import app

def test_websocket_metrics_increment():
    client = TestClient(app)
    
    # 1. Verify initial metrics
    # Need to pass API key for /metrics too
    res = client.get(f"/metrics?api_key={API_KEY}")
    initial_count = 0
    for line in res.text.split('\n'):
        if 'adk_tasks_total{status="success",tool_name="long_audit"}' in line:
            try:
                initial_count = float(line.split()[-1])
            except (ValueError, IndexError):
                initial_count = 0
            break
            
    # 2. Run a task via WebSocket
    with client.websocket_connect(f"/ws?api_key={API_KEY}") as websocket:
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
            if data["type"] == "result":
                found_result = True
                break
        assert found_result
        
    # 3. Verify metrics incremented
    res = client.get(f"/metrics?api_key={API_KEY}")
    final_count = 0
    for line in res.text.split('\n'):
        if 'adk_tasks_total{status="success",tool_name="long_audit"}' in line:
            try:
                final_count = float(line.split()[-1])
            except (ValueError, IndexError):
                final_count = 0
            break
    
    assert final_count == initial_count + 1
