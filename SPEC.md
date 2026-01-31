# Specification: ADK Progress Bridge v1.7.8

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

#### `HealthEngine` (`health.py`)
Decoupled metrics engine for deep system observability.
*   `collect_raw_metrics()`: Aggregates 100+ points of data from `psutil` and `resource`.
*   `get_health_data()`: Maps raw metrics to Prometheus Gauges and returns a structured health report.

#### `BroadcastMetricsManager` (`health.py`)
Centralized singleton for broadcasting real-time health metrics to all active streams.
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
    *   Message `{"type": "get_health"}` requests the latest system health data.
        *   Response: `{"type": "health_data", "data": {...}}`

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
  health: any | null; // Real-time system health metrics
}
```

## 4. Real-time System Observability
The bridge provides deep visibility into the host system performance:
1. **Health Engine:** A dedicated subsystem in `health.py` extracts 100+ metrics (CPU, Kernel, Throughput) with sub-second precision.
2. **Metrics Injection:** Real-time metrics are injected into progress streams every 3 seconds via a centralized singleton broadcaster.
3. **Fidelity:** Full alignment with Pydantic v2 for high-performance serialization.

## 5. Security & Robustness
*   **API Key Auth:** Mandatory for all endpoints (SSE, WS, REST).
*   **Heartbeats:** Bi-directional ping/pong every 60s.
*   **Message Limits:** 1MB ceiling on incoming WS frames.
*   **Reconnection:** Exponential backoff implemented on the frontend.
*   **Thread Safety:** `asyncio.Lock` ensures frame integrity during concurrent streaming.

## 6. Versioning & Identity
- **APP_VERSION**: 1.7.7
- **GIT_COMMIT**: v395-supreme-apex-final-signoff
- **OPERATIONAL_APEX**: SUPREME APEX FINAL SIGNOFF (v395)
