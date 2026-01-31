import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app, WS_MESSAGE_SIZE_LIMIT

@pytest.mark.asyncio
async def test_ws_message_size_limit():
    from fastapi import WebSocketDisconnect
    from starlette.testclient import TestClient
    
    with TestClient(app) as client:
        with client.websocket_connect("/ws?api_key=test-key") as websocket:
            # 1. Test message just below the limit
            small_payload = "a" * (WS_MESSAGE_SIZE_LIMIT - 100)
            message = {"type": "ping", "data": small_payload}
            websocket.send_text(json.dumps(message))
            
            response = websocket.receive_json()
            assert response["type"] == "pong"
            
            # 2. Test message above the limit
            large_payload = "a" * (WS_MESSAGE_SIZE_LIMIT + 100)
            large_message = {"type": "ping", "data": large_payload}
            websocket.send_text(json.dumps(large_message))
            
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "Message too large" in response["payload"]["detail"]

@pytest.mark.asyncio
async def test_ws_invalid_json():
    from starlette.testclient import TestClient
    
    with TestClient(app) as client:
        with client.websocket_connect("/ws?api_key=test-key") as websocket:
            websocket.send_text("not a json")
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "Invalid JSON" in response["payload"]["detail"]

@pytest.mark.asyncio
async def test_ws_non_dict_json():
    from starlette.testclient import TestClient
    
    with TestClient(app) as client:
        with client.websocket_connect("/ws?api_key=test-key") as websocket:
            websocket.send_text(json.dumps([1, 2, 3]))
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "Message must be a JSON object" in response["payload"]["detail"]
