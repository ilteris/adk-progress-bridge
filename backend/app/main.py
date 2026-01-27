import asyncio
import uuid
import time
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Body, Path as FastAPIPath
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError
from .bridge import registry, ProgressEvent, format_sse, ProgressPayload
from .context import call_id_var, tool_name_var
from .logger import logger
from .metrics import get_metrics, TASK_DURATION, TASKS_TOTAL, TASK_PROGRESS_STEPS_TOTAL

class StartTaskResponse(BaseModel):
    """
    Response returned after successfully starting a task.
    """
    call_id: str = Field(
        ..., 
        description="The unique identifier (UUID) for the started task session. Use this to connect to the /stream/{call_id} endpoint.",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )

async def cleanup_loop(max_age: int = 300, interval: int = 60):
    """Background loop to clean up stale tasks."""
    logger.info(f"Starting stale task cleanup loop (interval: {interval}s, max_age: {max_age}s)")
    while True:
        try:
            await asyncio.sleep(interval)
            await registry.cleanup_stale_tasks(max_age)
        except asyncio.CancelledError:
            logger.info("Cleanup loop cancelled")
            break
        except Exception as e:
            logger.error(f"Error in cleanup loop: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start cleanup loop
    logger.info("Application starting up")
    cleanup_task = asyncio.create_task(cleanup_loop())
    yield
    # Stop cleanup loop
    logger.info("Application shutting down")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    # Shutdown logic: Close all active generators
    await registry.cleanup_tasks()

app = FastAPI(
    title="ADK Progress Bridge",
    description="""
A real-time bridge for Google Agent Development Kit (ADK) tools. 
Transforms long-running backend tasks into streaming Server-Sent Events (SSE) 
to provide immediate feedback to the frontend.

### Key Features:
* **Tool Execution**: Start any registered tool with arbitrary arguments.
* **Progress Streaming**: Receive granular progress updates, logs, and metadata via SSE.
* **Observability**: Built-in Prometheus metrics and structured logging.
* **Resilience**: Automatic cleanup of stale sessions and graceful shutdown.
""",
    version="1.0.0",
    contact={
        "name": "Teddy",
        "url": "https://github.com/google-marketing-solutions/adk-progress-bridge",
    },
    license_info={
        "name": "MIT",
    },
    lifespan=lifespan
)

# Enable CORS for Vue.js development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get(
    "/metrics", 
    summary="Get Prometheus Metrics",
    description="Exposes application metrics in Prometheus format for monitoring.",
    tags=["Observability"]
)
async def metrics():
    return get_metrics()

@app.post(
    "/start_task/{tool_name}", 
    response_model=StartTaskResponse,
    summary="Start a Tool Task",
    description="Initializes a registered tool with the provided arguments and returns a session call_id.",
    tags=["Execution"],
    responses={
        404: {"description": "Tool not found in registry"},
        400: {"description": "Invalid arguments provided for the tool"}
    }
)
async def start_task(
    tool_name: str = FastAPIPath(..., description="The name of the registered tool to execute."), 
    args: Dict[str, Any] = Body(default={}, description="Key-value pairs of arguments to pass to the tool function.", examples=[{"duration": 10}])
):
    # Set tool name in context for this request
    tool_name_var.set(tool_name)
    
    tool = registry.get_tool(tool_name)
    if not tool:
        logger.warning(f"Tool not found: {tool_name}")
        raise HTTPException(status_code=404, detail="Tool not found")
    
    try:
        # Instantiate the generator (will trigger validation via pydantic.validate_call)
        gen = tool(**args)
    except ValidationError as e:
        logger.warning(f"Validation error for tool {tool_name}: {e.errors()}")
        raise HTTPException(status_code=400, detail=e.errors())
    except TypeError as e:
        # Fallback for other argument-related errors
        logger.warning(f"Argument error for tool {tool_name}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    call_id = str(uuid.uuid4())
    registry.store_task(call_id, gen, tool_name)
    
    logger.info(f"Task started: {tool_name}", extra={"call_id": call_id})
    return StartTaskResponse(call_id=call_id)

@app.get(
    "/stream/{call_id}", 
    summary="Stream Task Progress",
    description="""
Connect to this endpoint via EventSource (SSE) to receive progress updates for a previously started task.
The stream yields events of type 'progress', 'result', or 'error'.
""",
    tags=["Execution"],
    responses={
        200: {
            "description": "SSE Stream of ProgressEvent objects.",
            "model": ProgressEvent
        },
        404: {"description": "Task not found or already consumed."}
    }
)
async def stream_task(
    call_id: str = FastAPIPath(..., description="The unique session ID returned by the /start_task endpoint.")
):
    # We set call_id context for the request
    call_id_var.set(call_id)
    
    task_data = registry.get_task(call_id)
    if not task_data:
        logger.warning(f"Task not found or already consumed: {call_id}")
        raise HTTPException(status_code=404, detail="Task not found or already consumed")

    gen = task_data["gen"]
    tool_name = task_data["tool_name"]
    
    # Set tool_name context for the request
    tool_name_var.set(tool_name)

    async def event_generator():
        # Set context inside the generator to ensure logs from tool have it
        call_id_var.set(call_id)
        tool_name_var.set(tool_name)
        
        start_time = time.perf_counter()
        status = "success"
        
        logger.info(f"Starting stream for task: {call_id}")
        try:
            async for item in gen:
                if isinstance(item, ProgressPayload):
                    TASK_PROGRESS_STEPS_TOTAL.labels(tool_name=tool_name).inc()
                    event = ProgressEvent(call_id=call_id, type="progress", payload=item)
                else:
                    # Final result
                    event = ProgressEvent(call_id=call_id, type="result", payload=item)
                yield await format_sse(event)
        except Exception as e:
            status = "error"
            logger.error(f"Error during streaming task {call_id}: {e}")
            event = ProgressEvent(call_id=call_id, type="error", payload={"detail": str(e)})
            yield await format_sse(event)
        finally:
            duration = time.perf_counter() - start_time
            TASK_DURATION.labels(tool_name=tool_name).observe(duration)
            TASKS_TOTAL.labels(tool_name=tool_name, status=status).inc()
            
            logger.info(f"Stream finished for task: {call_id} (duration: {duration:.2f}s, status: {status})")
            registry.remove_task(call_id)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Import tools to register them
from . import dummy_tool