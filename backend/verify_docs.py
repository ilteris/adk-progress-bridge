import json
import sys
import os
from unittest.mock import MagicMock

# Mock prometheus_client before importing app.main
mock_prometheus = MagicMock()
sys.modules["prometheus_client"] = mock_prometheus

# Ensure we are in the right directory to import 'app'
sys.path.append(os.path.join(os.path.dirname(__file__), "."))
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
    security_schemes = components.get("securitySchemes", {})
    
    # Check Security Schemes
    assert "APIKeyHeader" in security_schemes, "Security scheme APIKeyHeader not found"
    assert security_schemes["APIKeyHeader"]["type"] == "apiKey"
    assert security_schemes["APIKeyHeader"]["name"] == "X-API-Key"
    assert security_schemes["APIKeyHeader"]["in"] == "header"

    # Check Endpoints for Security
    paths = schema.get("paths", {})
    
    start_task_post = paths.get("/start_task/{tool_name}", {}).get("post", {})
    assert "security" in start_task_post, "Start task endpoint should have security defined"
    assert any("APIKeyHeader" in s for s in start_task_post["security"])
    assert "401" in start_task_post["responses"], "Start task should have 401 response"

    stream_get = paths.get("/stream/{call_id}", {}).get("get", {})
    # Note: verify_api_key_sse uses Depends but we might not see it as 'security' 
    # if it's a plain Depends and not Security(...).
    # But we added it to responses in main.py.
    assert "401" in stream_get["responses"], "Stream task should have 401 response"

    print("Verification successful!")

if __name__ == "__main__":
    generate_openapi()