# Project Rules: ADK Progress Bridge

## 1. Technology Stack

### Backend (Python)
- **Framework**: FastAPI only
- **Async Pattern**: Native Python async generators for progress streaming
- **No Heavy Dependencies**: Avoid LangChain or similar frameworks for the bridge logic

### Frontend (Vue.js)
- **Framework**: Vue 3 with Composition API
- **Build Tool**: Vite
- **Styling**: Clean CSS or Bootstrap. **No Glassmorphism.**
- **State**: Use composables for state management

## 2. Architecture Constraints

### Communication Protocols
The bridge supports both **Server-Sent Events (SSE)** and **WebSockets (WS)**.

#### SSE Flow (Uni-directional)
- `GET /health`: Returns system health status, version, git commit, uptime, CPU count, load average, and active task count. 
- `GET /version`: Returns API version, git commit hash, and operational status.
- `GET /tools`: Returns a list of all registered tool names.
- `POST /start_task/{tool_name}`: Initiates a tool, returns `{ call_id }`.
- `GET /stream/{call_id}`: SSE endpoint for progress streaming.
- `POST /provide_input`: REST fallback for providing user input mid-execution.
- `POST /stop_task/{call_id}`: Manual termination.

#### WebSocket Flow (Bi-directional)
- `WS /ws`: Bi-directional connection for task control and streaming.
- Message `{"type": "list_tools", "request_id": "..."}` -> Server responds with `{"type": "tools_list", "tools": [...], "request_id": "..."}`.
- Message `{"type": "start", "tool_name": "...", "args": {...}, "request_id": "..."}` starts a task -> Server responds with `{"type": "task_started", "call_id": "...", "tool_name": "...", "request_id": "..."}` to confirm start.
- Message `{"type": "subscribe", "call_id": "...", "request_id": "..."}` subscribes to an existing task -> Server responds with `{"type": "task_started", "call_id": "...", "tool_name": "...", "request_id": "..."}` followed by the event stream.
- Message `{"type": "stop", "call_id": "...", "request_id": "..."}` stops a task -> Server responds with `{"type": "stop_success", "call_id": "...", "request_id": "..."}`.
- Message `{"type": "input", "call_id": "...", "value": "...", "request_id": "..."}` provides interactive input -> Server responds with `{"type": "input_success", "call_id": "...", "request_id": "..."}`.
- Message `{"type": "ping"}` -> Server responds with `{"type": "pong"}`.

#### Event Schema
- All progress events MUST follow the `ProgressEvent` schema defined in `backend/app/bridge.py`.
- Event types are strictly: `"progress"`, `"result"`, `"error"`, `"input_request"`, `"task_started"`.
- Always include `call_id` for event correlation.

### Tool Registration
- All tools MUST use the `@progress_tool` decorator.
- Tools MUST be async generators that yield `ProgressPayload` for progress and a `dict` for final result.
- Tools MUST be imported in `main.py` to register them.

## 3. Code Quality

### Python
- Use type hints everywhere.
- Use Pydantic models for data validation.
- Follow PEP 8 style guide.

### TypeScript/Vue
- Use TypeScript for all `.ts` and `.vue` files.
- Define interfaces for all data structures.
- Use `<script setup lang="ts">` syntax in Vue components.

## 4. API Design
- CORS must be enabled for local development.
- Support API Key authentication via `X-API-Key` header or `api_key` query parameter.

## 5. Robustness
- **Message Size Limit**: WebSocket messages are limited to 1MB.
- **Heartbeats**: Bi-directional ping/pong every 30-60 seconds.
- **Reconnection**: Frontend must implement exponential backoff reconnection.
- **Thread Safety**: Concurrent WebSocket writes must be protected by a lock.

## 6. Testing & Verification
- Use `verify_stream.py` for manual SSE testing.
- Use `verify_websocket.py` for manual WebSocket testing.
- Frontend composables should be testable in isolation using Vitest.
- Robustness tests (concurrency, timeouts, size limits) MUST be included in the backend test suite.