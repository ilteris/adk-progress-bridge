import asyncio
import sys
import os
import time

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.bridge import ToolRegistry

async def test_timeout_cleanup():
    registry = ToolRegistry()
    
    async def mock_gen():
        print("Generator started", flush=True)
        try:
            yield "data"
            await asyncio.sleep(10)
        except GeneratorExit:
            print("Generator closed (GeneratorExit)", flush=True)
            raise
        finally:
            print("Generator finally block reached", flush=True)

    call_id = "test-timeout-task"
    gen = mock_gen()
    
    # Advance to first yield
    await gen.__anext__()
    
    registry.store_task(call_id, gen)
    
    print("Task stored and advanced. Verifying it exists...", flush=True)
    assert registry._active_tasks.get(call_id) is not None
    
    print("Running cleanup with max_age=1s after waiting 2s...", flush=True)
    await asyncio.sleep(2)
    
    await registry.cleanup_stale_tasks(max_age_seconds=1)
    
    print("Verifying task is removed...", flush=True)
    assert registry.get_task(call_id) is None
    print("Cleanup test passed!", flush=True)

async def test_get_task_pops():
    registry = ToolRegistry()
    
    async def mock_gen():
        yield "data"

    call_id = "test-pop-task"
    gen = mock_gen()
    registry.store_task(call_id, gen)
    
    print("Task stored. Verifying it exists...", flush=True)
    assert call_id in registry._active_tasks
    
    print("Retrieving task...", flush=True)
    retrieved_gen = registry.get_task(call_id)
    assert retrieved_gen == gen
    
    print("Verifying task is popped from registry...", flush=True)
    assert call_id not in registry._active_tasks
    print("Pop test passed!", flush=True)

if __name__ == "__main__":
    asyncio.run(test_timeout_cleanup())
    asyncio.run(test_get_task_pops())