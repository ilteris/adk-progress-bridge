# ADK Progress Bridge

A technical implementation pattern for Google ADK (Agent Development Kit) to bring real-time tool execution progress to Vue.js frontends.

## ❓ The Problem: The "Black Box" Tool
In the standard ADK (and most GenAI) architecture, tools are treated as atomic "black boxes":
1.  Agent calls Tool.
2.  **... Silence (User sees a generic spinner) ...**
3.  Tool returns Output.

For complex tasks—like database migrations, multi-step audits, or deep research—this "silence" can last 30+ seconds. Users lose trust, wondering if the system has hung.

## 💡 The Solution: Async Generator Bridge
We transform standard tools into **Async Generators**. instead of just returning a value, the tool `yield`s intermediate status updates ("breadcrumbs") which are immediately streamed to the frontend via Server-Sent Events (SSE).

### Architectural Decision: Why "Pure" Generators?
We explicitly chose **Native Python Async Generators** over frameworks like LangChain's `dispatch_custom_event`.

| Feature | 🐍 Pure Generators (This Project) | 🦜 LangChain Events |
| :--- | :--- | :--- |
| **Philosophy** | "Pythonic" Native | Framework Specific |
| **Dependencies** | Zero (Standard Lib) | Heavy (LangChain Core) |
| **Control Flow** | Direct `yield` control | Indirect Callbacks/Managers |
| **Debugging** | Standard Stack Trace | Complex Handler Chains |

**Verdict:** By using native `yield`, we keep the implementation lightweight, easy to test, and universally compatible with any Python-based ADK agent, without forcing a heavy dependency on the project.

## 🛠️ The Architecture

### 1. The Protocol (SSE)
We define a strict JSON schema for the events streamed over the wire.
```json
// Event: "progress"
{
  "call_id": "550e8400-e29b...",
  "type": "progress",
  "payload": {
    "step": "Scanning Index",
    "pct": 45,
    "log": "Found 1500 records..."
  }
}

// Event: "result"
{
  "call_id": "550e8400-e29b...",
  "type": "result",
  "payload": {
    "summary": "Scan complete. 12 issues found."
  }
}
```

### 2. Backend (Python)
*   **`@progress_tool` Decorator:** Transforms a standard function into a tracked generator.
*   **`BridgeServer`:** A lightweight FastAPI wrapper that handles the SSE connection and manages the generator lifecycle.

### 3. Frontend (Vue.js)
*   **`useAgentStream`:** A Vue composable that connects to the SSE stream.
*   **Reactive State:** Automatically updates a `currentTask` object with the latest progress bar percentage and logs.

### 4. Scalability
For information on horizontal scaling, distributed workers, and Redis integration, see [SCALABILITY.md](SCALABILITY.md).

## 🚀 Production Integration Guide

Integrating this bridge into your existing ADK agent service is straightforward.

### Step 1: Install Core Files
Copy `backend/app/bridge.py` into your project (e.g., `src/utils/adk_bridge.py`).

### Step 2: Decorate Your Tools
Convert your long-running functions into async generators using `@progress_tool`.

```python
# BEFORE
def analyze_contracts(folder_path: str):
    data = load_files(folder_path)
    report = generate_report(data)
    return report

# AFTER
from src.utils.adk_bridge import progress_tool, ProgressPayload

@progress_tool(name="analyze_contracts")
async def analyze_contracts(folder_path: str):
    yield ProgressPayload(step="Loading Files", pct=10, log="Reading 50 files...")
    data = await load_files_async(folder_path)
    
    yield ProgressPayload(step="Generating Report", pct=80, log="Running AI analysis...")
    report = await generate_report_async(data)
    
    # The final yield is the return value
    yield report 
```

### Step 3: Mount the Endpoints
In your main FastAPI app, mount the bridge endpoints or import them directly.

```python
from fastapi import FastAPI
from src.utils.adk_bridge import registry, ProgressEvent, format_sse, ProgressPayload

app = FastAPI()

# ... existing routes ...

# Add the Bridge Endpoints
@app.post("/start_task/{tool_name}")
async def start_task(tool_name: str, args: dict = {}):
    # ... copy logic from backend/app/main.py ...
    pass

@app.get("/stream/{call_id}")
async def stream_task(call_id: str):
    # ... copy logic from backend/app/main.py ...
    pass
```

### Step 4: Frontend Hook
Use the composable in your Vue application.

```typescript
import { useAgentStream } from '@/composables/useAgentStream'

const { state, runTool } = useAgentStream()

// Trigger the tool
const handleAnalyze = () => {
    runTool('analyze_contracts', { folder_path: '/docs/legal' })
}

// Template
<div v-if="state.isStreaming">
    Progress: {{ state.progressPct }}%
    Current Step: {{ state.currentStep }}
</div>
```

## 🤖 AI Agent Skill

This project includes an AI agent skill at `.agent/skills/progress-bridge/SKILL.md`.

**What's in the skill:**
- **When to use** — Identifies scenarios where this pattern applies
- **Core pattern** — Quick-reference code for backend and frontend
- **Key files reference** — Table linking to all important files
- **SSE event schema** — The JSON contract
- **New tool checklist** — Step-by-step for adding tools
- **Common mistakes** — Gotchas to avoid

When an AI agent with this skill encounters a task involving real-time progress streaming, it will automatically reference this skill for the correct implementation pattern.

## License
MIT