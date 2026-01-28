# ADK Progress Bridge

A technical implementation pattern for Google ADK (Agent Development Kit) to bring real-time tool execution progress to Vue.js frontends.

## ❓ The Problem: The "Black Box" Tool
In the standard ADK (and most GenAI) architecture, tools are treated as atomic "black boxes":
1.  Agent calls Tool.
2.  **... Silence (User sees a generic spinner) ...**
3.  Tool returns Output.

For complex tasks—like database migrations, multi-step audits, or deep research—this "silence" can last 30+ seconds. Users lose trust, wondering if the system has hung.

## 💡 The Solution: Async Generator Bridge
We transform standard tools into **Async Generators**. instead of just returning a value, the tool `yield`s intermediate status updates ("breadcrumbs") which are immediately streamed to the frontend via **Server-Sent Events (SSE)** or **WebSockets**.

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

### 1. The Protocol (SSE & WebSocket)
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

// Event: "input_request" (WebSocket Only)
{
  "call_id": "550e8400-e29b...",
  "type": "input_request",
  "payload": {
    "prompt": "Continue to phase 2? (yes/no)"
  }
}

// Event: "ping"
{
  "type": "ping"
}

// Event: "tools_list"
{
  "type": "tools_list",
  "tools": ["tool1", "tool2"],
  "request_id": "req-123"
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
*   **`ToolRegistry`:** Manages available tools and active sessions.
*   **`InputManager`:** Handles bi-directional futures for mid-execution user input.
*   **FastAPI Endpoints:** 
    *   `/start_task`: Traditional REST for SSE flow.
    *   `/stream`: SSE output stream.
    *   `/ws`: Bi-directional WebSocket for sub-millisecond sync, task cancellation, and **interactive input**.

### 3. Frontend (Vue.js)
*   **`useAgentStream`:** A Vue composable that connects via SSE or WebSocket.
*   **Reactive State:** Automatically updates a `state` object with progress bars, logs, and results.

### 4. Scalability
For information on horizontal scaling, distributed workers, and Redis integration, see [SCALABILITY.md](SCALABILITY.md).

## 🚀 Production Integration Guide

### Step 1: Install Core Files
Copy `backend/app/bridge.py` into your project.

### Step 2: Decorate Your Tools
```python
from src.utils.adk_bridge import progress_tool, ProgressPayload, input_manager

@progress_tool(name="analyze_contracts")
async def analyze_contracts(folder_path: str):
    yield ProgressPayload(step="Loading Files", pct=10, log="Reading 50 files...")
    
    # Optional: Request input mid-execution (WS Only)
    yield {"type": "input_request", "payload": {"prompt": "Confirm scan?"}}
    response = await input_manager.wait_for_input(call_id, "Confirm scan?")
    
    yield ProgressPayload(step="Processing", pct=100, log=f"User said {response}")
    yield {"status": "complete"}
```

### Step 3: Frontend Hook
```typescript
import { useAgentStream } from '@/composables/useAgentStream'

const { state, runTool, stopTool, sendInput } = useAgentStream()

// Trigger the tool (default is SSE, set state.useWS = true for WebSocket)
const handleAnalyze = () => {
    runTool('analyze_contracts', { folder_path: '/docs/legal' })
}

// Handle an input request from the agent
const handleUserResponse = (val: string) => {
    sendInput(val)
}
```

## 🛠️ Bi-directional WebSocket Protocol Details
The WebSocket layer allows for:
1.  **Lower Latency:** No HTTP handshake overhead for starting/stopping tasks once connected.
2.  **Explicit Correlation:** `request_id` allows matching commands to responses in high-concurrency scenarios.
3.  **Explicit Cancellation:** Direct `stop` messages over the socket are handled instantly with success confirmation.
4.  **Connection Awareness:** The server automatically closes generators if the client disconnects.
5.  **Native Interaction:** Interactive input is sent directly back over the same socket.

## 🤖 AI Agent Skill

This project includes an AI agent skill at `.agent/skills/progress-bridge/SKILL.md`.

## License
License: MIT