import sys
import os
import json
import pytest
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app

def test_deep_health_check_tool_ws():
    """
    Verifies that the new deep_health_check tool works over WebSocket.
    """
    with TestClient(app) as client:
        with client.websocket_connect("/ws?api_key=test_key") as websocket:
            data = websocket.receive_json()
            print(f"Received: {data['type']}")
            assert data["type"] == "connected"
            
            request_id = "v590-health-test"
            websocket.send_json({
                "type": "start",
                "tool_name": "deep_health_check",
                "request_id": request_id
            })
            
            progress_received = False
            result_received = False
            
            for i in range(50):
                data = websocket.receive_json()
                print(f"Message {i}: {data.get('type')} {data.get('payload', {}).get('step') if data.get('type') == 'progress' else ''}")
                
                if data["type"] == "task_started":
                    assert data["request_id"] == request_id
                    call_id = data["call_id"]
                elif data["type"] == "progress":
                    progress_received = True
                elif data["type"] == "result":
                    assert data["payload"]["status"] == "healthy"
                    assert "snapshot" in data["payload"]
                    result_received = True
                    break
                elif data["type"] == "error":
                    print(f"Error received: {data['payload']}")
                    break
            
            assert progress_received, "Did not receive progress updates"
            assert result_received, "Did not receive final result"

def test_v590_metadata_verification():
    """
    Verifies that the version and metadata are correctly updated for v590.
    """
    with TestClient(app) as client:
        response = client.get("/version")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "2.1.6"
        assert "v590" in data["git_commit"]
        assert "v590" in data["status"]