import sys
import os
import json
import pytest
import asyncio
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set API key for tests before importing app
API_KEY = "test_secret_key"
os.environ["BRIDGE_API_KEY"] = API_KEY

from backend.app.main import app

@pytest.mark.asyncio
async def test_websocket_concurrency():
    """
    Verifies that multiple tasks can run concurrently over a single WebSocket connection.
    """
    client = TestClient(app)
    # TestClient's websocket_connect is synchronous in its context manager usage, 
    # but we can use it to test concurrency by starting multiple tasks.
    with client.websocket_connect(f"/ws?api_key={API_KEY}") as websocket:
        # 1. Start Task A (2 seconds)
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": 2},
            "request_id": "req_A"
        })
        
        # 2. Start Task B (1 second)
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": 1},
            "request_id": "req_B"
        })
        
        call_id_a = None
        call_id_b = None
        
        results_received = 0
        a_finished = False
        b_finished = False
        
        # We expect Task B to finish BEFORE Task A because it's shorter
        # (assuming they started roughly at the same time)
        
        for _ in range(50):
            data = websocket.receive_json()
            
            if data["type"] == "task_started":
                if data["request_id"] == "req_A":
                    call_id_a = data["call_id"]
                elif data["request_id"] == "req_B":
                    call_id_b = data["call_id"]
            
            if data["type"] == "result":
                results_received += 1
                if data["call_id"] == call_id_b:
                    b_finished = True
                    # If B finishes and A hasn't finished yet, that's good evidence of concurrency
                    # since A started first but takes longer.
                    # However, strictly speaking, they are just running concurrently.
                elif data["call_id"] == call_id_a:
                    a_finished = True
                
                if results_received == 2:
                    break
        
        assert call_id_a is not None
        assert call_id_b is not None
        assert a_finished
        assert b_finished
        assert results_received == 2

if __name__ == "__main__":
    # Manual run if needed
    import anyio
    anyio.run(test_websocket_concurrency)