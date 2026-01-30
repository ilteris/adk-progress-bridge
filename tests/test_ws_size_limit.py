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
        # Create a message that is slightly larger than the limit
        large_payload = "a" * (WS_MESSAGE_SIZE_LIMIT + 100)
        large_message = {
            "type": "start",
            "tool_name": "security_scan",
            "payload": large_payload
        }
        
        websocket.send_text(json.dumps(large_message))
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "Message too large" in data["payload"]["detail"]