# Specification: ADK Progress Bridge v2.12.61

## Overview
The ADK Progress Bridge is a high-performance middleware designed to connect background tools/tasks with a real-time terminal user interface (TUI). It provides a standardized protocol for reporting progress, logs, and results via Server-Sent Events (SSE) and WebSockets.

## 1. Architectural Components

### 1.1 Backend (FastAPI)
- **Tool Registry**: Manages registered tools and their metadata.
- **Task Manager / Broadcaster**: Orchestrates task execution and broadcasts events to multiple subscribers via `TaskBroadcaster`.
- **Event History Replay**: Maintains a buffer of task events, allowing late subscribers to see the full execution history.
- **WebSocket Manager**: Handles bi-directional communication, heartbeats, and correlation.
- **Health Engine**: Provides deep system metrics and audit data.
- **Structured Logging**: JSON-based logging with context tracking (call_id, tool_name).

### 1.2 Frontend (Vue 3 / Pinia)
- **WebSocket Manager**: Manages connection lifecycle with exponential backoff and shared connection support.
- **useAgentStream**: Composable for managing task state and streaming updates.
- **Material 3 UI**: Clean, responsive interface for monitoring tasks.

## 2. Protocol Specification

### 2.1 WebSocket Messages

#### Client to Server
- `ping`: Keep-alive heartbeat.
- `list_tools`: Request available tools.
- `list_active_tasks`: Request currently running tasks.
- `get_health`: Request system health and audit data.
- `start`: Initialize a new tool execution.
- `stop`: Terminate a running task.
- `subscribe`: Connect to an existing task stream (supports history replay).
- `input`: Provide input for a waiting task.

#### Server to Client
- `connected`: Handshake acknowledgement.
- `pong`: Heartbeat response.
- `tools_list`: List of available tools.
- `active_tasks_list`: List of active tasks.
- `health_data`: System metrics and audit findings.
- `task_started`: Confirmation of task initiation.
- `progress`: Incremental update (step, pct, log).
- `input_request`: Request for user input.
- `result`: Final task outcome.
- `error`: Failure notification.
- `system_metrics`: Real-time performance data.

## 3. Security & Stability

### 3.1 Authentication
- API Key based authentication for both REST and WebSocket endpoints.
- WebSocket handshake verification via query parameters.

### 3.2 Robustness
- **Broadcasting Engine**: Decouples tool execution from client connection.
- **Thread-Safe Writes**: Mutex-protected WebSocket message sending.
- **Error Correlation**: `request_id` tracking across asynchronous boundaries.
- **Reconnection**: Frontend automatically reconnects with backoff.
- **Input Validation**: Strict Pydantic models for API requests.

## 4. Auditing & Monitoring
(Comprehensive list of 2600 audit tools for system performance, process state, and network health)

## 5. Metadata
- **APP_VERSION**: 2.12.59
- **BUILD_TIMESTAMP**: 2026-02-02T23:30:00Z
- **GIT_COMMIT**: v837-supreme-apex-2600
- **OPERATIONAL_APEX**: v837 SUPREME APEX 2600 VERIFICATION