import asyncio
from typing import Any, Dict, List, AsyncGenerator, Callable, Literal, Union, Optional, Set
from pydantic import BaseModel, Field, validate_call
from .logger import logger
from .metrics import ACTIVE_TASKS, PEAK_ACTIVE_TASKS, STALE_TASKS_CLEANED_TOTAL, TOTAL_TASKS_STARTED

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
    type: Literal["progress", "result", "error", "input_request", "task_started", "system_metrics"] = Field(
        ..., 
        description="The nature of the event being streamed.",
        examples=["progress", "result", "error", "input_request"]
    )
    payload: Union[ProgressPayload, Dict[str, Any]] = Field(
        ..., 
        description="The actual data payload.",
    )

class InputManager:
    def __init__(self):
        self._pending_inputs: Dict[str, asyncio.Future] = {}
        self._lock = asyncio.Lock()

    async def wait_for_input(self, call_id: str, prompt: str) -> Any:
        future = asyncio.get_running_loop().create_future()
        async with self._lock:
            self._pending_inputs[call_id] = future
        
        logger.info(f"Task {call_id} waiting for input: {prompt}", extra={"call_id": call_id, "prompt": prompt})
        return await future

    async def provide_input(self, call_id: str, value: Any):
        async with self._lock:
            future = self._pending_inputs.pop(call_id, None)
        
        if future and not future.done():
            future.set_result(value)
            logger.info(f"Provided input for task {call_id}", extra={"call_id": call_id})
            return True
        return False

input_manager = InputManager()

class TaskBroadcaster:
    """
    Consumes an async generator and broadcasts events to multiple subscribers.
    Also maintains a buffer of events for late subscribers.
    """
    def __init__(self, call_id: str, tool_name: str, gen: AsyncGenerator):
        self.call_id = call_id
        self.tool_name = tool_name
        self.gen = gen
        self.history: List[ProgressEvent] = []
        self.subscribers: Set[asyncio.Queue] = set()
        self.is_done = False
        self.final_event: Optional[ProgressEvent] = None
        self.task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def start(self):
        self.task = asyncio.create_task(self._run())

    async def _run(self):
        try:
            async for item in self.gen:
                if isinstance(item, ProgressPayload):
                    event = ProgressEvent(call_id=self.call_id, type="progress", payload=item)
                elif isinstance(item, dict) and item.get("type") == "input_request":
                    event = ProgressEvent(call_id=self.call_id, type="input_request", payload=item["payload"])
                else:
                    event = ProgressEvent(call_id=self.call_id, type="result", payload=item)
                
                async with self._lock:
                    self.history.append(event)
                    if event.type == "result":
                        self.final_event = event
                        self.is_done = True
                    
                    for q in list(self.subscribers):
                        await q.put(event)
                
                if self.is_done:
                    break
        except asyncio.CancelledError:
            await self.gen.aclose()
            event = ProgressEvent(call_id=self.call_id, type="error", payload={"detail": "Task cancelled"})
            async with self._lock:
                self.final_event = event
                self.is_done = True
                for q in list(self.subscribers):
                    await q.put(event)
        except Exception as e:
            logger.error(f"Error in task {self.call_id}: {e}")
            event = ProgressEvent(call_id=self.call_id, type="error", payload={"detail": str(e)})
            async with self._lock:
                self.history.append(event)
                self.final_event = event
                self.is_done = True
                for q in list(self.subscribers):
                    await q.put(event)
        finally:
            self.is_done = True

    async def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue()
        async with self._lock:
            # Replay history
            for event in self.history:
                await q.put(event)
            
            if not self.is_done:
                self.subscribers.add(q)
            elif self.final_event and self.final_event not in self.history:
                 await q.put(self.final_event)
            
            # If done, put a sentinel or the final event is already there
        return q

    def unsubscribe(self, q: asyncio.Queue):
        if q in self.subscribers:
            self.subscribers.remove(q)

    async def stop(self):
        if self.task:
            self.task.cancel()
            await self.gen.aclose()

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        # Stores call_id -> {"broadcaster": broadcaster, "created_at": timestamp, "consumed": bool}
        self._active_tasks: Dict[str, Dict[str, Any]] = {}
        self._total_tasks_started = 0
        self._peak_active_tasks = 0
        self._lock = asyncio.Lock()

    def register(self, name: Optional[str] = None):
        import inspect
        def decorator(func: Callable):
            tool_name = name or func.__name__
            if not inspect.isasyncgenfunction(func):
                logger.warning(f"Tool {tool_name} is not an async generator function.")
            validated_func = validate_call(func)
            self._tools[tool_name] = validated_func
            logger.info(f"Tool registered: {tool_name}")
            return func
        return decorator

    @property
    def active_task_count(self) -> int:
        return len(self._active_tasks)

    @property
    def total_tasks_started(self) -> int:
        return self._total_tasks_started
    
    @property
    def peak_active_tasks(self) -> int:
        return self._peak_active_tasks

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())

    async def list_active_tasks(self) -> List[Dict[str, Any]]:
        async with self._lock:
            return [
                {
                    "call_id": call_id,
                    "tool_name": data["broadcaster"].tool_name,
                    "created_at": data["created_at"],
                    "consumed": data["consumed"]
                }
                for call_id, data in self._active_tasks.items()
            ]

    def get_tool(self, name: str):
        return self._tools.get(name)

    async def store_task(self, call_id: str, gen: AsyncGenerator, tool_name: str):
        import time
        broadcaster = TaskBroadcaster(call_id, tool_name, gen)
        async with self._lock:
            self._active_tasks[call_id] = {
                "broadcaster": broadcaster,
                "created_at": time.time(),
                "consumed": False
            }
            ACTIVE_TASKS.labels(tool_name=tool_name).inc()
            self._total_tasks_started += 1
            TOTAL_TASKS_STARTED.inc()
            
            current_count = len(self._active_tasks)
            if current_count > self._peak_active_tasks:
                self._peak_active_tasks = current_count
                PEAK_ACTIVE_TASKS.set(current_count)
        
        await broadcaster.start()
        logger.debug(f"Task stored and broadcaster started: {call_id}")

    async def get_broadcaster(self, call_id: str) -> Optional[TaskBroadcaster]:
        async with self._lock:
            task_data = self._active_tasks.get(call_id)
            if task_data:
                task_data["consumed"] = True
                return task_data["broadcaster"]
            return None

    async def get_task_no_consume(self, call_id: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            return self._active_tasks.get(call_id)

    async def remove_task(self, call_id: str):
        async with self._lock:
            task_data = self._active_tasks.pop(call_id, None)
            if task_data:
                tool_name = task_data["broadcaster"].tool_name
                ACTIVE_TASKS.labels(tool_name=tool_name).dec()
                # We don't necessarily stop the broadcaster here, 
                # because we want it to finish and then be cleaned up?
                # Actually, if we remove it, it should probably stop.
                await task_data["broadcaster"].stop()
                logger.info(f"Task removed from registry: {call_id}")

    async def cleanup_tasks(self):
        async with self._lock:
            tasks = list(self._active_tasks.items())
        for call_id, task_data in tasks:
            await task_data["broadcaster"].stop()
            await self.remove_task(call_id)

    async def cleanup_stale_tasks(self, max_age_seconds: int):
        import time
        now = time.time()
        stale_tasks = []
        async with self._lock:
            for call_id, task_data in self._active_tasks.items():
                if task_data["broadcaster"].is_done and now - task_data["created_at"] > max_age_seconds:
                    stale_tasks.append(call_id)
                elif not task_data["consumed"] and now - task_data["created_at"] > max_age_seconds:
                    stale_tasks.append(call_id)
        
        for call_id in stale_tasks:
            await self.remove_task(call_id)
            STALE_TASKS_CLEANED_TOTAL.inc()

registry = ToolRegistry()

def progress_tool(name: Optional[str] = None):
    def decorator(func: Callable):
        tool_name = name or func.__name__
        validated_func = validate_call(func)
        registry._tools[tool_name] = validated_func
        logger.info(f"Tool registered: {tool_name}")
        return func
    return decorator

async def format_sse(event: ProgressEvent) -> str:
    return f"data: {event.model_dump_json()}\n\n"
