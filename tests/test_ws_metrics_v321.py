import pytest
from backend.app.main import app, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX, MAX_CONCURRENT_TASKS

import asyncio
import json
from fastapi.testclient import TestClient

def test_ws_message_counters():
    client = TestClient(app)
    
    # Check initial metrics
    response = client.get("/health")
    data = response.json()
    initial_received = data["ws_messages_received"]
    initial_sent = data["ws_messages_sent"]
    
    with client.websocket_connect("/ws?api_key=test-api-key") as websocket:
        # Send ping
        websocket.send_json({"type": "ping"})
        msg = websocket.receive_json()
        assert msg["type"] == "pong"
        
        # Send list_tools
        websocket.send_json({"type": "list_tools"})
        msg = websocket.receive_json()
        assert msg["type"] == "tools_list"
        
    # Check updated metrics
    response = client.get("/health")
    data = response.json()
    # 2 more received (ping, list_tools)
    # 2 more sent (pong, tools_list)
    assert data["ws_messages_received"] == initial_received + 2
    assert data["ws_messages_sent"] == initial_sent + 2
    
    # Check prometheus metrics
    response = client.get("/metrics")
    # We can't easily check absolute values in /metrics if other tests ran,
    # but we can check if the labels are present.
    assert 'adk_ws_messages_received_total{message_type="ping"}' in response.text
    assert 'adk_ws_messages_received_total{message_type="list_tools"}' in response.text
    assert 'adk_ws_messages_sent_total{message_type="pong"}' in response.text
    assert 'adk_ws_messages_sent_total{message_type="tools_list"}' in response.text