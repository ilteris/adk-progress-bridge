# Monitoring & Metrics Implementation Plan

## 1. Metrics Enhancement
- Add `STALE_TASKS_CLEANED_TOTAL` Counter to `backend/app/metrics.py`.
- Add `TASK_PROGRESS_STEPS_TOTAL` Counter
- Add `ACTIVE_WS_CONNECTIONS` Gauge to `backend/app/metrics.py`. (labeled by `tool_name`) to `backend/app/metrics.py`.

## 2. Integration
- Update `backend/app/bridge.py`:
    - Increment `STALE_TASKS_CLEANED_TOTAL` in `cleanup_stale_tasks`.
- Update `backend/app/main.py`:
    - Increment `TASK_PROGRESS_STEPS_TOTAL` in `event_generator` and `run_ws_generator`.
- Increment/Decrement `ACTIVE_WS_CONNECTIONS` in `websocket_endpoint`. in `event_generator` loop when `ProgressPayload` is yielded.

## 3. Infrastructure
- Create `prometheus.yml` to scrape the FastAPI `/metrics` endpoint.
- Create `docker-compose.yml` to launch Prometheus and Grafana.

## 4. Verification
- Create `tests/test_metrics.py` to verify that:
    - `/metrics` endpoint returns valid Prometheus data.
    - `adk_tasks_total` increments on task completion.
    - `adk_active_tasks` accurately reflects the registry state.
    - `adk_task_progress_steps_total` increments during streaming.
