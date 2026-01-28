import threading
import concurrent.futures
import sys
import os

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.bridge import ToolRegistry

def test_tasks_thread_safety():
    registry = ToolRegistry()
    num_threads = 20
    num_ops = 1000
    
    # Define an async generator function
    async def mock_async_gen():
        yield 1

    def worker(worker_id):
        for i in range(num_ops):
            call_id = f"worker-{worker_id}-task-{i}"
            # Create an async generator object
            gen = mock_async_gen()
            registry.store_task(call_id, gen, "test_tool")
            task_data = registry.get_task(call_id)
            if task_data["gen"] != gen:
                raise Exception(f"Task mismatch for {call_id}")
            
            # Since get_task marks as consumed but doesn't remove, 
            # we manually remove for this test or just use remove_task
            registry.remove_task(call_id)
            if registry.get_task(call_id) is not None:
                raise Exception(f"Task not removed for {call_id}")

    print(f"Starting tasks thread safety test with {num_threads} threads and {num_ops} ops each...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker, i) for i in range(num_threads)]
        for future in concurrent.futures.as_completed(futures):
            future.result()

    print("Tasks thread safety test passed!")

def test_registration_thread_safety():
    registry = ToolRegistry()
    num_threads = 20
    num_ops = 500
    
    def worker(worker_id):
        for i in range(num_ops):
            tool_name = f"tool-{worker_id}-{i}"
            
            # Simulate decoration
            def dummy(): pass
            registry.register(name=tool_name)(dummy)
            
            # registry.get_tool returns the validated_func, not dummy.
            # But the .func attribute of the validated_func should be dummy
            tool = registry.get_tool(tool_name)
            if tool is None:
                 raise Exception(f"Tool not found: {tool_name}")
            
            # validate_call wrapped function has the original in .__wrapped__ or we can just check if it's callable
            if not callable(tool):
                raise Exception(f"Tool not callable for {tool_name}")

    print(f"Starting registration thread safety test with {num_threads} threads and {num_ops} ops each...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker, i) for i in range(num_threads)]
        for future in concurrent.futures.as_completed(futures):
            future.result()

    print("Registration thread safety test passed!")

if __name__ == "__main__":
    try:
        test_tasks_thread_safety()
        test_registration_thread_safety()
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)