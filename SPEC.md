# ADK Progress Bridge Specification

## 1. Overview
The ADK Progress Bridge facilitates real-time communication between long-running Python tools (typically part of an Agent Development Kit) and a monitoring interface (Web or TUI).

## 2. Communication Protocols

### 2.1 Backend (Python/FastAPI)

#### `ToolRegistry`
Manages tool registration and active task sessions.
*   `register(func)`: Decorator to register a tool.
*   `store_task(call_id, gen, tool_name)`: Persists an active generator.
*   `list_tools()`: Returns a list of all registered tool names.
*   `list_active_tasks()`: Returns a list of all currently active task sessions.
*   `cleanup_tasks()`: Graceful shutdown handler.

#### `InputManager`
Manages bi-directional input for tasks that require user interaction.
*   `wait_for_input(call_id, prompt)`: Pauses execution until user provides input.

#### API Endpoints
*   **REST Flow (SSE):**
    *   `GET /tools`: Returns a list of all registered tool names.
    *   `GET /tasks`: Returns a list of all currently active task sessions in the registry.
    *   `GET /health`: Returns system health status, version (**1.4.8**), git commit, uptime, CPU count, thread count, active WebSocket connections, **WebSocket messages received/sent counters**, load average, active task count, total tasks started, memory usage, CPU usage, **Open File Descriptors count**, **Thread count**, **Network Throughput (Bytes/sec)**, **Context Switches (Voluntary/Involuntary)**, **Task Success Rate %**, and configuration parameters (heartbeat timeout, cleanup interval, max concurrent tasks, etc.). and `adk_build_info` metric. Includes comprehensive system metrics: Disk usage, Swap memory, Page faults, Network packets, CPU frequency, Disk I/O, and **Process-specific IO counters including real-time throughput**.
    *   `GET /version`: Returns current API version (**1.4.8**), git commit hash, and operational status (e.g., "THE OMEGA").
    *   `POST /start_task/{tool_name}`: Initiates a task, returns `call_id`. Returns 503 if `MAX_CONCURRENT_TASKS` (100) is reached.
    *   `GET /stream/{call_id}`: SSE endpoint for progress streaming.
    *   `POST /stop_task/{call_id}`: Manual termination.
    *   `POST /provide_input`: REST fallback for providing input for SSE tasks.
*   **WebSocket Flow (Bi-directional):**
    *   `WS /ws`: Bi-directional connection for task control and streaming.
    *   Message `{"type": "list_tools", "request_id": "..."}` requests all tool names.
        *   Response: `{"type": "tools_list", "tools": [...], "request_id": "..."}`
    *   Message `{"type": "list_active_tasks", "request_id": "..."}` requests all currently active task sessions.
        *   Response: `{"type": "active_tasks_list", "tasks": [...], "request_id": "..."}`
    *   Message `{"type": "get_health", "request_id": "..."}` requests comprehensive system health data.
        *   Response: `{"type": "health_data", "data": {...}, "request_id": "..."}`
    *   Message `{"type": "start", "tool_name": "...", "args": {...}, "request_id": "..."}` starts a task. Returns error if `MAX_CONCURRENT_TASKS` is reached.
        *   Response: `{"type": "task_started", "call_id": "...", "tool_name": "...", "request_id": "..."}`
    *   Message `{"type": "subscribe", "call_id": "...", "request_id": "..."}` subscribes to an existing task.
        *   Response: `{"type": "task_started", "call_id": "...", "tool_name": "...", "request_id": "..."}` followed by stream.
    *   Message `{"type": "stop", "call_id": "...", "request_id": "..."}` stops a task.
        *   Response: `{"type": "stop_success", "call_id": "...", "request_id": "..."}`
    *   Message `{"type": "input", "call_id": "...", "value": "...", "request_id": "..."}` provides interactive input.
        *   Response: `{"type": "input_success", "call_id": "...", "request_id": "..."}`
    *   Message `{"type": "ping"}` keeps connection alive.
        *   Response: `{"type": "pong"}`

### 3. Frontend (Vue.js/TypeScript)

#### `useAgentStream` Composable
Manages reactive state and connection logic.
```typescript
interface AgentState {
  status: 'idle' | 'connecting' | 'connected' | 'reconnecting' | 'streaming' | 'waiting_for_input' | 'completed' | 'error';
  progress: ProgressPayload | null;
  result: any | null;
  error: string | null;
  useWS: boolean; // Toggle between SSE and WebSocket
}
```
*   `runTool(name, args)`: Initiates tool execution.
*   `stopTool()`: Cancels current execution.
*   `sendInput(value)`: Sends interactive input via WS or REST fallback.
*   `reset()`: Cleans up connections and state.

## 4. Implementation Details

### 4.1 Bi-directional WebSockets
The WebSocket layer allows for:
1.  **Sub-millisecond latency:** Superior to SSE for high-frequency updates.
2.  **Stateful connection:** Tools can be managed over a single socket.
3.  **Explicit Cancellation:** Direct `stop` messages over the socket are handled instantly with success confirmation.
4.  **Connection Awareness:** The server automatically closes generators if the client disconnects.
5.  **Native Interaction:** Interactive input is sent directly back over the same socket.
6.  **Cross-Protocol Monitoring:** The `subscribe` command allows a WebSocket client to monitor a task started via REST/SSE.
7.  **Real-time Monitoring:** The `list_active_tasks` message enables clients to monitor all ongoing task sessions across the system.
8.  **Native Health Protocol:** The `get_health` message allows clients to fetch full system telemetry without secondary HTTP polling.

### 4.2 Security
All endpoints (SSE, WS, REST) support API Key authentication via `X-API-Key` header or `api_key` query parameter.

### 4.3 Robustness
1.  **Heartbeat Support:** Backend monitors connection activity to prevent silent drops.
2.  **Exponential Backoff:** Frontend automatically attempts reconnection on connection loss.
3.  **Thread-Safe Tool Registry:** Registry uses locks to prevent race conditions during task management.
4.  **Stale Task Cleanup:** A background task on the backend cleans up tasks that were initiated but never streamed/consumed within a timeout period (default 300s).
5.  **Thread-Safe Writes:** The backend uses an `asyncio.Lock` to ensure WebSocket frames are not interleaved during concurrent task streaming.
6.  **Message Buffering:** The frontend buffers incoming WebSocket messages that arrive before the UI has fully subscribed to a task, preventing race conditions.
7.  **Operational Visibility:** Enhanced health monitoring with real-time tracking of active WebSocket connections, total message throughput (**Bytes/sec**), and resource utilization (CPU, Memory, FDs, Threads, **Context Switches**).
8.  **Concurrency Management:** Backend enforces a hard limit on the number of concurrent task generators in the registry to protect server resources.
9.  **THE ETERNITY Observability:** Version 1.4.8 (v358) reaches the ultimate operational apex, adding real-time process-level disk I/O throughput monitoring and resource utilization relative to limits. Includes all previous tiers: Apotheosis, Nirvana, Beyond Singularity, Ascension Singularity, Transcendence, Omnipotence, Deification, and THE OVERLORD.