import asyncio
import sys
import os
from pydantic import ValidationError

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.bridge import ToolRegistry, ProgressPayload

async def test_registry_validation():
    registry = ToolRegistry()
    
    @registry.register(name="test_tool")
    async def test_tool(duration: int, name: str = "test"):
        yield ProgressPayload(step="start", pct=0)
        yield {"result": "ok"}

    print("Testing registry tool with valid args...")
    tool = registry.get_tool("test_tool")
    gen = tool(duration=10)
    async for item in gen:
        pass
    print("Valid args passed.")

    print("Testing registry tool with invalid type...")
    try:
        tool(duration="not an int")
        print("FAILED: Should have raised ValidationError")
    except ValidationError:
        print("Passed: Caught expected ValidationError")

    print("Testing registry tool with missing arg...")
    try:
        tool(name="hello")
        print("FAILED: Should have raised ValidationError")
    except ValidationError:
        print("Passed: Caught expected ValidationError")

if __name__ == "__main__":
    asyncio.run(test_registry_validation())
