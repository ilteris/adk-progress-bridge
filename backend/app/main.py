import sys
import asyncio
import json
import uuid
import time
import os
import subprocess
import threading
import platform
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Query, Request, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    import psutil
except ImportError:
    psutil = None

from .bridge import registry, ProgressEvent, ProgressPayload, format_sse, input_manager
from .logger import logger
from .context import call_id_var, tool_name_var
from .auth import verify_api_key, verify_api_key_ws
from .metrics import (
    TASK_DURATION, TASKS_TOTAL, TASK_PROGRESS_STEPS_TOTAL, 
    ACTIVE_WS_CONNECTIONS, WS_MESSAGES_RECEIVED_TOTAL, WS_MESSAGES_SENT_TOTAL, BUILD_INFO,
    PEAK_ACTIVE_TASKS, WS_BYTES_RECEIVED_TOTAL, WS_BYTES_SENT_TOTAL,
    WS_REQUEST_LATENCY, WS_CONNECTION_DURATION, MEMORY_PERCENT, TOTAL_TASKS_STARTED,
    CPU_USAGE_PERCENT, PEAK_ACTIVE_WS_CONNECTIONS, OPEN_FDS, THREAD_COUNT,
    WS_THROUGHPUT_RECEIVED_BPS, WS_THROUGHPUT_SENT_BPS,
    CONTEXT_SWITCHES_VOLUNTARY, CONTEXT_SWITCHES_INVOLUNTARY,
    DISK_USAGE_PERCENT, SYSTEM_MEMORY_AVAILABLE, PAGE_FAULTS_MINOR, PAGE_FAULTS_MAJOR,
    SYSTEM_CPU_COUNT, SYSTEM_BOOT_TIME, SWAP_MEMORY_USAGE_PERCENT,
    SYSTEM_NETWORK_BYTES_SENT, SYSTEM_NETWORK_BYTES_RECV
)

# Configuration Constants for WebSocket and Task Lifecycle Management
WS_HEARTBEAT_TIMEOUT = 60.0
CLEANUP_INTERVAL = 60.0
STALE_TASK_MAX_AGE = 300.0
WS_MESSAGE_SIZE_LIMIT = 1024 * 1024  # 1MB
MAX_CONCURRENT_TASKS = 100
APP_VERSION = "1.2.5"
APP_START_TIME = time.time()
GIT_COMMIT = "v335-supreme"

BUILD_INFO.info({"version": APP_VERSION, "git_commit": GIT_COMMIT})
ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "*").split(",")

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.peak_ws_connections = 0
    app.state.last_throughput_time = time.time()
    app.state.last_bytes_received = 0
    app.state.last_bytes_sent = 0
    
    cleanup_task = asyncio.create_task(cleanup_background_task())
    logger.info("Background cleanup task started")
    yield
    cleanup_task.cancel()
    await registry.cleanup_tasks()
    logger.info("Server shutdown: Cleaned up active tasks")

async def cleanup_background_task():
    try:
        while True:
            await asyncio.sleep(CLEANUP_INTERVAL)
            await registry.cleanup_stale_tasks(max_age_seconds=STALE_TASK_MAX_AGE)
    except asyncio.CancelledError:
        logger.info("Background cleanup task cancelled")

def get_memory_usage_kb():
    if psutil:
        try:
            return psutil.Process().memory_info().rss // 1024
        except:
            pass
    
    try:
        if sys.platform == "darwin":
            # Mac
            output = subprocess.check_output(["ps", "-o", "rss=", "-p", str(os.getpid())])
            return int(output.strip())
        elif sys.platform.startswith("linux"):
            # Linux
            with open("/proc/self/status", "r") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        return int(line.split()[1])
    except:
        pass
    return 0

def get_memory_percent():
    if psutil:
        try:
            return psutil.Process().memory_percent()
        except:
            pass
    return 0.0

def get_cpu_percent():
    if psutil:
        try:
            return psutil.cpu_percent(interval=None)
        except:
            pass
    return 0.0

def get_open_fds():
    if psutil:
        try:
            proc = psutil.Process()
            if hasattr(proc, "num_fds"):
                return proc.num_fds()
            elif hasattr(proc, "num_handles"):
                return proc.num_handles()
        except:
            pass
    return 0

def get_context_switches():
    if psutil:
        try:
            switches = psutil.Process().num_ctx_switches()
            return switches.voluntary, switches.involuntary
        except:
            pass
    return 0, 0

def get_disk_usage_percent():
    if psutil:
        try:
            return psutil.disk_usage('/').percent
        except:
            pass
    return 0.0

def get_system_memory_available():
    if psutil:
        try:
            return psutil.virtual_memory().available
        except:
            pass
    return 0

def get_page_faults():
    if psutil:
        try:
            mem = psutil.Process().memory_info()
            minor = getattr(mem, "pfaults", 0)
            major = getattr(mem, "pageins", 0)
            return minor, major
        except:
            pass
    return 0, 0

def get_swap_memory_percent():
    if psutil:
        try:
            return psutil.swap_memory().percent
        except:
            pass
    return 0.0

def get_network_io():
    if psutil:
        try:
            io = psutil.net_io_counters()
            return io.bytes_sent, io.bytes_recv
        except:
            pass
    return 0, 0

def get_uptime_human(seconds: float) -> str:
    days, rem = divmod(int(seconds), 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    parts = []
    if days > 0: parts.append(f"{days}d")
    if hours > 0: parts.append(f"{hours}h")
    if minutes > 0: parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)

app = FastAPI(
    title="ADK Progress Bridge",
    description="A bridge between long-running agent tools and a real-time progress TUI/Frontend.",
    version=APP_VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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

AUTH_RESPONSES = {401: {"description": "Unauthorized"}}

@app.get("/tools", response_model=List[str], responses=AUTH_RESPONSES)
async def list_tools(authenticated: bool = Depends(verify_api_key)):
    return registry.list_tools()

@app.get("/tasks", responses=AUTH_RESPONSES)
async def list_active_tasks(authenticated: bool = Depends(verify_api_key)):
    return await registry.list_active_tasks()

@app.post("/start_task/{tool_name}", response_model=TaskStartResponse, responses=AUTH_RESPONSES)
async def start_task(
    tool_name: str, 
    request: Optional[TaskStartRequest] = None, 
    authenticated: bool = Depends(verify_api_key)
):
    if registry.active_task_count >= MAX_CONCURRENT_TASKS:
        raise HTTPException(
            status_code=503, 
            detail=f"Server busy: Maximum concurrent tasks ({MAX_CONCURRENT_TASKS}) reached."
        )

    tool = registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")
    
    call_id = str(uuid.uuid4())
    args = request.args if request else {}
    
    try:
        gen = tool(**args)
        await registry.store_task(call_id, gen, tool_name)
    except Exception as e:
        logger.error(f"Error starting tool {tool_name}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    return TaskStartResponse(
        call_id=call_id,
        stream_url=f"/stream/{call_id}"
    )

@app.get("/stream/{call_id}", responses=AUTH_RESPONSES)
@app.get("/stream", responses=AUTH_RESPONSES)
async def stream_task(
    call_id: Optional[str] = None,
    cid: Optional[str] = Query(None, alias="call_id"),
    authenticated: bool = Depends(verify_api_key)
):
    actual_call_id = call_id or cid
    if not actual_call_id:
        raise HTTPException(status_code=400, detail="call_id is required")

    task_data = await registry.get_task(actual_call_id)
    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found or already being streamed")
    
    gen = task_data["gen"]
    tool_name = task_data["tool_name"]

    async def event_generator():
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
            await gen.aclose()
        except Exception as e:
            status = "error"
            logger.error(f"Error during task {actual_call_id} execution: {e}")
            error_event = ProgressEvent(call_id=actual_call_id, type="error", payload={"detail": str(e)})
            yield await format_sse(error_event)
        finally:
            duration = time.perf_counter() - start_time
            TASK_DURATION.labels(tool_name=tool_name).observe(duration)
            TASKS_TOTAL.labels(tool_name=tool_name, status=status).inc()
            await registry.remove_task(actual_call_id)
            logger.info(f"Stream finished for task: {actual_call_id} (duration: {duration:.2f}s, status: {status})")

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/provide_input", responses=AUTH_RESPONSES)
async def provide_input(request: InputProvideRequest, authenticated: bool = Depends(verify_api_key)):
    if await input_manager.provide_input(request.call_id, request.value):
        return {"status": "input accepted"}
    else:
        raise HTTPException(status_code=404, detail=f"No task waiting for input with call_id: {request.call_id}")

@app.post("/stop_task/{call_id}", responses=AUTH_RESPONSES)
@app.post("/stop_task", responses=AUTH_RESPONSES)
async def stop_task(
    call_id: Optional[str] = None, 
    cid: Optional[str] = Query(None, alias="call_id"),
    authenticated: bool = Depends(verify_api_key)
):
    actual_call_id = call_id or cid
    if not actual_call_id:
        raise HTTPException(status_code=400, detail="call_id is required")
    task_data = await registry.get_task_no_consume(actual_call_id)
    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found or already finished")
    await task_data["gen"].aclose()
    if not task_data["consumed"]:
        await registry.remove_task(actual_call_id)
    return {"status": "stop signal sent"}

@app.get("/health") 
async def health_check(): 
    load_avg = os.getloadavg() if hasattr(os, "getloadavg") else (0, 0, 0)
    
    # Calculate totals from metrics
    ws_received_count = 0
    for m in WS_MESSAGES_RECEIVED_TOTAL.collect():
        for s in m.samples:
            if s.name.endswith("_total"):
                ws_received_count += s.value
                
    ws_sent_count = 0
    for m in WS_MESSAGES_SENT_TOTAL.collect():
        for s in m.samples:
            if s.name.endswith("_total"):
                ws_sent_count += s.value

    ws_bytes_received = int(WS_BYTES_RECEIVED_TOTAL._value.get())
    ws_bytes_sent = int(WS_BYTES_SENT_TOTAL._value.get())

    # Calculate throughput
    now = time.time()
    last_time = getattr(app.state, "last_throughput_time", APP_START_TIME)
    last_received = getattr(app.state, "last_bytes_received", 0)
    last_sent = getattr(app.state, "last_bytes_sent", 0)
    
    dt = now - last_time
    if dt >= 1.0:
        throughput_received = (ws_bytes_received - last_received) / dt
        throughput_sent = (ws_bytes_sent - last_sent) / dt
        WS_THROUGHPUT_RECEIVED_BPS.set(throughput_received)
        WS_THROUGHPUT_SENT_BPS.set(throughput_sent)
        app.state.last_throughput_time = now
        app.state.last_bytes_received = ws_bytes_received
        app.state.last_bytes_sent = ws_bytes_sent
    else:
        throughput_received = int(WS_THROUGHPUT_RECEIVED_BPS._value.get())
        throughput_sent = int(WS_THROUGHPUT_SENT_BPS._value.get())

    uptime_seconds = time.time() - APP_START_TIME
    mem_percent = get_memory_percent()
    MEMORY_PERCENT.set(mem_percent)
    cpu_percent = get_cpu_percent()
    CPU_USAGE_PERCENT.set(cpu_percent)
    open_fds = get_open_fds()
    OPEN_FDS.set(open_fds)
    thread_count = threading.active_count()
    THREAD_COUNT.set(thread_count)
    
    voluntary_ctx, involuntary_ctx = get_context_switches()
    CONTEXT_SWITCHES_VOLUNTARY.set(voluntary_ctx)
    CONTEXT_SWITCHES_INVOLUNTARY.set(involuntary_ctx)

    disk_usage = get_disk_usage_percent()
    DISK_USAGE_PERCENT.set(disk_usage)
    sys_mem_avail = get_system_memory_available()
    SYSTEM_MEMORY_AVAILABLE.set(sys_mem_avail)
    minor_pf, major_pf = get_page_faults()
    PAGE_FAULTS_MINOR.set(minor_pf)
    PAGE_FAULTS_MAJOR.set(major_pf)

    # v335 metrics
    cpu_count = psutil.cpu_count() if psutil else os.cpu_count()
    SYSTEM_CPU_COUNT.set(cpu_count)
    boot_time = psutil.boot_time() if psutil else 0
    SYSTEM_BOOT_TIME.set(boot_time)
    swap_percent = get_swap_memory_percent()
    SWAP_MEMORY_USAGE_PERCENT.set(swap_percent)
    net_sent, net_recv = get_network_io()
    SYSTEM_NETWORK_BYTES_SENT.set(net_sent)
    SYSTEM_NETWORK_BYTES_RECV.set(net_recv)
    
    active_tasks_list = await registry.list_active_tasks()
    tools_summary = {}
    for t in active_tasks_list:
        tools_summary[t["tool_name"]] = tools_summary.get(t["tool_name"], 0) + 1

    # Task success rate
    total_finished = 0
    total_success = 0
    for m in TASKS_TOTAL.collect():
        for s in m.samples:
            total_finished += s.value
            if s.labels.get("status") == "success":
                total_success += s.value
    
    success_rate = (total_success / total_finished * 100) if total_finished > 0 else 100.0

    return { 
        "status": "healthy", 
        "version": APP_VERSION, 
        "git_commit": GIT_COMMIT,
        "operational_apex": "SUPREME ABSOLUTE APEX", 
        "python_version": sys.version, 
        "python_implementation": platform.python_implementation(),
        "system_platform": sys.platform, 
        "cpu_count": cpu_count,
        "cpu_usage_percent": cpu_percent,
        "thread_count": thread_count,
        "open_fds": open_fds,
        "context_switches": {
            "voluntary": voluntary_ctx,
            "involuntary": involuntary_ctx
        },
        "page_faults": {
            "minor": minor_pf,
            "major": major_pf
        },
        "swap_memory_usage_percent": swap_percent,
        "boot_time_seconds": boot_time,
        "network_io_total": {
            "bytes_sent": net_sent,
            "bytes_recv": net_recv
        },
        "active_ws_connections": int(ACTIVE_WS_CONNECTIONS._value.get()),
        "peak_ws_connections": getattr(app.state, "peak_ws_connections", 0),
        "ws_messages_received": int(ws_received_count),
        "ws_messages_sent": int(ws_sent_count),
        "ws_bytes_received": ws_bytes_received,
        "ws_bytes_sent": ws_bytes_sent,
        "ws_throughput_bps": {
            "received": throughput_received,
            "sent": throughput_sent
        },
        "load_avg": load_avg,
        "disk_usage_percent": disk_usage,
        "memory_rss_kb": get_memory_usage_kb(),
        "memory_percent": mem_percent,
        "system_memory_available_bytes": sys_mem_avail,
        "registry_size": registry.active_task_count, 
        "peak_registry_size": registry.peak_active_tasks,
        "total_tasks_started": registry.total_tasks_started,
        "task_success_rate_percent": success_rate,
        "registry_summary": tools_summary,
        "uptime_seconds": uptime_seconds,
        "uptime_human": get_uptime_human(uptime_seconds),
        "start_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(APP_START_TIME)), 
        "timestamp": now,
        "config": {
            "ws_heartbeat_timeout": WS_HEARTBEAT_TIMEOUT,
            "cleanup_interval": CLEANUP_INTERVAL,
            "stale_task_max_age": STALE_TASK_MAX_AGE,
            "ws_message_size_limit": WS_MESSAGE_SIZE_LIMIT,
            "max_concurrent_tasks": MAX_CONCURRENT_TASKS,
            "allowed_origins": ALLOWED_ORIGINS
        }
    }

@app.get("/version") 
async def get_version(): 
    return {
        "version": APP_VERSION, 
        "git_commit": GIT_COMMIT,
        "status": "SUPREME ABSOLUTE APEX", 
        "timestamp": time.time()
    } 

@app.get("/metrics")
async def metrics():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    
    # Update gauges before returning
    MEMORY_PERCENT.set(get_memory_percent())
    CPU_USAGE_PERCENT.set(get_cpu_percent())
    OPEN_FDS.set(get_open_fds())
    THREAD_COUNT.set(threading.active_count())
    v, i = get_context_switches()
    CONTEXT_SWITCHES_VOLUNTARY.set(v)
    CONTEXT_SWITCHES_INVOLUNTARY.set(i)
    DISK_USAGE_PERCENT.set(get_disk_usage_percent())
    SYSTEM_MEMORY_AVAILABLE.set(get_system_memory_available())
    min_pf, maj_pf = get_page_faults()
    PAGE_FAULTS_MINOR.set(min_pf)
    PAGE_FAULTS_MAJOR.set(maj_pf)
    
    SYSTEM_CPU_COUNT.set(psutil.cpu_count() if psutil else os.cpu_count())
    SYSTEM_BOOT_TIME.set(psutil.boot_time() if psutil else 0)
    SWAP_MEMORY_USAGE_PERCENT.set(get_swap_memory_percent())
    net_sent, net_recv = get_network_io()
    SYSTEM_NETWORK_BYTES_SENT.set(net_sent)
    SYSTEM_NETWORK_BYTES_RECV.set(net_recv)
    
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    conn_start_time = time.perf_counter()
    ACTIVE_WS_CONNECTIONS.inc()
    
    # Update peak connections
    current_ws = int(ACTIVE_WS_CONNECTIONS._value.get())
    if current_ws > getattr(app.state, "peak_ws_connections", 0):
        app.state.peak_ws_connections = current_ws
        PEAK_ACTIVE_WS_CONNECTIONS.set(current_ws)
        
    active_tasks: Dict[str, asyncio.Task] = {}
    try:
        try:
            await verify_api_key_ws(websocket)
        except HTTPException:
            return

        logger.info("WebSocket connection established")
        send_lock = asyncio.Lock()

        async def safe_send_json(data: dict):
            async with send_lock:
                try:
                    msg_type = data.get("type", "unknown")
                    WS_MESSAGES_SENT_TOTAL.labels(message_type=msg_type).inc()
                    json_str = json.dumps(data)
                    WS_BYTES_SENT_TOTAL.inc(len(json_str))
                    await websocket.send_text(json_str)
                except Exception as e:
                    logger.error(f"Error sending WS message: {e}")
                    raise

        while True:
            try:
                # Use raw receive to handle both text and binary frames gracefully
                msg = await asyncio.wait_for(websocket.receive(), timeout=WS_HEARTBEAT_TIMEOUT)
                
                if msg["type"] == "websocket.disconnect":
                    logger.info("WebSocket disconnected by client")
                    break
                
                if msg["type"] != "websocket.receive":
                    continue

                if "bytes" in msg:
                    WS_BYTES_RECEIVED_TOTAL.inc(len(msg["bytes"]))
                    WS_MESSAGES_RECEIVED_TOTAL.labels(message_type="binary").inc()
                    logger.warning("Received binary frame over WebSocket")
                    await safe_send_json({
                        "type": "error",
                        "payload": {"detail": "Binary messages are not supported. Please send JSON text."}
                    })
                    continue
                
                data = msg.get("text", "")
                WS_BYTES_RECEIVED_TOTAL.inc(len(data))
                
                if len(data) > WS_MESSAGE_SIZE_LIMIT:
                    WS_MESSAGES_RECEIVED_TOTAL.labels(message_type="oversized").inc()
                    logger.warning(f"WebSocket message exceeded size limit: {len(data)} bytes")
                    await safe_send_json({
                        "type": "error",
                        "payload": {"detail": f"Message too large (max {WS_MESSAGE_SIZE_LIMIT} bytes)"}
                    })
                    continue

                req_start_time = time.perf_counter()
                message = json.loads(data)
                if not isinstance(message, dict):
                    WS_MESSAGES_RECEIVED_TOTAL.labels(message_type="invalid_format").inc()
                    logger.warning(f"Received non-dictionary message over WebSocket: {type(message)}")
                    await safe_send_json({
                        "type": "error",
                        "payload": {"detail": "Message must be a JSON object (dictionary)"}
                    })
                    continue
                
                msg_type = message.get("type", "unknown")
                WS_MESSAGES_RECEIVED_TOTAL.labels(message_type=msg_type).inc()
            except asyncio.TimeoutError:
                logger.warning("WebSocket heartbeat timeout exceeded")
                break
            except json.JSONDecodeError:
                WS_MESSAGES_RECEIVED_TOTAL.labels(message_type="invalid_json").inc()
                logger.warning("Received invalid JSON over WebSocket")
                await safe_send_json({
                    "type": "error",
                    "payload": {"detail": "Invalid JSON received"}
                })
                continue
            except Exception as e:
                logger.error(f"Error receiving WS message: {e}")
                break
            
            request_id = message.get("request_id")
            
            try:
                if msg_type == "ping":
                    await safe_send_json({"type": "pong"})
                elif msg_type == "list_tools":
                    tools = registry.list_tools()
                    await safe_send_json({
                        "type": "tools_list",
                        "tools": tools,
                        "request_id": request_id
                    })
                elif msg_type == "list_active_tasks":
                    tasks = await registry.list_active_tasks()
                    await safe_send_json({
                        "type": "active_tasks_list",
                        "tasks": tasks,
                        "request_id": request_id
                    })
                elif msg_type == "start":
                    if registry.active_task_count >= MAX_CONCURRENT_TASKS:
                        await safe_send_json({
                            "type": "error",
                            "request_id": request_id,
                            "payload": {"detail": f"Server busy: Maximum concurrent tasks ({MAX_CONCURRENT_TASKS}) reached."}
                        })
                    else:
                        tool_name = message.get("tool_name")
                        args = message.get("args", {})
                        tool = registry.get_tool(tool_name)
                        if not tool:
                            await safe_send_json({
                                "type": "error",
                                "request_id": request_id,
                                "payload": {"detail": f"Tool not found: {tool_name}"}
                            })
                        else:
                            call_id = str(uuid.uuid4())
                            try:
                                gen = tool(**args)
                                await registry.store_task(call_id, gen, tool_name)
                                await registry.mark_consumed(call_id)
                                await safe_send_json({
                                    "type": "task_started", 
                                    "call_id": call_id, 
                                    "tool_name": tool_name, 
                                    "request_id": request_id
                                })
                                task = asyncio.create_task(run_ws_generator(safe_send_json, call_id, tool_name, gen, active_tasks))
                                active_tasks[call_id] = task
                            except Exception as e:
                                logger.error(f"Failed to start tool {tool_name} via WS: {e}", extra={"tool_name": tool_name})
                                await safe_send_json({
                                    "type": "error",
                                    "call_id": call_id,
                                    "request_id": request_id,
                                    "payload": {"detail": str(e)}
                                })
                elif msg_type == "stop":
                    call_id = message.get("call_id")
                    if call_id in active_tasks:
                        logger.info(f"Stopping task {call_id} via WebSocket request", extra={"call_id": call_id})
                        active_tasks[call_id].cancel()
                        await safe_send_json({
                            "call_id": call_id,
                            "type": "progress",
                            "payload": {"step": "Cancelled", "pct": 0, "log": "Task stopped by user."}
                        })
                        await safe_send_json({
                            "type": "stop_success",
                            "call_id": call_id,
                            "request_id": request_id
                        })
                    else:
                        # Try to stop task that might be in the registry but not in active_tasks (e.g. not being streamed yet)
                        task_data = await registry.get_task_no_consume(call_id)
                        if task_data:
                            logger.info(f"Stopping non-streamed task {call_id} via WebSocket request", extra={"call_id": call_id})
                            await task_data["gen"].aclose()
                            if not task_data["consumed"]:
                                await registry.remove_task(call_id)
                            await safe_send_json({
                                "type": "stop_success",
                                "call_id": call_id,
                                "request_id": request_id
                            })
                        else:
                            await safe_send_json({
                                "type": "error",
                                "call_id": call_id,
                                "request_id": request_id, 
                                "payload": {"detail": f"No active task found with call_id: {call_id}"}
                            })
                elif msg_type == "subscribe":
                    call_id = message.get("call_id")
                    task_data = await registry.get_task(call_id)
                    if task_data:
                        tool_name = task_data["tool_name"]
                        gen = task_data["gen"]
                        await safe_send_json({
                            "type": "task_started", 
                            "call_id": call_id, 
                            "tool_name": tool_name, 
                            "request_id": request_id
                        })
                        task = asyncio.create_task(run_ws_generator(safe_send_json, call_id, tool_name, gen, active_tasks))
                        active_tasks[call_id] = task
                    else:
                        await safe_send_json({
                            "type": "error",
                            "call_id": call_id,
                            "request_id": request_id, 
                            "payload": {"detail": f"Task not found or already being streamed: {call_id}"}
                        })
                elif msg_type == "input":
                    call_id = message.get("call_id")
                    value = message.get("value")
                    if await input_manager.provide_input(call_id, value):
                        logger.info(f"Input received for task {call_id}", extra={"call_id": call_id})
                        await safe_send_json({
                            "type": "input_success",
                            "call_id": call_id,
                            "request_id": request_id
                        })
                    else:
                        await safe_send_json({
                            "type": "error",
                            "call_id": call_id,
                            "request_id": request_id, 
                            "payload": {"detail": f"No task waiting for input with call_id: {call_id}"}
                        })
                else:
                    logger.warning(f"Unknown WebSocket message type: {msg_type}", extra={"ws_message": message})
                    await safe_send_json({
                        "type": "error",
                        "request_id": request_id, 
                        "payload": {"detail": f"Unknown message type: {msg_type}"}
                    })
            finally:
                req_latency = time.perf_counter() - req_start_time
                WS_REQUEST_LATENCY.labels(message_type=msg_type).observe(req_latency)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        ACTIVE_WS_CONNECTIONS.dec()
        conn_duration = time.perf_counter() - conn_start_time
        WS_CONNECTION_DURATION.observe(conn_duration)
        if active_tasks:
            logger.info(f"Cleaning up {len(active_tasks)} WebSocket tasks due to disconnect/timeout")
            for task in active_tasks.values():
                task.cancel()

async def run_ws_generator(send_fn, call_id: str, tool_name: str, gen, active_tasks: Dict[str, asyncio.Task]):
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
            await send_fn(event.model_dump())
    except asyncio.CancelledError:
        status = "cancelled"
        logger.info(f"WS task {call_id} cancelled")
        await gen.aclose()
    except Exception as e:
        status = "error"
        logger.error(f"Error during WS task {call_id}: {e}")
        event = ProgressEvent(call_id=call_id, type="error", payload={"detail": str(e)})
        try:
            await send_fn(event.model_dump())
        except:
            pass
    finally:
        duration = time.perf_counter() - start_time
        TASK_DURATION.labels(tool_name=tool_name).observe(duration)
        TASKS_TOTAL.labels(tool_name=tool_name, status=status).inc()
        await registry.remove_task(call_id)
        active_tasks.pop(call_id, None)
        logger.info(f"WS task finished: {call_id} (duration: {duration:.2f}s, status: {status})")

from . import dummy_tool