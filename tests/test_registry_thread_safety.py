import concurrent.futures
import sys
import os
import asyncio
import pytest

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.bridge import ToolRegistry

@pytest.mark.asyncio
async def test_tasks_thread_safety():
    registry = ToolRegistry()
    num_concurrent = 20
    num_ops = 100
    
    # Define an async generator function
    async def mock_async_gen():
        yield 1

    async def worker(worker_id):
        for i in range(num_ops):
            call_id = f"worker-{worker_id}-task-{i}"
            # Create an async generator object
            gen = mock_async_gen()
            await registry.store_task(call_id, gen, "test_tool")
            task_data = await registry.get_task(call_id)
            if task_data["gen"] != gen:
                raise Exception(f"Task mismatch for {call_id}")
            
            # Since get_task marks as consumed but doesn't remove, 
            # we manually remove for this test or just use remove_task
            await registry.remove_task(call_id)
            if await registry.get_task(call_id) is not None:
                raise Exception(f"Task not removed for {call_id}")

    print(f"Starting tasks concurrency test with {num_concurrent} coroutines and {num_ops} ops each...")
    tasks = [worker(i) for i in range(num_concurrent)]
    await asyncio.gather(*tasks)
    print("Tasks concurrency test passed!")

@pytest.mark.asyncio
async def test_registration_thread_safety():
    registry = ToolRegistry()
    num_concurrent = 20
    num_ops = 100
    
    async def worker(worker_id):
        for i in range(num_ops):
            tool_name = f"tool-{worker_id}-{i}"
            
            # Simulate decoration
            def dummy(): pass
            registry.register(name=tool_name)(dummy)
            
            # registry.get_tool returns the validated_func, not dummy.
            tool = registry.get_tool(tool_name)
            if tool is None:
                 raise Exception(f"Tool not found: {tool_name}")
            
            if not callable(tool):
                raise Exception(f"Tool not callable for {tool_name}")

    print(f"Starting registration concurrency test with {num_concurrent} coroutines and {num_ops} ops each...")
    tasks = [worker(i) for i in range(num_concurrent)]
    await asyncio.gather(*tasks)
    print("Registration concurrency test passed!")
