import asyncio
import json
import uuid
import threading
import time
import inspect
from typing import Any, Dict, List, AsyncGenerator, Callable, Literal, Union, Optional
from pydantic import BaseModel, Field, validate_call
from .logger import logger
from .metrics import ACTIVE_TASKS, STALE_TASKS_CLEANED_TOTAL

class ProgressPayload(BaseModel):
    """
    Standard schema for progress updates yielded by tools.
    """
    step: str = Field(
        ..., 
        description="A human-readable label for the current task phase.",
        examples=["Analyzing documents", "Uploading results", "Scanning ports"]
    )
    pct: int = Field(
        ..., 
        ge=0, 
        le=100, 
        description="The completion percentage of the overall task (0-100).",
        examples=[45]
    )
    log: Optional[str] = Field(
        None, 
        description="Detailed log message, breadcrumb, or status update for the current step.",
        examples=["Found 12 matching records in batch 3...", "Port 80 is open", "Processed document 5 of 10"]
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Structured key-value pairs providing additional context for this update.",
        examples=[{"batch_size": 100, "retry_count": 0, "doc_id": "doc_123"}]
    )

class ProgressEvent(BaseModel):
    """
    The event envelope sent over the Server-Sent Events (SSE) stream.
    """
    call_id: str = Field(
        ..., 
        description="The unique identifier for this specific task execution session.",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    type: Literal["progress", "result", "error", "input_request", "task_started"] = Field(
        ..., 
        description="The nature of the event being streamed. 'progress' indicates an interim update, 'result' is the final output, 'error' signifies a failure, and 'input_request' prompts the user for information.",
        examples=["progress", "result", "error", "input_request"]
    )
    timestamp: float = Field(default_factory=time.time, description="Unix timestamp of when the event was created.")
    payload: Union[ProgressPayload, Dict[str, Any]] = Field(
        ..., 
        description="The actual data payload. Contains a ProgressPayload object for 'progress' types, or the final result/error details.",
    )

class InputManager:
    def __init__(self):
        self._pending_inputs: Dict[str, asyncio.Future] = {}
        self._lock = threading.Lock()

    async def wait_for_input(self, call_id: str, prompt: str) -> Any:
        future = asyncio.get_running_loop().create_future()
        with self._lock:
            self._pending_inputs[call_id] = future
        
        logger.info(f"Task {call_id} waiting for input: {prompt}", extra={"call_id": call_id, "prompt": prompt})
        return await future

    def provide_input(self, call_id: str, value: Any):
        with self._lock:
            future = self._pending_inputs.pop(call_id, None)
        
        if future and not future.done():
            future.set_result(value)
            logger.info(f"Provided input for task {call_id}", extra={"call_id": call_id})
            return True
        return False

input_manager = InputManager()

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        # Stores call_id -> {"gen": gen, "tool_name": str, "created_at": timestamp, "consumed": bool}
        self._active_tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def register(self, name: Optional[str] = None):
        def decorator(func: Callable):
            tool_name = name or func.__name__
            
            # Verify it's an async generator
            if not inspect.isasyncgenfunction(func):
                logger.warning(f"Tool {tool_name} is not an async generator function. It might fail during execution.")
            
            # Apply pydantic validation to the tool
            validated_func = validate_call(func)
            with self._lock:
                self._tools[tool_name] = validated_func
            logger.info(f"Tool registered: {tool_name}", extra={"tool_name": tool_name})
            return func
        return decorator

    def list_tools(self) -> List[str]:
        with self._lock:
            return list(self._tools.keys())

    def get_tool(self, name: str):
        with self._lock:
            return self._tools.get(name)

    def store_task(self, call_id: str, gen: AsyncGenerator, tool_name: str):
        # Final safety check: ensure gen is actually an async generator
        if not inspect.isasyncgen(gen):
            # Silence RuntimeWarning for unawaited coroutines if tool was 'async def' but not generator
            if inspect.iscoroutine(gen):
                gen.close()
            raise TypeError(f"Tool {tool_name} did not return an async generator. Got {type(gen)}")

        with self._lock:
            if call_id in self._active_tasks:
                raise ValueError(f"Task with call_id {call_id} already exists")
            self._active_tasks[call_id] = {
                "gen": gen,
                "tool_name": tool_name,
                "created_at": time.time(),
                "consumed": False
            }
            ACTIVE_TASKS.labels(tool_name=tool_name).inc()
        logger.debug(f"Task stored in registry: {call_id}", extra={"call_id": call_id, "tool_name": tool_name})

    def get_task(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the task data and marks it as consumed."""
        with self._lock:
            task_data = self._active_tasks.get(call_id)
            if task_data and not task_data["consumed"]:
                task_data["consumed"] = True
                return task_data
            return None
    
    def mark_consumed(self, call_id: str):
        """Marks a task as consumed without retrieving it. Used for WebSocket tasks."""
        with self._lock:
            task_data = self._active_tasks.get(call_id)
            if task_data:
                task_data["consumed"] = True
                logger.debug(f"Task marked as consumed: {call_id}", extra={"call_id": call_id})

    def get_task_no_consume(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the task data without marking it as consumed."""
        with self._lock:
            return self._active_tasks.get(call_id)

    def remove_task(self, call_id: str):
        """Removes the task from the registry if it exists."""
        with self._lock:
            task_data = self._active_tasks.get(call_id)
            if task_data:
                tool_name = task_data["tool_name"]
                ACTIVE_TASKS.labels(tool_name=tool_name).dec()
                del self._active_tasks[call_id]
                logger.debug(f"Task removed from registry: {call_id}", extra={"call_id": call_id})

    async def cleanup_tasks(self):
        """Closes all active generators currently in the registry."""
        with self._lock:
            tasks = list(self._active_tasks.items())
        
        if tasks:
            logger.info(f"Cleaning up {len(tasks)} active tasks during shutdown")
        
        for call_id, task_data in tasks:
            gen = task_data["gen"]
            tool_name = task_data["tool_name"]
            try:
                await gen.aclose()
            except Exception as e:
                logger.error(f"Error closing generator {call_id}: {e}", extra={"call_id": call_id, "tool_name": tool_name})
            finally:
                self.remove_task(call_id)

    async def cleanup_stale_tasks(self, max_age_seconds: int):
        """Closes tasks that were created more than max_age_seconds ago and never consumed."""
        now = time.time()
        stale_tasks = []
        
        with self._lock:
            for call_id, task_data in self._active_tasks.items():
                if not task_data["consumed"] and now - task_data["created_at"] > max_age_seconds:
                    stale_tasks.append((call_id, task_data["gen"], task_data["tool_name"]))
        
        if not stale_tasks:
            return

        logger.info(f"Cleaning up {len(stale_tasks)} stale tasks")
        for call_id, gen, tool_name in stale_tasks:
            try:
                await gen.aclose()
            except Exception as e:
                logger.error(f"Error closing stale generator {call_id}: {e}", extra={"call_id": call_id, "tool_name": tool_name})
            finally:
                self.remove_task(call_id)
                STALE_TASKS_CLEANED_TOTAL.inc()

registry = ToolRegistry()

def progress_tool(name: Optional[str] = None):
    """
    Decorator to register an async generator as a tool.
    The generator should yield ProgressPayload objects and finally a Dict for result.
    """
    return registry.register(name)

async def format_sse(event: ProgressEvent) -> str:
    """Formats a ProgressEvent as an SSE data string."""
    return f"data: {event.model_dump_json()}\n\n"