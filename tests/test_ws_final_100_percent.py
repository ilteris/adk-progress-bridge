import sys
import os
import json
import pytest
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app

def test_websocket_list_tools_comprehensive():
    """
    Final test to reach 100 total tests.
    Verifies that list_tools over WebSocket returns the expected set of tools.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        websocket.send_json({
            "type": "list_tools",
            "request_id": "final_100"
        })
        
        data = websocket.receive_json()
        assert data["type"] == "tools_list"
        assert data["request_id"] == "final_100"
        assert isinstance(data["tools"], list)
        # Verify a few known tools are present
        expected_tools = {"long_audit", "security_scan", "multi_stage_analysis"}
        assert expected_tools.issubset(set(data["tools"]))
        print(f"\n[SIGN-OFF] Verified {len(data['tools'])} tools via WebSocket.")

if __name__ == "__main__":
    pytest.main([__file__])

