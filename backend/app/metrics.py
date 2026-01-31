from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

# Metrics definitions
TASK_DURATION = Histogram(
    "adk_task_duration_seconds",
    "Time spent executing the task",
    ["tool_name"]
)

TASKS_TOTAL = Counter(
    "adk_tasks_total",
    "Total number of tasks executed",
    ["tool_name", "status"]
)

ACTIVE_TASKS = Gauge(
    "adk_active_tasks",
    "Number of tasks currently in the registry",
    ["tool_name"]
)

STALE_TASKS_CLEANED_TOTAL = Counter(
    "adk_stale_tasks_cleaned_total",
    "Total number of stale tasks cleaned up from the registry"
)

TASK_PROGRESS_STEPS_TOTAL = Counter(
    "adk_task_progress_steps_total",
    "Total number of progress steps yielded by tasks",
    ["tool_name"]
)

ACTIVE_WS_CONNECTIONS = Gauge(
    "adk_active_ws_connections",
    "Number of active WebSocket connections"
)

WS_MESSAGES_RECEIVED_TOTAL = Counter(
    "adk_ws_messages_received_total",
    "Total number of messages received via WebSocket",
    ["message_type"]
)

WS_MESSAGES_SENT_TOTAL = Counter(
    "adk_ws_messages_sent_total",
    "Total number of messages sent via WebSocket",
    ["message_type"]
)

BUILD_INFO = Info("adk_build", "Application build information")

def get_metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
