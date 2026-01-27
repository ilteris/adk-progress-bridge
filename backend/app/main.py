import asyncio
import json
import uuid
import time
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Query, Request, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .bridge import registry, ProgressEvent, ProgressPayload, format_sse, input_manager
from .logger import logger
from .context import call_id_var, tool_name_var
from .auth import verify_api_key, verify_api_key_ws
from .metrics import TASK_DURATION, TASKS_TOTAL, TASK_PROGRESS_STEPS_TOTAL

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start stale task cleanup in the background
    cleanup_task = asyncio.create_task(cleanup_background_task())
    logger.info("Background cleanup task started")
    yield
    # Shutdown: Clean up tasks
    cleanup_task.cancel()
    await registry.cleanup_tasks()
    logger.info("Server shutdown: Cleaned up active tasks")

async def cleanup_background_task():
    try:
        while True:
            await asyncio.sleep(60)
            await registry.cleanup_stale_tasks(max_age_seconds=300)
    except asyncio.CancelledError:
        logger.info("Background cleanup task cancelled")

app = FastAPI(
    title="ADK Progress Bridge",
    description="A bridge between long-running agent tools and a real-time progress TUI/Frontend.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TaskStartRequest(BaseModel):
    args: Dict[str, Any] = {}

class TaskStartResponse(BaseModel):
    call_id: str
    stream_url: str

class InputProvideRequest(BaseModel):
    call_id: str
    value: Any

@app.post("/start_task/{tool_name}", response_model=TaskStartResponse)
async def start_task(
    tool_name: str, 
    request: Optional[TaskStartRequest] = None, 
    authenticated: bool = Depends(verify_api_key)
):
    """
    Starts a tool execution and returns a call_id to stream progress.
    """
    tool = registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")
    
    call_id = str(uuid.uuid4())
    
    args = request.args if request else {}
    
    try:
        # Create the generator but don't start consuming yet
        gen = tool(**args)
        registry.store_task(call_id, gen, tool_name)
    except Exception as e:
        logger.error(f"Error starting tool {tool_name}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    return TaskStartResponse(
        call_id=call_id,
        stream_url=f"/stream/{call_id}"
    )

@app.get("/stream/{call_id}")
@app.get("/stream")
async def stream_task(
    call_id: Optional[str] = None,
    cid: Optional[str] = Query(None, alias="call_id"),
    authenticated: bool = Depends(verify_api_key)
):
    """
    SSE endpoint to stream progress and results for a task.
    Supports both path parameter and query parameter for call_id.
    """
    actual_call_id = call_id or cid
    if not actual_call_id:
        raise HTTPException(status_code=400, detail="call_id is required")

    task_data = registry.get_task(actual_call_id)
    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found or already being streamed")
    
    gen = task_data["gen"]
    tool_name = task_data["tool_name"]

    async def event_generator():
        # Set context vars for the generator's thread/task
        call_id_var.set(actual_call_id)
        tool_name_var.set(tool_name)
        
        start_time = time.perf_counter()
        status = "success"
        
        try:
            async for item in gen:
                if isinstance(item, ProgressPayload):
                    TASK_PROGRESS_STEPS_TOTAL.labels(tool_name=tool_name).inc()
                    event = ProgressEvent(call_id=actual_call_id, type="progress", payload=item)
                elif isinstance(item, dict) and item.get("type") == "input_request":
                    event = ProgressEvent(call_id=actual_call_id, type="input_request", payload=item["payload"])
                else:
                    event = ProgressEvent(call_id=actual_call_id, type="result", payload=item)
                
                yield await format_sse(event)
                
        except asyncio.CancelledError:
            status = "cancelled"
            logger.info(f"Task {actual_call_id} was cancelled by client")
            # Ensure generator is closed
            await gen.aclose()
        except Exception as e:
            status = "error"
            logger.error(f"Error during task {actual_call_id} execution: {e}")
            error_event = ProgressEvent(
                call_id=actual_call_id, 
                type="error", 
                payload={"detail": str(e)}
            )
            yield await format_sse(error_event)
        finally:
            duration = time.perf_counter() - start_time
            TASK_DURATION.labels(tool_name=tool_name).observe(duration)
            TASKS_TOTAL.labels(tool_name=tool_name, status=status).inc()
            
            registry.remove_task(actual_call_id)
            logger.info(f"Stream finished for task: {actual_call_id} (duration: {duration:.2f}s, status: {status})")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

@app.post("/provide_input")
async def provide_input(request: InputProvideRequest, authenticated: bool = Depends(verify_api_key)):
    """
    Allows providing input to a task waiting for it. 
    Useful for SSE-based flows where the client can't send data back over the stream.
    """
    if input_manager.provide_input(request.call_id, request.value):
        return {"status": "input accepted"}
    else:
        raise HTTPException(status_code=404, detail=f"No task waiting for input with call_id: {request.call_id}")

@app.post("/stop_task/{call_id}")
@app.post("/stop_task")
async def stop_task(
    call_id: Optional[str] = None, 
    cid: Optional[str] = Query(None, alias="call_id"),
    authenticated: bool = Depends(verify_api_key)
):
    """
    Manually stops a running task.
    Supports both path parameter and query parameter for call_id.
    """
    actual_call_id = call_id or cid
    if not actual_call_id:
        raise HTTPException(status_code=400, detail="call_id is required")

    task_data = registry.get_task_no_consume(actual_call_id)
    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found or already finished")
    
    await task_data["gen"].aclose()
    
    # If the task was not yet consumed, it won't be removed by the stream generator's finally block
    # because the stream generator was never started. So we remove it here.
    if not task_data["consumed"]:
        registry.remove_task(actual_call_id)
        
    return {"status": "stop signal sent"}

@app.get("/metrics")
async def metrics():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Bi-directional WebSocket endpoint for executing tools and receiving progress.
    """
    await websocket.accept()
    
    try:
        await verify_api_key_ws(websocket)
    except HTTPException:
        return

    logger.info("WebSocket connection established")
    
    active_tasks: Dict[str, asyncio.Task] = {}

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            msg_type = message.get("type")
            
            if msg_type == "start":
                tool_name = message.get("tool_name")
                args = message.get("args", {})
                
                tool = registry.get_tool(tool_name)
                if not tool:
                    await websocket.send_json({
                        "type": "error",
                        "payload": {"detail": f"Tool not found: {tool_name}"}
                    })
                    continue
                
                call_id = str(uuid.uuid4())
                
                try:
                    gen = tool(**args)
                    # Register task globally
                    registry.store_task(call_id, gen, tool_name)
                    # Run the generator in a background task tracked locally
                    task = asyncio.create_task(run_ws_generator(websocket, call_id, tool_name, gen, active_tasks))
                    active_tasks[call_id] = task
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "call_id": call_id,
                        "payload": {"detail": str(e)}
                    })
            
            elif msg_type == "stop":
                call_id = message.get("call_id")
                if call_id in active_tasks:
                    logger.info(f"Stopping task {call_id} via WebSocket request")
                    active_tasks[call_id].cancel()
                    await websocket.send_json({
                        "call_id": call_id,
                        "type": "progress",
                        "payload": {"step": "Cancelled", "pct": 0, "log": "Task stopped by user."}
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "payload": {"detail": f"No active task found with call_id: {call_id}"}
                    })
            
            elif msg_type == "input":
                call_id = message.get("call_id")
                value = message.get("value")
                if input_manager.provide_input(call_id, value):
                    logger.info(f"Input received for task {call_id}")
                else:
                    await websocket.send_json({
                        "type": "error",
                        "payload": {"detail": f"No task waiting for input with call_id: {call_id}"}
                    })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Cleanup all tasks associated with this connection
        if active_tasks:
            logger.info(f"Cleaning up {len(active_tasks)} WebSocket tasks due to disconnect")
            for task in active_tasks.values():
                task.cancel()

async def run_ws_generator(websocket: WebSocket, call_id: str, tool_name: str, gen, active_tasks: Dict[str, asyncio.Task]):
    # Set context vars
    call_id_var.set(call_id)
    tool_name_var.set(tool_name)
    
    start_time = time.perf_counter()
    status = "success"
    
    logger.info(f"Starting WS execution for task: {call_id}")
    try:
        async for item in gen:
            if isinstance(item, ProgressPayload):
                TASK_PROGRESS_STEPS_TOTAL.labels(tool_name=tool_name).inc()
                event = ProgressEvent(call_id=call_id, type="progress", payload=item)
            elif isinstance(item, dict) and item.get("type") == "input_request":
                event = ProgressEvent(call_id=call_id, type="input_request", payload=item["payload"])
            else:
                event = ProgressEvent(call_id=call_id, type="result", payload=item)
            
            await websocket.send_json(event.model_dump())
            
    except asyncio.CancelledError:
        status = "cancelled"
        logger.info(f"WS task {call_id} cancelled")
        await gen.aclose()
    except Exception as e:
        status = "error"
        logger.error(f"Error during WS task {call_id}: {e}")
        event = ProgressEvent(call_id=call_id, type="error", payload={"detail": str(e)})
        try:
            await websocket.send_json(event.model_dump())
        except:
            pass # Socket might be closed
    finally:
        duration = time.perf_counter() - start_time
        TASK_DURATION.labels(tool_name=tool_name).observe(duration)
        TASKS_TOTAL.labels(tool_name=tool_name, status=status).inc()
        
        # Cleanup
        registry.remove_task(call_id)
        active_tasks.pop(call_id, None)
        
        logger.info(f"WS task finished: {call_id} (duration: {duration:.2f}s, status: {status})")

# Import tools to register them
from . import dummy_tool