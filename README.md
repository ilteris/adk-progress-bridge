# ADK Progress Bridge

A real-time progress bridge between long-running agent tools and a frontend/TUI. Built for high-fidelity agent status monitoring.

**Current Version:** 1.0.8 ("SUPREME ABSOLUTE APEX")

## 🚀 Key Features

- **Bi-directional WebSockets:** Real-time progress updates, task cancellation, and interactive input.
- **Server-Sent Events (SSE):** Robust fallback for uni-directional streaming.
- **Dynamic Tool Discovery:** Tools are automatically registered and can be listed via REST or WebSocket.
- **Multi-task Concurrency:** Handle multiple independent streams simultaneously over a single WebSocket.
- **Robustness Built-in:**
  - Thread-safe WebSocket writes.
  - Exponential backoff reconnection on the frontend.
  - Heartbeat support and timeout management.
  - Message buffering to prevent race conditions.
  - Stale task cleanup on the backend.
- **Security:** API Key authentication for all communication channels.
- **Observability:** Integrated Prometheus metrics for task duration and status.

## 🛠️ Tech Stack

- **Backend:** FastAPI (Python)
- **Frontend:** Vue 3, Vite, TypeScript, Bootstrap
- **Communication:** WebSockets, Server-Sent Events (SSE)
- **Testing:** Pytest (Backend), Vitest (Frontend Unit), Playwright (E2E)

## 🏁 Getting Started

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 3. Verification
Run the supreme verification suite to ensure all 106 tests pass:
```bash
python3 verify_supreme.py
```

## 📚 Documentation

See [SPEC.md](SPEC.md) for protocol details and [rules.md](rules.md) for architectural constraints.

## 🧪 License
MIT