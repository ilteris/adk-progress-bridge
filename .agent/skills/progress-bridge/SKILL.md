---
name: ADK Progress Bridge
description: Transform long-running AI tools into real-time SSE/WebSocket progress streams
---

# ADK Progress Bridge Skill

This skill teaches how to implement real-time progress streaming for GenAI/ADK tools using async generators, Server-Sent Events (SSE), and WebSockets.

## When to Use This Skill

- Building long-running AI tools (>5 seconds) that need user feedback.
- Implementing multi-step workflows with progress tracking.
- Requiring **bi-directional** interaction (e.g., stopping/cancelling a task in-flight).
- Needing sub-millisecond task state synchronization.

## Core Patterns

### 1. Backend: Async Generator Tool

```python
from backend.app.bridge import progress_tool, ProgressPayload

@progress_tool(name="my_tool")
async def my_tool(args):
    # Yield progress updates
    yield ProgressPayload(step="Working...", pct=50, log="Details here")
    
    # Yield final result (must be dict)
    yield {"status": "complete", "data": result}
```

### 2. Frontend: Streaming Composable

```typescript
import { useAgentStream } from '@/composables/useAgentStream'

const { state, runTool, stopTool } = useAgentStream()

// Option A: Server-Sent Events (Default)
state.useWS = false
await runTool('my_tool', { arg: 'value' })

// Option B: WebSockets (Bi-directional)
state.useWS = true
await runTool('my_tool', { arg: 'value' })
// Later...
stopTool() // Sends 'stop' message to backend
```

## Key Files Reference

| File | Purpose |
|------|---------|
| `backend/app/bridge.py` | Core: `ProgressPayload`, `@progress_tool`, `ToolRegistry` |
| `backend/app/main.py` | API: `/stream` (SSE) and `/ws` (WebSocket) endpoints |
| `frontend/src/composables/useAgentStream.ts` | Vue composable for SSE/WS |
| `frontend/src/components/TaskMonitor.vue` | UI component example |

## Communication Protocols

### SSE (One-Way)
- `POST /start_task` -> returns `call_id`
- `GET /stream/{call_id}` -> streams `ProgressEvent`

### WebSocket (Bi-directional)
- `WS /ws` -> Upgrade
- Message `{"type": "start", "tool_name": "...", "args": {...}}` -> starts task
- Message `{"type": "stop", "call_id": "..."}` -> cancels task
- Server sends `ProgressEvent` JSON objects.

## Common Mistakes

- ❌ Forgetting to yield a final `dict` (tool hangs).
- ❌ Not importing tool in `main.py` (404 on `/start_task`).
- ❌ WebSocket: Forgetting that `run_ws_generator` must be an `asyncio.Task` to be cancellable.
- ❌ Not closing generators via `.aclose()` on cancellation (leads to memory leaks/stale tasks).