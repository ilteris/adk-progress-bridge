import asyncio
import json
import uuid
from typing import Any, Dict, AsyncGenerator, Callable, Literal, Union, Optional
from pydantic import BaseModel, Field

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
        self._active_tasks: Dict[str, AsyncGenerator] = {}

    def register(self, name: Optional[str] = None):
        def decorator(func: Callable):
            tool_name = name or func.__name__
            self._tools[tool_name] = func
            return func
        return decorator

    def get_tool(self, name: str):
        return self._tools.get(name)

    def store_task(self, call_id: str, gen: AsyncGenerator):
        self._active_tasks[call_id] = gen

    def get_task(self, call_id: str) -> Optional[AsyncGenerator]:
        return self._active_tasks.get(call_id)
    
    def remove_task(self, call_id: str):
        if call_id in self._active_tasks:
            del self._active_tasks[call_id]

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
