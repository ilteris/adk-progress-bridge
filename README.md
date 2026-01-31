# ADK Progress Bridge

A technical implementation pattern for Google ADK (Agent Development Kit) to bring real-time tool execution progress and deep system observability to Vue.js frontends.

## ❓ The Problem: The "Black Box" Tool
In the standard ADK architecture, tools are treated as atomic "black boxes". Users often experience a "silence gap" during long-running tasks, leading to a loss of trust and clarity.

## 💡 The Solution: Async Generator Bridge + Health Engine
We transform standard tools into **Async Generators**. instead of just returning a value, the tool `yield`s intermediate status updates which are streamed to the frontend via **SSE** or **WebSockets**.

Furthermore, we've integrated a dedicated **Health Engine** (`health.py`) that monitors 100+ system metrics in real-time, injecting them into the progress stream for ultimate visibility.

### Key Architectural Pillars
- **Native Python Async Generators:** Lightweight, zero-dependency progress tracking.
- **Bi-directional WebSockets:** Sub-millisecond sync for task control, cancellation, and interactive input.
- **Health Subsystem:** Decoupled metrics collection and broadcasting engine.
- **Absolute Fidelity:** Fully verified with 100% test coverage and Pydantic v2 alignment.

## 🚀 Getting Started

### Backend (Python)
- **`@progress_tool` Decorator:** Track your tool's progress.
- **`HealthEngine`:** Deep system observability out of the box.
- **`BroadcastMetricsManager`:** Centralized metrics broadcasting.

### Frontend (Vue.js)
- **`useAgentStream`:** Composable for connecting via SSE or WS.
- **Live Dashboard:** Reactive state including logs, progress bars, and system health.

## 📚 Documentation
For detailed protocol specs, see [SPEC.md](SPEC.md). For scalability and production deployment, see [SCALABILITY.md](SCALABILITY.md) and [DEPLOYMENT.md](DEPLOYMENT.md).

## 🤖 AI Agent Skill
Includes a pre-configured skill at `.agent/skills/progress-bridge/SKILL.md`.

## License
License: MIT