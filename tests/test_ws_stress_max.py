import sys
import os
import json
import pytest
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app, WS_MESSAGE_SIZE_LIMIT

def test_websocket_message_size_limit():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Send a message exactly at the limit (should be fine)
        # We need to account for JSON overhead, so let's send a slightly smaller payload inside the JSON
        payload_size = WS_MESSAGE_SIZE_LIMIT - 100
        large_payload = "a" * payload_size
        
        websocket.send_json({
            "type": "ping",
            "data": large_payload
        })
        
        data = websocket.receive_json()
        assert data["type"] == "pong"

        # 2. Send a message exceeding the limit
        # send_text is better to control exact size
        exceeding_size = WS_MESSAGE_SIZE_LIMIT + 1024
        huge_message = json.dumps({
            "type": "ping",
            "data": "b" * exceeding_size
        })
        
        websocket.send_text(huge_message)
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "Message too large" in data["payload"]["detail"]

def test_websocket_large_start_args():
    """Test that a large start message is also rejected if it exceeds the limit."""
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        payload_size = WS_MESSAGE_SIZE_LIMIT + 100
        large_args = {"data": "x" * payload_size}
        
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": large_args,
            "request_id": "large_req"
        })
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "Message too large" in data["payload"]["detail"]
