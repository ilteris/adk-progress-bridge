import sys
import asyncio
import json
import uuid
import time
import os
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
from .metrics import (
    TASK_DURATION, TASKS_TOTAL, TASK_PROGRESS_STEPS_TOTAL, 
    ACTIVE_WS_CONNECTIONS, WS_MESSAGES_RECEIVED_TOTAL, WS_MESSAGES_SENT_TOTAL, BUILD_INFO,
    PEAK_ACTIVE_TASKS, WS_BYTES_RECEIVED_TOTAL, WS_BYTES_SENT_TOTAL,
    WS_REQUEST_LATENCY, WS_CONNECTION_DURATION, TOTAL_TASKS_STARTED,
    PEAK_ACTIVE_WS_CONNECTIONS, WS_MESSAGE_SIZE_BYTES,
    WS_BINARY_FRAMES_REJECTED_TOTAL, WS_CONNECTION_ERRORS_TOTAL
)
from .health import HealthEngine, BroadcastMetricsManager

# Configuration Constants
WS_HEARTBEAT_TIMEOUT = 60.0
CLEANUP_INTERVAL = 60.0
STALE_TASK_MAX_AGE = 300.0
WS_MESSAGE_SIZE_LIMIT = 1024 * 1024  # 1MB
MAX_CONCURRENT_TASKS = 100
APP_VERSION = "1.7.1"
APP_START_TIME = time.time()
GIT_COMMIT = "v379-final-signoff"
OPERATIONAL_APEX = "GOD TIER FIDELITY (v379 ULTIMATE)"

BUILD_INFO.info({"version": APP_VERSION, "git_commit": GIT_COMMIT})
ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "*").split(",")

health_engine = HealthEngine(APP_START_TIME)

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
    task_data = await registry.get_task(actual_call_id)
    if not task_data: raise HTTPException(status_code=404, detail="Task not found")
    gen, tool_name = task_data["gen"], task_data["tool_name"]

    async def event_generator():
        call_id_var.set(actual_call_id); tool_name_var.set(tool_name)
        start_time, status, metrics_queue, combined_queue = time.perf_counter(), "success", metrics_broadcaster.subscribe(actual_call_id), asyncio.Queue()
        async def pull_gen():
            try:
                async for item in gen: await combined_queue.put(("item", item))
                await combined_queue.put(("done", None))
            except Exception as e: await combined_queue.put(("error", e))
        async def pull_metrics():
            try:
                while True: await combined_queue.put(("metrics", await metrics_queue.get()))
            except asyncio.CancelledError: pass
        gen_task, metrics_task = asyncio.create_task(pull_gen()), asyncio.create_task(pull_metrics())
        try:
            while True:
                msg_type, payload = await combined_queue.get()
                if msg_type == "done": break
                elif msg_type == "error": raise payload
                elif msg_type == "metrics": yield await format_sse(ProgressEvent(call_id=actual_call_id, type="system_metrics", payload=payload))
                elif msg_type == "item":
                    if isinstance(payload, ProgressPayload):
                        TASK_PROGRESS_STEPS_TOTAL.labels(tool_name=tool_name).inc()
                        yield await format_sse(ProgressEvent(call_id=actual_call_id, type="progress", payload=payload))
                    elif isinstance(payload, dict) and payload.get("type") == "input_request": yield await format_sse(ProgressEvent(call_id=actual_call_id, type="input_request", payload=payload["payload"]))
                    else: yield await format_sse(ProgressEvent(call_id=actual_call_id, type="result", payload=payload))
            gen_task.cancel(); metrics_task.cancel()
        except asyncio.CancelledError: status = "cancelled"; await gen.aclose()
        except Exception as e: status = "error"; yield await format_sse(ProgressEvent(call_id=actual_call_id, type="error", payload={"detail": str(e)}))
        finally:
            metrics_broadcaster.unsubscribe(actual_call_id)
            if not gen_task.done(): gen_task.cancel()
            if not metrics_task.done(): metrics_task.cancel()
            duration = time.perf_counter() - start_time
            TASK_DURATION.labels(tool_name=tool_name).observe(duration); TASKS_TOTAL.labels(tool_name=tool_name, status=status).inc()
            await registry.remove_task(actual_call_id)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/provide_input", responses=AUTH_RESPONSES)
async def provide_input(request: InputProvideRequest, authenticated: bool = Depends(verify_api_key)):
    if await input_manager.provide_input(request.call_id, request.value): return {"status": "input accepted"}
    raise HTTPException(status_code=404, detail="No task waiting for input")

@app.post("/stop_task/{call_id}", responses=AUTH_RESPONSES)
@app.post("/stop_task", responses=AUTH_RESPONSES)
async def stop_task(call_id: Optional[str] = None, cid: Optional[str] = Query(None, alias="call_id"), authenticated: bool = Depends(verify_api_key)):
    actual_call_id = call_id or cid
    if not actual_call_id: raise HTTPException(status_code=400, detail="call_id is required")
    task_data = await registry.get_task_no_consume(actual_call_id)
    if not task_data: raise HTTPException(status_code=404, detail="Task not found")
    await task_data["gen"].aclose()
    if not task_data["consumed"]: await registry.remove_task(actual_call_id)
    return {"status": "stop signal sent"}

@app.get("/health") 
async def health_check(): return await health_engine.get_health_data(app.state, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX)

@app.get("/version") 
async def get_version(): return {"version": APP_VERSION, "git_commit": GIT_COMMIT, "status": OPERATIONAL_APEX, "timestamp": time.time()} 

@app.get("/metrics")
async def metrics():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    await health_engine.get_health_data(app.state, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX)
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    conn_start_time = time.perf_counter()
    ACTIVE_WS_CONNECTIONS.inc()
    current_ws = int(ACTIVE_WS_CONNECTIONS._value.get())
    if current_ws > getattr(app.state, "peak_ws_connections", 0):
        app.state.peak_ws_connections = current_ws
        PEAK_ACTIVE_WS_CONNECTIONS.set(current_ws)
    active_tasks: Dict[str, asyncio.Task] = {}
    try:
        try: await verify_api_key_ws(websocket)
        except HTTPException: WS_CONNECTION_ERRORS_TOTAL.labels(error_type="auth_failure").inc(); return
        send_lock = asyncio.Lock()
        async def safe_send_json(data: dict):
            async with send_lock:
                try:
                    WS_MESSAGES_SENT_TOTAL.labels(message_type=data.get("type", "unknown")).inc()
                    json_str = json.dumps(data)
                    WS_BYTES_SENT_TOTAL.inc(len(json_str)); WS_MESSAGE_SIZE_BYTES.observe(len(json_str))
                    await websocket.send_text(json_str)
                except Exception as e: logger.error(f"Error sending WS message: {e}"); raise
        while True:
            try:
                msg = await asyncio.wait_for(websocket.receive(), timeout=WS_HEARTBEAT_TIMEOUT)
                if msg["type"] == "websocket.disconnect": break
                if msg["type"] != "websocket.receive": continue
                if "bytes" in msg:
                    WS_BYTES_RECEIVED_TOTAL.inc(len(msg["bytes"])); WS_MESSAGES_RECEIVED_TOTAL.labels(message_type="binary").inc(); WS_BINARY_FRAMES_REJECTED_TOTAL.inc()
                    await safe_send_json({"type": "error", "payload": {"detail": "Binary messages are not supported."}})
                    continue
                data = msg.get("text", "")
                WS_BYTES_RECEIVED_TOTAL.inc(len(data)); WS_MESSAGE_SIZE_BYTES.observe(len(data))
                if len(data) > WS_MESSAGE_SIZE_LIMIT:
                    WS_MESSAGES_RECEIVED_TOTAL.labels(message_type="oversized").inc()
                    await safe_send_json({"type": "error", "payload": {"detail": f"Message too large (max {WS_MESSAGE_SIZE_LIMIT})"}})
                    continue
                req_start_time, message = time.perf_counter(), json.loads(data)
                if not isinstance(message, dict):
                    WS_MESSAGES_RECEIVED_TOTAL.labels(message_type="invalid_format").inc()
                    await safe_send_json({"type": "error", "payload": {"detail": "Message must be a JSON object"}})
                    continue
                msg_type, request_id = message.get("type", "unknown"), message.get("request_id")
                WS_MESSAGES_RECEIVED_TOTAL.labels(message_type=msg_type).inc()
            except asyncio.TimeoutError: break
            except json.JSONDecodeError:
                WS_MESSAGES_RECEIVED_TOTAL.labels(message_type="invalid_json").inc(); WS_CONNECTION_ERRORS_TOTAL.labels(error_type="protocol_error").inc()
                await safe_send_json({"type": "error", "payload": {"detail": "Invalid JSON received"}})
                continue
            except Exception: WS_CONNECTION_ERRORS_TOTAL.labels(error_type="protocol_error").inc(); break
            
            try:
                if msg_type == "ping": await safe_send_json({"type": "pong"})
                elif msg_type == "list_tools": await safe_send_json({"type": "tools_list", "tools": registry.list_tools(), "request_id": request_id})
                elif msg_type == "list_active_tasks": await safe_send_json({"type": "active_tasks_list", "tasks": await registry.list_active_tasks(), "request_id": request_id})
                elif msg_type == "get_health": await safe_send_json({"type": "health_data", "data": await health_engine.get_health_data(app.state, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX), "request_id": request_id})
                elif msg_type == "start":
                    if registry.active_task_count >= MAX_CONCURRENT_TASKS: await safe_send_json({"type": "error", "request_id": request_id, "payload": {"detail": "Server busy"}})
                    else:
                        tool_name = message.get("tool_name")
                        tool = registry.get_tool(tool_name)
                        if not tool: await safe_send_json({"type": "error", "request_id": request_id, "payload": {"detail": f"Tool not found: {tool_name}"}})
                        else:
                            call_id = str(uuid.uuid4())
                            try:
                                gen = tool(**message.get("args", {}))
                                await registry.store_task(call_id, gen, tool_name); await registry.mark_consumed(call_id)
                                await safe_send_json({"type": "task_started", "call_id": call_id, "tool_name": tool_name, "request_id": request_id})
                                active_tasks[call_id] = asyncio.create_task(run_ws_generator(safe_send_json, call_id, tool_name, gen, active_tasks))
                            except Exception as e: await safe_send_json({"type": "error", "call_id": call_id, "request_id": request_id, "payload": {"detail": str(e)}})
                elif msg_type == "stop":
                    call_id = message.get("call_id")
                    if call_id in active_tasks:
                        active_tasks[call_id].cancel()
                        await safe_send_json({"call_id": call_id, "type": "progress", "payload": {"step": "Cancelled", "pct": 0, "log": "Task stopped by user."}})
                        await safe_send_json({"type": "stop_success", "call_id": call_id, "request_id": request_id})
                    else:
                        task_data = await registry.get_task_no_consume(call_id)
                        if task_data:
                            await task_data["gen"].aclose()
                            if not task_data["consumed"]: await registry.remove_task(call_id)
                            await safe_send_json({"type": "stop_success", "call_id": call_id, "request_id": request_id})
                        else: await safe_send_json({"type": "error", "call_id": call_id, "request_id": request_id, "payload": {"detail": "No active task found"}})
                elif msg_type == "subscribe":
                    call_id = message.get("call_id")
                    task_data = await registry.get_task(call_id)
                    if task_data:
                        active_tasks[call_id] = asyncio.create_task(run_ws_generator(safe_send_json, call_id, task_data["tool_name"], task_data["gen"], active_tasks))
                        await safe_send_json({"type": "task_started", "call_id": call_id, "tool_name": task_data["tool_name"], "request_id": request_id})
                    else: await safe_send_json({"type": "error", "call_id": call_id, "request_id": request_id, "payload": {"detail": "No active task found"}})
                elif msg_type == "input":
                    call_id = message.get("call_id")
                    if await input_manager.provide_input(call_id, message.get("value")): await safe_send_json({"type": "input_success", "call_id": call_id, "request_id": request_id})
                    else: await safe_send_json({"type": "error", "call_id": call_id, "request_id": request_id, "payload": {"detail": "No task waiting for input"}})
                else: await safe_send_json({"type": "error", "request_id": request_id, "payload": {"detail": "Unknown message type"}})
                WS_REQUEST_LATENCY.labels(message_type=msg_type).observe(time.perf_counter() - req_start_time)
            except Exception as e:
                WS_CONNECTION_ERRORS_TOTAL.labels(error_type="other_error").inc()
                await safe_send_json({"type": "error", "request_id": request_id, "payload": {"detail": "Internal error"}})
    finally:
        ACTIVE_WS_CONNECTIONS.dec(); WS_CONNECTION_DURATION.observe(time.perf_counter() - conn_start_time)
        for t in active_tasks.values():
            if not t.done(): t.cancel()

async def run_ws_generator(send_func, call_id, tool_name, gen, active_tasks):
    call_id_var.set(call_id); tool_name_var.set(tool_name)
    start_time, status, metrics_queue = time.perf_counter(), "success", metrics_broadcaster.subscribe(call_id)
    async def metrics_pusher():
        try:
            while True: await send_func({"call_id": call_id, "type": "system_metrics", "payload": await metrics_queue.get()})
        except asyncio.CancelledError: pass
    metrics_task = asyncio.create_task(metrics_pusher())
    try:
        async for item in gen:
            if isinstance(item, ProgressPayload):
                TASK_PROGRESS_STEPS_TOTAL.labels(tool_name=tool_name).inc()
                await send_func({"call_id": call_id, "type": "progress", "payload": item.model_dump()})
            elif isinstance(item, dict) and item.get("type") == "input_request": await send_func({"call_id": call_id, "type": "input_request", "payload": item["payload"]})
            else: await send_func({"call_id": call_id, "type": "result", "payload": item})
    except asyncio.CancelledError: status = "cancelled"; await gen.aclose()
    except Exception as e: status = "error"; await send_func({"call_id": call_id, "type": "error", "payload": {"detail": str(e)}})
    finally:
        metrics_broadcaster.unsubscribe(call_id); metrics_task.cancel()
        TASK_DURATION.labels(tool_name=tool_name).observe(time.perf_counter() - start_time); TASKS_TOTAL.labels(tool_name=tool_name, status=status).inc()
        await registry.remove_task(call_id); active_tasks.pop(call_id, None)

from . import dummy_tool
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
