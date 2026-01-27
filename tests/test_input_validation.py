import asyncio
import sys
import os
import pytest
from pydantic import ValidationError

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.bridge import ToolRegistry, ProgressPayload

@pytest.mark.asyncio
async def test_registry_validation():
    registry = ToolRegistry()
    
    @registry.register(name="test_tool")
    async def test_tool(duration: int, name: str = "test"):
        yield ProgressPayload(step="start", pct=0)
        yield {"result": "ok"}

    tool = registry.get_tool("test_tool")
    gen = tool(duration=10)
    async for _ in gen:
        pass

    with pytest.raises(ValidationError):
        tool(duration="not an int")

    with pytest.raises(ValidationError):
        tool(name="hello")