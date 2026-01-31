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

PEAK_ACTIVE_TASKS = Gauge(
    "adk_peak_active_tasks",
    "Peak number of tasks in the registry since start"
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

PEAK_ACTIVE_WS_CONNECTIONS = Gauge(
    "adk_peak_active_ws_connections",
    "Peak number of active WebSocket connections since start"
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

WS_BYTES_RECEIVED_TOTAL = Counter(
    "adk_ws_bytes_received_total",
    "Total number of bytes received via WebSocket"
)

WS_BYTES_SENT_TOTAL = Counter(
    "adk_ws_bytes_sent_total",
    "Total number of bytes sent via WebSocket"
)

WS_THROUGHPUT_RECEIVED_BPS = Gauge(
    "adk_ws_throughput_received_bps",
    "Current WebSocket received throughput in bytes per second"
)

WS_THROUGHPUT_SENT_BPS = Gauge(
    "adk_ws_throughput_sent_bps",
    "Current WebSocket sent throughput in bytes per second"
)

WS_REQUEST_LATENCY = Histogram(
    "adk_ws_request_latency_seconds",
    "Latency of WebSocket request processing",
    ["message_type"]
)

WS_CONNECTION_DURATION = Histogram(
    "adk_ws_connection_duration_seconds",
    "Duration of WebSocket connections"
)

MEMORY_PERCENT = Gauge(
    "adk_memory_percent",
    "Memory usage percentage of the process"
)

CPU_USAGE_PERCENT = Gauge(
    "adk_cpu_usage_percent",
    "CPU usage percentage of the process"
)

OPEN_FDS = Gauge(
    "adk_open_fds",
    "Number of open file descriptors for the process"
)

THREAD_COUNT = Gauge(
    "adk_thread_count",
    "Number of active threads in the process"
)

CONTEXT_SWITCHES_VOLUNTARY = Gauge(
    "adk_context_switches_voluntary",
    "Number of voluntary context switches"
)

CONTEXT_SWITCHES_INVOLUNTARY = Gauge(
    "adk_context_switches_involuntary",
    "Number of involuntary context switches"
)

TOTAL_TASKS_STARTED = Counter(
    "adk_total_tasks_started_total",
    "Total number of tasks started since application launch"
)

BUILD_INFO = Info("adk_build", "Application build information")

def get_metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)