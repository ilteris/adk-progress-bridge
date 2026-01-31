# Specification: ADK Progress Bridge

## 1. System Overview
The system consists of a Python backend (FastAPI) acting as the ADK Agent host and a Vue.js frontend client. They communicate via **Server-Sent Events (SSE)** or **WebSockets** for real-time progress updates.

## 2. Backend Specification (Python)

### 2.1 Core Components (`backend/app/`)

#### `ProgressEvent` (Pydantic Model)
A structured container for event data.
*   `call_id`: UUID string.
*   `type`: Literal ["progress", "result", "error", "input_request", "task_started"].
*   `payload`: Any event-specific data.

#### `ToolRegistry`
Manages tool registration and active task sessions.
*   `register(func)`: Decorator to register a tool.
*   `store_task(call_id, gen, tool_name)`: Persists an active generator.
*   `list_tools()`: Returns a list of all registered tool names.
*   `list_active_tasks()`: Returns a list of all currently active task sessions.
*   `cleanup_tasks()`: Graceful shutdown handler.

#### `InputManager`
Manages bi-directional input for tasks that require user interaction.
*   `provide_input(call_id, value)`: Signals a waiting generator with user input.

### 2.2 API Endpoints (`backend/main.py`)

*   **REST Flow (SSE):**
    *   `GET /tools`: Returns a list of all registered tool names.
    *   `GET /tasks`: Returns a list of all currently active task sessions in the registry.
    *   `GET /health`: Returns system health status, version (**1.2.9**), git commit, uptime, CPU count, thread count, active WebSocket connections, **WebSocket messages received/sent counters**, load average, active task count, total tasks started, memory usage, CPU usage, **Open File Descriptors count**, **Thread count**, **Network Throughput (Bytes/sec)**, **Context Switches (Voluntary/Involuntary)**, **Task Success Rate %**, and configuration parameters (heartbeat timeout, cleanup interval, max concurrent tasks, etc.). and `adk_build_info` metric. Includes comprehensive system metrics: Disk usage, Swap memory, Page faults, Network packets, CPU frequency, Disk I/O, and **Process-specific IO counters**.
    *   `GET /version`: Returns current API version (**1.2.9**), git commit hash, and operational status (e.g., "SUPREME ABSOLUTE APEX OMEGA ULTRA").
    *   `POST /start_task/{tool_name}`: Initiates a task, returns `call_id`. Returns 503 if `MAX_CONCURRENT_TASKS` (100) is reached.
    *   `GET /stream/{call_id}`: SSE endpoint for progress streaming.
    *   `POST /stop_task/{call_id}`: Manual termination.
    *   `POST /provide_input`: REST fallback for providing input for SSE tasks.
*   **WebSocket Flow:**
    *   `WS /ws`: Bi-directional connection for task control and streaming.
    *   Message `{"type": "list_tools", "request_id": "..."}` requests all tool names.
        *   Response: `{"type": "tools_list", "tools": [...], "request_id": "..."}`
    *   Message `{"type": "list_active_tasks", "request_id": "..."}` requests all currently active task sessions.
        *   Response: `{"type": "active_tasks_list", "tasks": [...], "request_id": "..."}`
    *   Message `{"type": "start", "tool_name": "...", "args": {...}, "request_id": "..."}` starts a task. Returns error if `MAX_CONCURRENT_TASKS` is reached.
        *   Response: `{"type": "task_started", "call_id": "...", "tool_name": "...", "request_id": "..."}`
    *   Message `{"type": "subscribe", "call_id": "...", "request_id": "..."}` subscribes to an existing task.
        *   Response: `{"type": "task_started", "call_id": "...", "tool_name": "...", "request_id": "..."}` followed by stream.
    *   Message `{"type": "stop", "call_id": "...", "request_id": "..."}` stops a task.
        *   Response: `{"type": "stop_success", "call_id": "...", "request_id": "..."}`
    *   Message `{"type": "input", "call_id": "...", "value": "...", "request_id": "..."}` provides interactive input.
        *   Response: `{"type": "input_success", "call_id": "...", "request_id": "..."}`
    *   Message `{"type": "ping"}` requests a heartbeat check.
        *   Response: `{"type": "pong"}`

## 3. Frontend Specification (Vue.js)

### 3.1 Composable: `useAgentStream.ts`
Reactive state manager for the bridge.

**State:**
```typescript
interface AgentState {
  status: ConnectionStatus; // idle, connecting, connected, error, waiting_for_input, etc.
  isConnected: boolean;
  callId: string | null;
  currentStep: string;
  progressPct: number;
  logs: string[];
  result: any | null;
  error: string | null;
  isStreaming: boolean;
  useWS: boolean; // Toggle between SSE and WS
  inputPrompt: string | null; // Prompt text when waiting for input
  tools: string[]; // List of available tools fetched from backend
}
```

**Actions:**
*   `fetchTools()`: Retrieves tools via REST or WebSocket depending on configuration.
*   `runTool(name, args)`: Orchestrates the connection based on `useWS` setting.
*   `stopTool()`: Sends a stop signal via WS or POST request via HTTP.
*   `sendInput(value)`: Sends interactive input via WS or REST fallback.
*   `reset()`: Cleans up connections and state.

## 4. Implementation Details

### 4.1 Bi-directional WebSockets
The WebSocket layer allows for:
1.  **Lower Latency:** No HTTP handshake overhead for starting/stopping tasks once connected.
2.  **Explicit Correlation:** `request_id` ensures that task starts and control commands are correctly matched to their results/acknowledgements, supporting high-concurrency.
3.  **Explicit Cancellation:** Direct `stop` messages over the socket are handled instantly with success confirmation.
4.  **Connection Awareness:** The server automatically closes generators if the client disconnects.
5.  **Native Interaction:** Interactive input is sent directly back over the same socket.
6.  **Cross-Protocol Monitoring:** The `subscribe` command allows a WebSocket client to monitor a task started via REST/SSE.
7.  **Real-time Monitoring:** The `list_active_tasks` message enables clients to monitor all ongoing task sessions across the system.

### 4.2 Security
All endpoints (SSE, WS, REST) support API Key authentication via `X-API-Key` header or `api_key` query parameter.

### 4.3 Robustness & Maintenance
1.  **Heartbeats:** WebSocket connections use periodic ping/pong messages to keep the connection alive and detect dead peers.
2.  **Message Size Limiting:** Incoming WebSocket messages are limited to 1MB to prevent memory exhaustion and DoS attacks.
3.  **Automatic Reconnection:** The frontend implements exponential backoff reconnection for WebSocket connections.
4.  **Stale Task Cleanup:** A background task on the backend cleans up tasks that were initiated but never streamed/consumed within a timeout period (default 300s).
5.  **Thread-Safe Writes:** The backend uses an `asyncio.Lock` to ensure WebSocket frames are not interleaved during concurrent task streaming.
6.  **Message Buffering:** The frontend buffers incoming WebSocket messages that arrive before the UI has fully subscribed to a task, preventing race conditions.
7.  **Operational Visibility:** Enhanced health monitoring with real-time tracking of active WebSocket connections, total message throughput (**Bytes/sec**), and resource utilization (CPU, Memory, FDs, Threads, **Context Switches**).
8.  **Concurrency Management:** Backend enforces a hard limit on the number of concurrent task generators in the registry to protect server resources.
9.  **Supreme Observability:** Version 1.2.9 (v339) introduces **Omega Plus Ultra** tier observability, including system-wide swap memory metrics and **Process-specific IO counters** (Read/Write bytes and counts).