import asyncio
import json
import uuid
import threading
import time
from typing import Any, Dict, AsyncGenerator, Callable, Literal, Union, Optional
from pydantic import BaseModel, Field, validate_call
from .logger import logger

class ProgressPayload(BaseModel):
    step: str
    pct: int = Field(ge=0, le=100)
    log: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ProgressEvent(BaseModel):
    call_id: str
    type: Literal["progress", "result", "error"]
    payload: Union[ProgressPayload, Dict[str, Any]]

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        # Stores call_id -> {"gen": gen, "created_at": timestamp, "consumed": bool}
        self._active_tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def register(self, name: Optional[str] = None):
        def decorator(func: Callable):
            tool_name = name or func.__name__
            # Apply pydantic validation to the tool
            validated_func = validate_call(func)
            with self._lock:
                self._tools[tool_name] = validated_func
            logger.info(f"Tool registered: {tool_name}", extra={"tool_name": tool_name})
            return func
        return decorator

    def get_tool(self, name: str):
        with self._lock:
            return self._tools.get(name)

    def store_task(self, call_id: str, gen: AsyncGenerator):
        with self._lock:
            self._active_tasks[call_id] = {
                "gen": gen,
                "created_at": time.time(),
                "consumed": False
            }
        logger.debug(f"Task stored in registry: {call_id}", extra={"call_id": call_id})

    def get_task(self, call_id: str) -> Optional[AsyncGenerator]:
        """Retrieves the task and marks it as consumed."""
        with self._lock:
            task_data = self._active_tasks.get(call_id)
            if task_data and not task_data["consumed"]:
                task_data["consumed"] = True
                return task_data["gen"]
            return None
    
    def remove_task(self, call_id: str):
        """Removes the task from the registry if it exists."""
        with self._lock:
            if call_id in self._active_tasks:
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
            try:
                await gen.aclose()
            except Exception as e:
                logger.error(f"Error closing generator {call_id}: {e}", extra={"call_id": call_id})
            finally:
                self.remove_task(call_id)

    async def cleanup_stale_tasks(self, max_age_seconds: int):
        """Closes tasks that were created more than max_age_seconds ago and never consumed."""
        now = time.time()
        stale_tasks = []
        
        with self._lock:
            for call_id, task_data in self._active_tasks.items():
                if not task_data["consumed"] and now - task_data["created_at"] > max_age_seconds:
                    stale_tasks.append((call_id, task_data["gen"]))
        
        if not stale_tasks:
            return

        logger.info(f"Cleaning up {len(stale_tasks)} stale tasks")
        for call_id, gen in stale_tasks:
            try:
                await gen.aclose()
            except Exception as e:
                logger.error(f"Error closing stale generator {call_id}: {e}", extra={"call_id": call_id})
            finally:
                self.remove_task(call_id)

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