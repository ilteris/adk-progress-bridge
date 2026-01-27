# TODO: ADK Progress Bridge

This list tracks the remaining tasks and planned improvements for the ADK Progress Bridge project.

## 🛠 Core Backend Improvements
- [x] **Task Timeout/Cleanup:** Implement a background task to clean up abandoned tasks in `ToolRegistry` that were never streamed.
- [x] **Thread Safety:** Ensure `ToolRegistry` is thread-safe for concurrent task storage and retrieval.
- [x] **Graceful Shutdown:** Ensure active generators are closed when the server shuts down.
- [ ] **Input Validation:** Enhance validation for `args` passed to `start_task`.
- [ ] **Structured Logging:** Replace print/basic logs with structured logging for better observability.

## 🎨 Frontend Refinement
- [x] **Reconnection Logic:** Implement automatic reconnection in `useAgentStream` if the SSE connection drops.
- [x] **Advanced UI Components:** Add more visualization options for different types of tool results.
- [x] **Parameter Input:** Allow users to input tool parameters (e.g., duration) directly from the UI.
- [ ] **Dark Mode Support:** Improve UI styling to support system dark mode preferences.

## 🧪 Testing & Quality
- [ ] **Backend Unit Tests:** Add tests for `ToolRegistry`, `progress_tool` decorator, and SSE formatting.
- [ ] **API Integration Tests:** Use `TestClient` to verify the `/start_task` and `/stream` endpoints.
- [ ] **Frontend Component Tests:** Add Vitest tests for `TaskMonitor.vue` and `useAgentStream`.
- [ ] **End-to-End Tests:** Implement Playwright tests for the full flow from clicking "Start" to seeing the result.

## 📚 Documentation & Developer Experience
- [ ] **API Documentation:** Use FastAPI's Swagger UI to document the bridge endpoints.
- [ ] **Deployment Guide:** Add instructions for deploying the bridge in a production environment (e.g., GKE, Cloud Run).
- [ ] **Advanced Examples:** Create more complex dummy tools showing parallel work or sub-task progress.

## 🚀 Production Readiness
- [ ] **Authentication/Authorization:** Add middleware to secure the bridge endpoints.
- [ ] **Scalability Strategy:** Document how to handle tasks across multiple server instances (e.g., using Redis for state management).
- [ ] **Monitoring & Metrics:** Integrate with Prometheus/Grafana to track task duration and success rates.
