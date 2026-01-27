import json
import sys
from unittest.mock import MagicMock

# Mock prometheus_client before importing app.main
mock_prometheus = MagicMock()
sys.modules["prometheus_client"] = mock_prometheus

# Also mock app.metrics if needed or let it import and use the mocked prometheus_client
# Ensure we are in the right directory to import 'app'
sys.path.append(".")
from app.main import app

def generate_openapi():
    # FastAPI's openapi() function generates the schema
    schema = app.openapi()
    
    # Save to a file for inspection
    with open("openapi_check.json", "w") as f:
        json.dump(schema, f, indent=2)
    
    print("OpenAPI schema saved to openapi_check.json")
    
    # Simple assertions to verify our changes
    components = schema.get("components", {})
    schemas = components.get("schemas", {})
    
    # Check ProgressPayload
    payload_schema = schemas.get("ProgressPayload")
    assert payload_schema is not None, "ProgressPayload schema not found"
    assert "description" in payload_schema, "ProgressPayload should have a description"
    assert "step" in payload_schema["properties"], "ProgressPayload should have 'step'"
    assert "description" in payload_schema["properties"]["step"], "ProgressPayload.step should have a description"
    
    # Check StartTaskResponse (Updated name)
    start_resp = schemas.get("StartTaskResponse")
    assert start_resp is not None, "StartTaskResponse schema not found"
    assert "call_id" in start_resp["properties"]
    assert "description" in start_resp["properties"]["call_id"]
    
    # Check Endpoints
    paths = schema.get("paths", {})
    start_task_path = paths.get("/start_task/{tool_name}")
    assert start_task_path is not None
    assert "post" in start_task_path
    # Updated summary to match implementation
    assert start_task_path["post"]["summary"] == "Start a Tool Task"
    
    stream_path = paths.get("/stream/{call_id}")
    assert stream_path is not None
    assert "get" in stream_path
    # Updated summary to match implementation
    assert stream_path["get"]["summary"] == "Stream Task Progress"

    # Check for general app info
    assert schema["info"]["title"] == "ADK Progress Bridge"
    assert "description" in schema["info"]
    assert schema["info"]["version"] == "1.0.0"

    print("Verification successful!")

if __name__ == "__main__":
    generate_openapi()
