import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
import json

def test_ws_v663_new_tools_availability():
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        # Initial connected message
        conn_msg = websocket.receive_json()
        assert conn_msg["type"] == "connected"
        
        # Request list of tools
        websocket.send_json({"type": "list_tools"})
        response = websocket.receive_json()
        assert response["type"] == "tools_list"
        tools = response["tools"]
        
        assert "system_disk_io_write_time_audit" in tools
        assert "system_disk_io_busy_time_audit" in tools
        assert "system_cpu_times_percent_idle_focused_audit" in tools

def test_ws_v663_system_disk_io_write_time_audit():
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        # Initial connected message
        websocket.receive_json()
        
        websocket.send_json({
            "type": "start",
            "tool_name": "system_disk_io_write_time_audit",
            "args": {"samples": 1}
        })
        
        # Expect task_started
        response = websocket.receive_json()
        assert response["type"] == "task_started"
        
        # Receive progress and final result
        messages = []
        while True:
            msg = websocket.receive_json()
            messages.append(msg)
            if msg["type"] == "result":
                break
        
        assert any(m["type"] == "progress" for m in messages)
        final_msg = messages[-1]
        assert "final_write_time" in final_msg["payload"]

def test_ws_v663_system_disk_io_busy_time_audit():
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        # Initial connected message
        websocket.receive_json()
        
        websocket.send_json({
            "type": "start",
            "tool_name": "system_disk_io_busy_time_audit",
            "args": {"samples": 1}
        })
        
        # Expect task_started
        response = websocket.receive_json()
        assert response["type"] == "task_started"
        
        # Receive progress and final result
        messages = []
        while True:
            msg = websocket.receive_json()
            messages.append(msg)
            if msg["type"] == "result":
                break
        
        assert any(m["type"] == "progress" for m in messages)
        final_msg = messages[-1]
        assert "final_busy_time" in final_msg["payload"]

def test_ws_v663_system_cpu_times_percent_idle_focused_audit():
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        # Initial connected message
        websocket.receive_json()
        
        websocket.send_json({
            "type": "start",
            "tool_name": "system_cpu_times_percent_idle_focused_audit",
            "args": {"samples": 1}
        })
        
        # Expect task_started
        response = websocket.receive_json()
        assert response["type"] == "task_started"
        
        # Receive progress and final result
        messages = []
        while True:
            msg = websocket.receive_json()
            messages.append(msg)
            if msg["type"] == "result":
                break
        
        assert any(m["type"] == "progress" for m in messages)
        final_msg = messages[-1]
        assert "final_idle_percent" in final_msg["payload"]