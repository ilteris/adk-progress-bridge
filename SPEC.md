# Specification: ADK Progress Bridge

## 1. System Overview
The system consists of a Python backend (FastAPI) acting as the ADK Agent host and a Vue.js frontend client. They communicate via **Server-Sent Events (SSE)** or **WebSockets** for real-time progress updates.

## 2. Backend Specification (Python)

### 2.1 Core Components (`backend/app/`)

#### `ProgressEvent` (Pydantic Model)
A structured container for event data.
*   `call_id`: UUID string.
*   `type`: Literal ["progress", "result", "error", "input_request", "task_started", "system_metrics"].
*   `payload`: Any event-specific data.

#### `ToolRegistry`
Manages tool registration and active task sessions.
*   `register(func)`: Decorator to register a tool.
*   `store_task(call_id, gen, tool_name)`: Persists an active generator.
*   `list_tools()`: Returns a list of all registered tool names.
*   `cleanup_tasks()`: Graceful shutdown handler.

#### `InputManager`
Manages bi-directional input for tasks that require user interaction.
*   `provide_input(call_id, value)`: Signals a waiting generator with user input.

#### `BroadcastMetricsManager`
Centralized singleton for broadcasting real-time health metrics.
*   `start()`: Begins periodic metrics gathering.
*   `stop()`: Halts gathering.
*   `subscribe(call_id)`: Returns an asyncio.Queue for receiving metrics.
*   `unsubscribe(call_id)`: Removes a listener.

### 2.2 API Endpoints (`backend/main.py`)

*   **REST Flow (SSE):**
    *   `GET /tools`: Returns a list of all registered tool names.
    *   `POST /start_task/{tool_name}`: Initiates a task, returns `call_id`.
    *   `GET /stream/{call_id}`: SSE endpoint for progress streaming.
    *   `POST /stop_task/{call_id}`: Manual termination.
    *   `POST /provide_input`: REST fallback for providing input for SSE tasks.
*   **WebSocket Flow:**
    *   `WS /ws`: Bi-directional connection for task control and streaming.
    *   Message `{"type": "list_tools", "request_id": "..."}` requests all tool names.
        *   Response: `{"type": "tools_list", "tools": [...], "request_id": "..."}`
    *   Message `{"type": "start", "tool_name": "...", "args": {...}, "request_id": "..."}` starts a task.
        *   Response: `{"type": "task_started", "call_id": "...", "tool_name": "...", "request_id": "..."}`
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

### 3.2 Component: `TaskMonitor.vue`
*   **Configuration:** UI to set tool parameters and toggle WebSocket mode.
*   **Tool Selection:** Dynamic dropdown populated via `fetchTools`.
*   **Interactive UI:** Dynamic input field appears when the agent requests input.
*   **Progress:** Animated progress bar and status labels.
*   **Console:** Real-time log output with timestamps.

## 4. Real-time System Observability
The bridge provides deep visibility into the host system performance during task execution:
1. **Periodic Metrics Injection:** The backend automatically injects system-wide health metrics (CPU, kernel stats, throughput) into the progress stream every 3 seconds for both WebSocket and SSE-based tasks, powered by a centralized singleton broadcaster for maximum efficiency.
2. **Metrics Payload:** The `system_metrics` event contains a comprehensive payload including CPU usage breakdown, memory pressure, context switches, interrupt rates, and disk/network throughput.
3. **Pydantic v2 Alignment:** The system utilizes modern Pydantic v2 `.model_dump()` and `.model_dump_json()` methods for high-performance serialization.

## 5. Implementation Details

### 4.1 Bi-directional WebSockets
The WebSocket layer allows for:
1.  **Lower Latency:** No HTTP handshake overhead for starting/stopping tasks once connected.
2.  **Explicit Correlation:** `request_id` ensures that task starts and control commands are correctly matched to their results/acknowledgements, supporting high-concurrency.
3.  **Explicit Cancellation:** Direct `stop` messages over the socket are handled instantly with success confirmation.
4.  **Connection Awareness:** The server automatically closes generators if the client disconnects.
5.  **Native Interaction:** Interactive input is sent directly back over the same socket.

### 4.2 Security
All endpoints (SSE, WS, REST) support API Key authentication via `X-API-Key` header or `api_key` query parameter.

### 4.3 Robustness & Maintenance
1.  **Heartbeats:** WebSocket connections use periodic ping/pong messages to keep the connection alive and detect dead peers.
2.  **Message Size Limiting:** Incoming WebSocket messages are limited to 1MB to prevent memory exhaustion and DoS attacks.
3.  **Automatic Reconnection:** The frontend implements exponential backoff reconnection for WebSocket connections.
4.  **Stale Task Cleanup:** A background task on the backend cleans up tasks that were initiated but never streamed/consumed within a timeout period (default 300s).
5.  **Thread-Safe Writes:** The backend uses an `asyncio.Lock` to ensure WebSocket frames are not interleaved during concurrent task streaming.
6.  **Message Buffering:** The frontend buffers incoming WebSocket messages that arrive before the UI has fully subscribed to a task, preventing race conditions.

## 6. Versioning & Identity
- **APP_VERSION**: 1.6.5
- **GIT_COMMIT**: v365-supreme-broadcaster
- **OPERATIONAL_APEX**: THE NEBULA (v365 SUPREME BROADCASTER)