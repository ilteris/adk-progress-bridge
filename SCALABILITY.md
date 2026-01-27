# Scalability Strategy

This document outlines the approach for scaling the ADK Progress Bridge to multiple server instances.

## Current Architecture & Limitations

The current implementation of the `ToolRegistry` stores `AsyncGenerator` objects in an in-memory dictionary (`self._active_tasks`). 

### The Problem: Process-Bound State
`AsyncGenerator` objects are bound to the memory space of the process that created them. If a client initializes a task via `/start_task` on **Instance A**, but the subsequent `/stream/{call_id}` request is routed to **Instance B**, Instance B will have no knowledge of that `call_id` or its generator.

## Recommended Strategies

### 1. Sticky Sessions (Session Affinity)
The simplest way to scale the current architecture is to use a Load Balancer (e.g., Nginx, HAProxy, GCLB) with **Sticky Sessions** enabled.

- **Mechanism**: The Load Balancer uses a cookie or client IP to ensure that all requests from a specific client are routed to the same server instance for a defined period.
- **Pros**: 
    - No code changes required.
    - Maintains the simplicity of the `AsyncGenerator` pattern.
- **Cons**: 
    - Uneven load distribution if some tasks are significantly heavier than others.
    - If an instance goes down, all active tasks on that instance are lost.

### 2. Distributed Task Execution (Stateless API)
For a truly stateless API tier that can scale horizontally without affinity, the execution logic must be decoupled from the API process.

#### Proposed Distributed Architecture:
1.  **Task Queue**: Use Redis or RabbitMQ as a message broker.
2.  **Worker Tier**: Move the tool execution logic into background workers (e.g., Celery, Python-RQ, or custom Ray actors).
3.  **State Store**: Use Redis to store task metadata and progress history.
4.  **Pub/Sub for Real-time Updates**:
    - The **Worker** executes the tool and publishes progress updates to a Redis channel named after the `call_id`.
    - The **API Instance** (any instance) receives the `/stream/{call_id}` request, subscribes to the Redis channel, and yields messages as SSE events.

#### Redis-based ToolRegistry Schema:
Instead of storing generators, the `ToolRegistry` would manage task state in Redis:
- `task:{call_id}:metadata` (Hash): `{"tool_name": "...", "status": "running", "created_at": "..."}`
- `task:{call_id}:progress` (List or Stream): A buffer of progress updates for clients that connect late.
- `task:{call_id}:channel` (PubSub): For real-time streaming.

## Implementation Roadmap for Redis Support

To transition to a Redis-backed registry:

1.  **Abstract Registry**: Create a `BaseRegistry` interface and implement `InMemoryRegistry` and `RedisRegistry`.
2.  **Tool Adapters**: Modify `@progress_tool` to support serializing tool arguments and pushing to a queue.
3.  **Event Bridge**: Implement a listener in the API that bridges Redis PubSub messages to the SSE `StreamingResponse`.
4.  **Cleanup**: Use Redis EXPIRE keys for automatic cleanup of stale task metadata instead of a manual background loop.

## Metrics & Monitoring in Multi-Instance
When scaling, Prometheus metrics must be aggregated.
- Use the `prometheus_multiproc_dir` for Gunicorn-based deployments.
- For Kubernetes, use a **Prometheus ServiceMonitor** to scrape all pods and aggregate via PromQL (e.g., `sum(active_tasks) by (tool_name)`).
