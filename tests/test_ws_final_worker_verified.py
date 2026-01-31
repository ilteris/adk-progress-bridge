import sys
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from fastapi import WebSocketDisconnect

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app

@pytest.mark.asyncio
async def test_ws_god_tier_final_verification():
    """
    Ultimate final verification test by Worker-Adele to confirm God Tier status.
    Verifies concurrent start, list_tools, and ping/pong interleaved.
    """
    # Ensure BRIDGE_API_KEY is None for this test
    with patch("backend.app.auth.BRIDGE_API_KEY", None):
        client = TestClient(app)
        with client.websocket_connect("/ws") as websocket:
            # 1. Ping
            websocket.send_json({"type": "ping"})
            assert websocket.receive_json()["type"] == "pong"
            
            # 2. List Tools
            websocket.send_json({"type": "list_tools", "request_id": "req_tools"})
            data = websocket.receive_json()
            assert data["type"] == "tools_list"
            assert "long_audit" in data["tools"]
            assert data["request_id"] == "req_tools"
            
            # 3. Start Task
            websocket.send_json({
                "type": "start",
                "tool_name": "security_scan",
                "args": {"target": "god-tier"},
                "request_id": "req_start"
            })
            
            start_data = websocket.receive_json()
            assert start_data["type"] == "task_started"
            call_id = start_data["call_id"]
            assert start_data["request_id"] == "req_start"
            
            # 4. Interleaved Ping
            websocket.send_json({"type": "ping"})
            
            # 5. Receive Progress
            event1 = websocket.receive_json()
            # It could be the pong or progress
            if event1["type"] == "pong":
                progress1 = websocket.receive_json()
            else:
                progress1 = event1
                assert websocket.receive_json()["type"] == "pong"
                
            assert progress1["type"] == "progress"
            assert progress1["call_id"] == call_id
            
            # 6. Wait for result
            while True:
                event = websocket.receive_json()
                if event["type"] == "result":
                    assert event["payload"]["status"] == "secure"
                    break
                elif event["type"] == "progress":
                    continue
                else:
                    pytest.fail(f"Unexpected event type: {event['type']}")

@pytest.mark.asyncio
async def test_ws_authentication_enforcement():
    """
    Verifies that WebSocket authentication is enforced when BRIDGE_API_KEY is set.
    """
    with patch("backend.app.auth.BRIDGE_API_KEY", "god-tier-secret"):
        client = TestClient(app)
        # Try without key
        with client.websocket_connect("/ws") as websocket:
            with pytest.raises(Exception): # TestClient raises exception on receive if closed
                websocket.receive_json()
        
        # Try with wrong key
        with client.websocket_connect("/ws?api_key=wrong") as websocket:
            with pytest.raises(Exception):
                websocket.receive_json()
                
        # Try with correct key
        with client.websocket_connect("/ws?api_key=god-tier-secret") as websocket:
            websocket.send_json({"type": "ping"})
            assert websocket.receive_json()["type"] == "pong"
