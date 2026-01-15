# ADK Progress Bridge

A technical implementation pattern for Google ADK (Agent Development Kit) to bring real-time tool execution progress to Vue.js frontends, inspired by LangGraph's `run_writer`.

## Overview

Traditional ADK tools follow a request-response pattern. For long-running agents (e.g., complex data analysis, sub-agent orchestration, or multi-step physical audits), this results in poor UX. 

The **ADK Progress Bridge** transforms standard tools into **Async Generators** that stream intermediate status updates to the UI via Server-Sent Events (SSE).

## Backend Implementation (Python / ADK)

Tools are wrapped in an `AsyncGenerator` that yields structured progress packets before the final result.

### The Protocol
```json
{
  "type": "progress" | "result",
  "call_id": "uuid",
  "payload": {
    "step": "Analyzing masonry contracts",
    "pct": 60,
    "metadata": {}
  }
}
```

### Example Pattern
```python
async def my_long_running_tool(input_data):
    yield {"type": "progress", "step": "Phase 1: Extraction", "pct": 25}
    # ... logic ...
    yield {"type": "progress", "step": "Phase 2: Analysis", "pct": 75}
    # ... logic ...
    yield {"type": "result", "data": "Final analysis summary."}
```

## Frontend Implementation (Vue.js / Composition API)

A reactive composable manages a "Tool Registry" that tracks active tool calls and their current state.

### `useAgentStream.ts`
```typescript
import { reactive, ref } from 'vue';

export function useAgentStream() {
  const activeTools = reactive(new Map());
  const finalResponse = ref("");

  const handleStream = async (response) => {
    const reader = response.body.getReader();
    // Logic to parse SSE and update activeTools map
  };

  return { activeTools, finalResponse, handleStream };
}
```

## Benefits

- **Reduced Perceived Latency**: Users see activity immediately.
- **Granular Error Handling**: Identify exactly which step in a tool failed.
- **Framework Native**: Designed specifically for the Google ADK and Vue ecosystem.

## License
MIT
