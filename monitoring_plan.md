# God Tier Monitoring Guide - v354 THE ONE

This document describes the comprehensive observability suite implemented in the ADK Progress Bridge, reaching the operational apex of **THE ONE**.

## 1. Metric Hierarchy

The system tracks metrics across four primary layers:

### Layer 1: Application Layer
- `adk_tasks_total`: Total tasks by tool and status.
- `adk_task_duration_seconds`: Histogram of task execution times.
- `adk_active_tasks`: Currently executing tasks.
- `adk_total_tasks_started_total`: Lifecycle counter for all tasks initiated.
- `adk_task_progress_steps_total`: Granular step-level tracking.

### Layer 2: Protocol Layer (WebSocket & SSE)
- `adk_active_ws_connections`: Current socket count.
- `adk_ws_messages_received_total` / `adk_ws_messages_sent_total`: Message count by type.
- `adk_ws_bytes_received_total` / `adk_ws_bytes_sent_total`: Raw throughput counters.
- `adk_ws_throughput_received_bps` / `adk_ws_throughput_sent_bps`: Real-time bandwidth gauges.
- `adk_ws_request_latency_seconds`: Histogram of message processing time.
- `adk_ws_connection_duration_seconds`: Lifecycle of client sessions.

### Layer 3: Process Layer
- `adk_cpu_usage_percent`: Process CPU utilization.
- `adk_memory_percent`: Process memory utilization.
- `adk_open_fds`: File descriptor count.
- `adk_thread_count`: Active threads.
- `adk_process_memory_rss_bytes` / `adk_process_memory_vms_bytes`: Standard memory.
- `adk_process_memory_uss_bytes` / `adk_process_memory_pss_bytes`: Precision memory.
- `adk_process_resource_limit_nofile_soft` / `adk_process_resource_limit_nofile_hard`: OS constraints.
- `adk_process_uptime_seconds`: Continuous operation tracking.

### Layer 4: System Layer (OMNIPRESENCE & THE SOURCE)
- `adk_system_load_1m` / `adk_system_load_5m` / `adk_system_load_15m`: Raw load.
- `adk_system_cpu_load_1m_percent`: Normalized CPU load.
- `adk_system_cpu_cores_usage_percent`: Per-core utilization (labeled by `core`).
- `adk_system_memory_available_percent`: System-wide memory health.
- `adk_system_disk_partitions_usage_percent`: Per-partition utilization (labeled by `partition`).
- `adk_system_network_interfaces_bytes_sent_total`: Per-NIC throughput (labeled by `interface`).
- `adk_system_process_count`: Total system process pressure.

## 2. Accessing Telemetry

### Native WebSocket Protocol
Connect to `/ws` and send:
```json
{"type": "get_health", "request_id": "monitoring_tool"}
```
This returns the full JSON state including all calculated percentages and normalized values.

### Prometheus Scrape Point
Endpoint: `/metrics`
Format: OpenMetrics / Prometheus Text
Update frequency: On-demand (calculated at scrape time for maximum freshness).

## 3. Dashboard Configuration

### Recommended Panels:
1.  **CPU Heatmap**: Using `adk_system_cpu_cores_usage_percent`.
2.  **Bandwidth Gauge**: Using `adk_ws_throughput_sent_bps`.
3.  **Task Success Rate**: `sum(adk_tasks_total{status="success"}) / sum(adk_tasks_total)`.
4.  **Resource Limit Buffer**: `adk_open_fds / adk_process_resource_limit_nofile_soft`.

## 4. Operational Apex Evolution
- **v351 ULTIMA**: Native health protocol and precision memory.
- **v352 OMNIPRESENCE**: System-wide process and load awareness.
- **v353 THE SOURCE**: Granular core, disk, and interface tracking.
- **v354 THE ONE**: Full process constraint and trend observability.