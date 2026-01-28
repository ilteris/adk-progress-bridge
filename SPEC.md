# Specification: ADK Progress Bridge

## 1. System Overview
The system consists of a Python backend (FastAPI) acting as the ADK Agent host and a Vue.js frontend client. They communicate via **Server-Sent Events (SSE)** or **WebSockets** for real-time progress updates.

## 2. Backend Specification (Python)

### 2.1 Core Components (`backend/app/`)

#### `ProgressEvent` (Pydantic Model)
A structured container for event data.
*   `call_id`: UUID string.
*   `timestamp`: Unix timestamp (float) for event correlation.
*   `type`: Literal ["progress", "result", "error", "input_request", "task_started"].
*   `payload`: Any event-specific data.

#### `ToolRegistry`
Manages tool registration and active task sessions.
*   `register(func)`: Decorator to register a tool.
*   `store_task(call_id, gen, tool_name)`: Persists an active generator. Raises `ValueError` if `call_id` already exists (collision protection).
*   `list_tools()`: Returns a list of all registered tool names.
*   `cleanup_tasks()`: Graceful shutdown handler.

#### `InputManager`
Manages bi-directional input for tasks that require user interaction.
*   `provide_input(call_id, value)`: Signals a waiting generator with user input.

### 2.2 API Endpoints (`backend/main.py`)

*   **REST Flow (SSE):**
    *   `GET /tools`: Returns a list of all registered tool names.
    *   `POST /start_task/{tool_name}`: Initiates a task, returns `call_id` and `timestamp`.
    *   `GET /stream/{call_id}`: SSE stream for progress.
    *   `POST /stop_task/{call_id}`: Manual termination of SSE task.
    *   `POST /provide_input`: REST fallback to provide input for SSE tasks.
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

## 4. Implementation Details

### 4.1 Bi-directional WebSockets
The WebSocket layer allows for:
1.  **Lower Latency:** No HTTP handshake overhead for starting/stopping tasks once connected.
2.  **Explicit Correlation:** `request_id` ensures that task starts and control commands are correctly matched to their results/acknowledgements, supporting high-concurrency.
3.  **Explicit Cancellation:** Direct `stop` messages over the socket are handled instantly with success confirmation.
4.  **Connection Awareness:** The server automatically closes generators if the client disconnects.
5.  **Native Interaction:** Interactive input is sent directly back over the same socket.

### 4.2 Security
All endpoints (SSE, WS, REST) support API Key authentication via `X-API-Key` header or `api_key` query parameter.