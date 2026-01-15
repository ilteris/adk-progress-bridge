---
name: ADK Progress Bridge
description: Transform long-running AI tools into real-time SSE progress streams
---

# ADK Progress Bridge Skill

This skill teaches how to implement real-time progress streaming for GenAI/ADK tools using async generators and Server-Sent Events.

## When to Use This Skill

- Building long-running AI tools (>5 seconds) that need user feedback
- Implementing multi-step workflows with progress tracking
- Creating audit, analysis, or data processing tools
- Any tool where "silence" during execution is a UX problem

## Core Pattern

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

### 2. Frontend: SSE Composable

```typescript
import { useAgentStream } from '@/composables/useAgentStream'

const { state, runTool } = useAgentStream()
await runTool('my_tool', { arg: 'value' })

// Reactive state: state.progressPct, state.currentStep, state.logs
```

## Key Files Reference

| File | Purpose |
|------|---------|
| `backend/app/bridge.py` | Core: `ProgressPayload`, `@progress_tool`, `ToolRegistry` |
| `backend/app/main.py` | API: `/start_task`, `/stream` endpoints |
| `frontend/src/composables/useAgentStream.ts` | Vue composable for SSE |
| `frontend/src/components/TaskMonitor.vue` | UI component example |

## SSE Event Schema

```json
{
  "call_id": "uuid",
  "type": "progress|result|error",
  "payload": { "step": "...", "pct": 0-100, "log": "..." }
}
```

## Adding a New Tool Checklist

1. [ ] Create `backend/app/my_tool.py` with `@progress_tool` decorator
2. [ ] Implement async generator yielding `ProgressPayload` + final `dict`
3. [ ] Import in `backend/app/main.py` to register
4. [ ] Test via `/verify-stream` workflow or `verify_stream.py`

## Common Mistakes

- ❌ Forgetting to yield a final `dict` (tool hangs)
- ❌ Not importing tool in `main.py` (404 on `/start_task`)
- ❌ Using sync functions instead of async generators
- ❌ Not closing EventSource on result/error in frontend
