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

### SSE Protocol
- All progress events MUST follow the `ProgressEvent` schema defined in `backend/app/bridge.py`
- Event types are strictly: `"progress"`, `"result"`, `"error"`
- Always include `call_id` for event correlation

### Tool Registration
- All tools MUST use the `@progress_tool` decorator
- Tools MUST be async generators that yield `ProgressPayload` for progress and a `dict` for final result
- Tools MUST be imported in `main.py` to register them

## 3. Code Quality

### Python
- Use type hints everywhere
- Use Pydantic models for data validation
- Follow PEP 8 style guide

### TypeScript/Vue
- Use TypeScript for all `.ts` and `.vue` files
- Define interfaces for all data structures
- Use `<script setup lang="ts">` syntax in Vue components

## 4. API Design
- `POST /start_task/{tool_name}` — Initiates a tool, returns `{ call_id }`
- `GET /stream/{call_id}` — SSE endpoint for progress streaming
- CORS must be enabled for local development

## 5. Testing & Verification
- Use `verify_stream.py` for manual SSE testing
- Frontend composables should be testable in isolation
