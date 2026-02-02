import sys
import asyncio
import json
import uuid
import time
import os
import inspect
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Query, Request, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .bridge import registry, ProgressEvent, ProgressPayload, format_sse, input_manager, TaskBroadcaster
from .logger import logger
from .context import call_id_var, tool_name_var
from .auth import verify_api_key, verify_api_key_ws
from .metrics import (
    TASK_DURATION, TASKS_TOTAL, TASK_PROGRESS_STEPS_TOTAL, 
    ACTIVE_WS_CONNECTIONS, WS_MESSAGES_RECEIVED_TOTAL, WS_MESSAGES_SENT_TOTAL, BUILD_INFO,
    PEAK_ACTIVE_TASKS, WS_BYTES_RECEIVED_TOTAL, WS_BYTES_SENT_TOTAL,
    WS_REQUEST_LATENCY, WS_CONNECTION_DURATION, TOTAL_TASKS_STARTED,
    PEAK_ACTIVE_WS_CONNECTIONS, WS_MESSAGE_SIZE_BYTES,
    WS_BINARY_FRAMES_REJECTED_TOTAL, WS_CONNECTION_ERRORS_TOTAL
)
from .health import health_engine, BroadcastMetricsManager, APP_START_TIME

# Configuration Constants
WS_HEARTBEAT_TIMEOUT = 60.0
CLEANUP_INTERVAL = 60.0
STALE_TASK_MAX_AGE = 300.0
WS_MESSAGE_SIZE_LIMIT = 1024 * 1024  # 1MB
MAX_CONCURRENT_TASKS = 100
MAX_QUEUE_SIZE = 1000
APP_VERSION = "2.12.72" # Bumped for v845 websocket integration + metrics
BUILD_TIMESTAMP = "2026-02-02T23:59:00Z"
GIT_COMMIT = "v845-supreme-apex-2920"
OPERATIONAL_APEX = "v845 SUPREME APEX 3012 VERIFICATION"

BUILD_INFO.info({"version": APP_VERSION, "git_commit": GIT_COMMIT, "build_timestamp": BUILD_TIMESTAMP})
ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "*").split(",")

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.peak_ws_connections = 0
    app.state.last_throughput_time, app.state.last_bytes_received, app.state.last_bytes_sent = time.time(), 0, 0
    app.state.last_io_time, app.state.last_proc_read_bytes, app.state.last_proc_write_bytes = time.time(), 0, 0
    app.state.last_sys_io_time, app.state.last_sys_read_bytes, app.state.last_sys_write_bytes = time.time(), 0, 0
    app.state.last_sys_net_recv_bytes, app.state.last_sys_net_sent_bytes = 0, 0
    app.state.last_sys_cpu_stats_time, app.state.last_sys_ctx_switches, app.state.last_sys_interrupts, app.state.last_sys_soft_interrupts, app.state.last_sys_syscalls = time.time(), 0, 0, 0, 0
    app.state.last_sys_pf_time, app.state.last_sys_pf_minor, app.state.last_sys_pf_major = time.time(), 0, 0
    cleanup_task = asyncio.create_task(cleanup_background_task())
    await metrics_broadcaster.start()
    yield
    await metrics_broadcaster.stop(); cleanup_task.cancel(); await registry.cleanup_tasks()

async def cleanup_background_task():
    try:
        while True:
            await asyncio.sleep(CLEANUP_INTERVAL); await registry.cleanup_stale_tasks(max_age_seconds=STALE_TASK_MAX_AGE)
    except asyncio.CancelledError: pass

metrics_broadcaster = BroadcastMetricsManager(health_engine, None, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX)
app = FastAPI(title="ADK Progress Bridge", description="Bridge between tools and TUI.", version=APP_VERSION, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
metrics_broadcaster.app = app

class TaskStartRequest(BaseModel): args: Dict[str, Any] = {}
class TaskStartResponse(BaseModel): call_id: str; stream_url: str
class InputProvideRequest(BaseModel): call_id: str; value: Any
AUTH_RESPONSES = {401: {"description": "Unauthorized"}}

@app.get("/tools", response_model=List[str], responses=AUTH_RESPONSES)
async def list_tools(authenticated: bool = Depends(verify_api_key)): return registry.list_tools()

@app.get("/tasks", responses=AUTH_RESPONSES)
async def list_active_tasks(authenticated: bool = Depends(verify_api_key)): return await registry.list_active_tasks()

@app.get("/health", responses=AUTH_RESPONSES)
async def get_health(authenticated: bool = Depends(verify_api_key)):
    return await health_engine.get_health_data(app.state, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX)

@app.post("/start_task/{tool_name}", response_model=TaskStartResponse, responses=AUTH_RESPONSES)
async def start_task(tool_name: str, request: Optional[TaskStartRequest] = None, authenticated: bool = Depends(verify_api_key)):
    if registry.active_task_count >= MAX_CONCURRENT_TASKS: raise HTTPException(status_code=503, detail="Server busy")
    tool = registry.get_tool(tool_name)
    if not tool: raise HTTPException(status_code=404, detail="Tool not found")
    call_id = str(uuid.uuid4())
    try:
        gen = tool(**(request.args if request else {}))
        await registry.store_task(call_id, gen, tool_name)
    except Exception as e: raise HTTPException(status_code=400, detail=str(e))
    return TaskStartResponse(call_id=call_id, stream_url=f"/stream/{call_id}")

@app.get("/stream/{call_id}", responses=AUTH_RESPONSES)
@app.get("/stream", responses=AUTH_RESPONSES)
async def stream_task(call_id: Optional[str] = None, cid: Optional[str] = Query(None, alias="call_id"), authenticated: bool = Depends(verify_api_key)):
    actual_call_id = call_id or cid
    if not actual_call_id: raise HTTPException(status_code=400, detail="call_id is required")
    broadcaster = await registry.get_broadcaster(actual_call_id)
    if not broadcaster: raise HTTPException(status_code=404, detail="Task not found")
    return StreamingResponse(broadcaster.subscribe(), media_type="text/event-stream")

@app.post("/input", responses=AUTH_RESPONSES)
async def provide_input(request: InputProvideRequest, authenticated: bool = Depends(verify_api_key)):
    if await input_manager.provide_input(request.call_id, request.value): return {"status": "success"}
    raise HTTPException(status_code=404, detail="No active input request found for this call_id")

@app.post("/stop_task/{call_id}", responses=AUTH_RESPONSES)
async def stop_task(call_id: str, authenticated: bool = Depends(verify_api_key)):
    if await registry.stop_task(call_id): return {"status": "success"}
    raise HTTPException(status_code=404, detail="Task not found")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    start_time = time.time()
    ACTIVE_WS_CONNECTIONS.inc()
    PEAK_ACTIVE_WS_CONNECTIONS.set(ACTIVE_WS_CONNECTIONS._value.get())
    
    # Authenticate via initial message or query param
    auth_verified = False
    api_key = websocket.query_params.get("api_key")
    if api_key and verify_api_key_ws(api_key):
        auth_verified = True
        await websocket.send_json({"type": "connected"})
    
    subscribed_tasks: Dict[str, asyncio.Task] = {}
    conn_id = str(uuid.uuid4())

    async def stream_broadcaster(call_id: str, broadcaster: TaskBroadcaster, request_id: Optional[str]):
        try:
            async for event in broadcaster.subscribe():
                await websocket.send_text(event.model_dump_json() if hasattr(event, "model_dump_json") else event)
                WS_MESSAGES_SENT_TOTAL.inc()
                WS_BYTES_SENT_TOTAL.inc(len(str(event)))
        except Exception as e:
            logger.error(f"Error streaming task {call_id} to websocket: {e}")

    async def stream_metrics():
        q = metrics_broadcaster.subscribe(conn_id)
        try:
            while True:
                metrics = await q.get()
                await websocket.send_json({"type": "system_metrics", "payload": metrics})
                WS_MESSAGES_SENT_TOTAL.inc()
        except Exception as e:
            logger.error(f"Error streaming metrics to websocket: {e}")
        finally:
            metrics_broadcaster.unsubscribe(conn_id)

    metrics_task = asyncio.create_task(stream_metrics())

    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=WS_HEARTBEAT_TIMEOUT)
                WS_MESSAGES_RECEIVED_TOTAL.inc()
                WS_BYTES_RECEIVED_TOTAL.inc(len(data))
                if len(data) > WS_MESSAGE_SIZE_LIMIT:
                    await websocket.send_json({"type": "error", "message": "Message too large"})
                    continue
                
                msg = json.loads(data)
                
                if not auth_verified:
                    if msg.get("type") == "auth" and verify_api_key_ws(msg.get("api_key")):
                        auth_verified = True
                        await websocket.send_json({"type": "auth_success"})
                        await websocket.send_json({"type": "connected"})
                        continue
                    else:
                        await websocket.send_json({"type": "error", "message": "Unauthorized"})
                        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                        break

                msg_type = msg.get("type")
                request_id = msg.get("request_id")

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong", "request_id": request_id})
                
                elif msg_type == "list_tools":
                    await websocket.send_json({
                        "type": "tools_list", 
                        "tools": registry.list_tools(),
                        "request_id": request_id
                    })

                elif msg_type == "list_active_tasks":
                    await websocket.send_json({
                        "type": "active_tasks_list",
                        "tasks": await registry.list_active_tasks(),
                        "request_id": request_id
                    })

                elif msg_type == "get_health":
                    health_data = await health_engine.get_health_data(app.state, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX)
                    await websocket.send_json({
                        "type": "health_data",
                        "data": health_data,
                        "request_id": request_id
                    })

                elif msg_type in ("start", "start_task"):
                    tool_name = msg.get("tool_name")
                    args = msg.get("args", {})
                    if registry.active_task_count >= MAX_CONCURRENT_TASKS:
                        await websocket.send_json({"type": "error", "message": "Server busy", "request_id": request_id})
                        continue
                    
                    tool = registry.get_tool(tool_name)
                    if not tool:
                        await websocket.send_json({"type": "error", "message": "Tool not found", "request_id": request_id})
                        continue
                    
                    call_id = str(uuid.uuid4())
                    # Send confirmation immediately
                    await websocket.send_json({
                        "type": "task_started", 
                        "call_id": call_id, 
                        "request_id": request_id
                    })
                    
                    try:
                        # Use context vars for metrics/logging
                        call_id_var.set(call_id)
                        tool_name_var.set(tool_name)
                        
                        gen = tool(**args)
                        broadcaster = await registry.store_task(call_id, gen, tool_name)
                        
                        task = asyncio.create_task(stream_broadcaster(call_id, broadcaster, request_id))
                        subscribed_tasks[call_id] = task
                                
                    except Exception as e:
                        logger.error(f"Task error: {e}")
                        await websocket.send_json({
                            "type": "error", 
                            "call_id": call_id, 
                            "message": str(e),
                            "request_id": request_id
                        })

                elif msg_type == "subscribe":
                    call_id = msg.get("call_id")
                    broadcaster = await registry.get_broadcaster(call_id)
                    if broadcaster:
                        await websocket.send_json({
                            "type": "subscribed",
                            "call_id": call_id,
                            "request_id": request_id
                        })
                        task = asyncio.create_task(stream_broadcaster(call_id, broadcaster, request_id))
                        subscribed_tasks[call_id] = task
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Task not found",
                            "request_id": request_id
                        })

                elif msg_type in ("stop", "stop_task"):
                    call_id = msg.get("call_id")
                    if await registry.stop_task(call_id):
                        await websocket.send_json({
                            "type": "stop_success" if msg_type == "stop" else "task_stopped", 
                            "call_id": call_id,
                            "request_id": request_id
                        })
                        if call_id in subscribed_tasks:
                            subscribed_tasks[call_id].cancel()
                            del subscribed_tasks[call_id]
                    else:
                        await websocket.send_json({
                            "type": "error", 
                            "message": "Task not found", 
                            "request_id": request_id
                        })

                elif msg_type in ("input", "provide_input"):
                    call_id = msg.get("call_id")
                    value = msg.get("value")
                    if await input_manager.provide_input(call_id, value):
                        await websocket.send_json({
                            "type": "input_success" if msg_type == "input" else "input_accepted", 
                            "call_id": call_id,
                            "request_id": request_id
                        })
                    else:
                        await websocket.send_json({
                            "type": "error", 
                            "message": "No active input request", 
                            "request_id": request_id
                        })
                
                else:
                    await websocket.send_json({
                        "type": "error", 
                        "message": f"Unknown message type: {msg_type}",
                        "request_id": request_id
                    })

            except asyncio.TimeoutError:
                # Heartbeat timeout
                await websocket.close(code=status.WS_1001_GOING_AWAY)
                break
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WS Error: {e}")
                WS_CONNECTION_ERRORS_TOTAL.inc()
                break
    finally:
        ACTIVE_WS_CONNECTIONS.dec()
        duration = time.time() - start_time
        WS_CONNECTION_DURATION.observe(duration)
        metrics_task.cancel()
        for task in subscribed_tasks.values():
            task.cancel()
