import asyncio
import sys
import os
import time
import pytest

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.bridge import ToolRegistry

@pytest.mark.asyncio
async def test_timeout_cleanup():
    registry = ToolRegistry()
    
    async def mock_gen():
        try:
            yield "data"
            await asyncio.sleep(10)
        except GeneratorExit:
            raise

    call_id = "test-timeout-task"
    gen = mock_gen()
    
    # Advance to first yield
    await gen.__anext__()
    
    registry.store_task(call_id, gen, "mock_tool")
    
    assert registry._active_tasks.get(call_id) is not None
    
    # Run cleanup with max_age=0.1s after waiting 0.2s
    await asyncio.sleep(0.2)
    
    await registry.cleanup_stale_tasks(max_age_seconds=0.1)
    
    assert registry.get_task(call_id) is None

@pytest.mark.asyncio
async def test_get_task_pops():
    registry = ToolRegistry()
    
    async def mock_gen():
        yield "data"

    call_id = "test-pop-task"
    gen = mock_gen()
    registry.store_task(call_id, gen, "mock_tool")
    
    assert call_id in registry._active_tasks
    
    task_data = registry.get_task(call_id)
    assert task_data["gen"] == gen
    
    # get_task marks it as consumed, but doesn't remove it from _active_tasks immediately.
    # removal happens in remove_task which is called by the stream finally block.
    assert call_id in registry._active_tasks
    assert registry._active_tasks[call_id]["consumed"] is True
    
    # Second call should return None
    assert registry.get_task(call_id) is None
