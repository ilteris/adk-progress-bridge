# Specification: ADK Progress Bridge

## 1. System Overview
The system consists of a Python backend (FastAPI) acting as the ADK Agent host and a Vue.js frontend client. They communicate via a one-way **Server-Sent Events (SSE)** channel for real-time updates and standard HTTP REST for initiating actions.

## 2. Backend Specification (Python)

### 2.1 Core Components (`backend/bridge/`)

#### `ProgressEvent` (Data Class)
A structured container for event data.
*   `call_id`: UUID string.
*   `type`: Literal ["progress", "result", "error"].
*   `payload`: Dict.

#### `ToolRegistry`
A singleton or instance that manages available tools.
*   `register(func)`: Decorator to register a tool.
*   `get(name)`: Retrieves a tool callable.

#### `execute_tool_stream(tool_name, input_data)`
A helper function that:
1.  Instantiates the generator for the named tool.
2.  Iterates through the `yield` items.
3.  Formats them as SSE-compliant strings (e.g., `data: {...}\n\n`).
4.  Yields the final result as a specific event type.

### 2.2 API Endpoints (`backend/main.py`)

*   `POST /start_task`: Accepts `{ tool_name, args }`. Returns `{ call_id }`.
*   `GET /stream/{call_id}`: Returns `Content-Type: text/event-stream`. Connects to the running generator identified by `call_id`.

## 3. Frontend Specification (Vue.js)

### 3.1 Composable: `useAgentStream.ts`
Manages the connection and state.

**State:**
```typescript
interface AgentState {
  isConnected: boolean;
  callId: string | null;
  currentStep: string;
  progressPct: number; // 0-100
  logs: string[];      // History of "step" messages
  result: any | null;
  error: string | null;
}
```

**Actions:**
*   `runTool(name, args)`: Initiates the POST request and immediately subscribes to the SSE stream.
*   `reset()`: Clears state for a new run.

### 3.2 Component: `TaskMonitor.vue`
A visual representation of the `AgentState`.
*   **Progress Bar:** Bind to `progressPct`.
*   **Status Text:** Bind to `currentStep`.
*   **Log Console:** A scrollable div rendering `logs`.
*   **Result View:** Displays the final JSON output when `result` is present.

## 4. Implementation Plan

### Phase 1: Backend Core
1.  Setup `backend/` with `FastAPI`.
2.  Implement `bridge.py` with the `ProgressEvent` model and `@progress_tool` decorator.
3.  Create a `dummy_tool.py` that simulates work (sleeps and yields progress).
4.  Implement the `/stream` endpoint.

### Phase 2: Frontend Client
1.  Scaffold a simple Vue 3 app (Vite).
2.  Implement `useAgentStream.ts`.
3.  Build `TaskMonitor.vue` using standard HTML/CSS (no heavy UI framework dependencies initially, just clean styles).

### Phase 3: Integration & Polish
1.  Connect Frontend to Backend.
2.  Verify the "Stream" flow (Progress Bar moves in real-time).
3.  Handle edge cases (errors during tool execution).
