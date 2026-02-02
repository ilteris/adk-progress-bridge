# Specification: ADK Progress Bridge v2.10.5

## Overview
The ADK Progress Bridge is a high-performance middleware designed to connect background tools/tasks with a real-time terminal user interface (TUI). It provides a standardized protocol for reporting progress, logs, and results via Server-Sent Events (SSE) and WebSockets.

## 1. Architectural Components

### 1.1 Backend (FastAPI)
- **Tool Registry**: Manages registered tools and their metadata.
- **Task Manager**: Orchestrates task execution, input management, and lifecycle.
- **WebSocket Manager**: Handles bi-directional communication, heartbeats, and correlation.
- **Health Engine**: Provides deep system metrics and audit data.
- **Structured Logging**: JSON-based logging with context tracking (call_id, tool_name).

### 1.2 Frontend (Vue 3 / Pinia)
- **WebSocket Manager**: Manages connection lifecycle with exponential backoff.
- **useAgentStream**: Composable for managing task state and streaming updates.
- **Material 3 UI**: Clean, responsive interface for monitoring tasks.

## 2. Protocol Specification

### 2.1 WebSocket Messages

#### Client to Server
- `ping`: Keep-alive heartbeat.
- `list_tools`: Request available tools.
- `list_active_tasks`: Request currently running tasks.
- `get_health`: Request system health and audit data.
- `start`: Initialize a new tool execution.
- `stop`: Terminate a running task.
- `subscribe`: Connect to an existing task stream.
- `input`: Provide input for a waiting task.

#### Server to Client
- `connected`: Handshake acknowledgement.
- `pong`: Heartbeat response.
- `tools_list`: List of available tools.
- `active_tasks_list`: List of active tasks.
- `health_data`: System metrics and audit findings.
- `task_started`: Confirmation of task initiation.
- `progress`: Incremental update (step, pct, log).
- `input_request`: Request for user input.
- `result`: Final task outcome.
- `error`: Failure notification.
- `system_metrics`: Real-time performance data.

## 3. Security & Stability

### 3.1 Authentication
- API Key based authentication for both REST and WebSocket endpoints.
- WebSocket handshake verification via query parameters.

### 3.2 Robustness
- **Thread-Safe Writes**: Mutex-protected WebSocket message sending.
- **Error Correlation**: `request_id` tracking across asynchronous boundaries.
- **Reconnection**: Frontend automatically reconnects with backoff.
- **Input Validation**: Strict Pydantic models for API requests.

## 4. Auditing & Monitoring

### 4.1 Audit Tools
- `resource_monitor`: CPU, Memory, Threads, FDs.
- `deep_health_check`: Comprehensive system snapshot.
- `network_status_check`: Latency and DNS resolution.
- `system_config_audit`: Environment and runtime config.
- `connectivity_benchmark`: Latency sampling and quality scoring.
- `concurrency_stress_test`: Event loop latency under load.
- `garbage_collection_audit`: Memory management stats.
- `asyncio_task_audit`: Active task tracking.
- `disk_io_audit`: I/O throughput monitoring.
- `context_switch_audit`: Scheduler efficiency.
- `memory_leak_audit`: RSS growth tracking.
- `network_connections_audit`: Socket lifecycle monitoring.
- `open_files_audit`: File handle tracking.
- `cpu_usage_audit`: Per-core utilization.
- `load_average_audit`: System load tracking.
- `process_uptime_audit`: Reliability monitoring.
- `virtual_memory_audit`: System memory stats.
- `disk_usage_audit`: Storage monitoring.
- `swap_memory_audit`: Page file usage.
- `process_priority_audit`: Nice value and scheduling.
- `process_memory_full_audit`: USS/PSS monitoring.
- `process_io_counters_audit`: Process-level I/O.
- `process_environ_audit`: Environment variable tracking.
- `process_cmdline_audit`: Command line argument tracking.
- `process_memory_maps_audit`: Memory mapping tracking.
- `process_cpu_times_audit`: Process-level CPU timing.
- `process_cpu_affinity_audit`: Process-level CPU affinity.
- `process_num_fds_audit`: Process-level file descriptor count.
- `process_page_faults_audit`: Process-level page fault tracking.
- `process_memory_percent_audit`: Process-level memory percentage tracking.
- `process_num_threads_audit`: Process-level thread count tracking.
- `process_status_audit`: Process-level status tracking.
- `process_create_time_audit`: Process-level creation time tracking.
- `process_cwd_audit`: Process-level working directory tracking.
- `process_parent_audit`: Process-level parent tracking.
- `process_username_audit`: Process-level username tracking.
- `process_nice_audit`: Process-level priority (nice) tracking. 
- `process_open_files_audit`: Process-level open files tracking. 
- `process_connections_audit`: Process-level network connections tracking.
- `process_memory_full_info_audit`: Process-level full memory tracking. 
- `process_threads_audit`: Process-level thread detail tracking. 
- `process_exe_audit`: Process-level executable path tracking.
- `process_terminal_audit`: Process-level terminal tracking.
- `process_ionice_extended_audit`: Process-level ionice priority tracking.
- `process_rlimit_audit`: Process-level resource limit tracking.
- `process_cpu_num_audit`: Process-level CPU core tracking.
- `system_net_io_counters_audit`: System-wide network I/O tracking.
- `system_users_audit`: System-wide logged-in user tracking.
- `system_disk_partitions_audit`: System-wide disk partition tracking.
- `system_net_if_addrs_audit`: System-wide network interface addresses tracking.
- `system_net_if_stats_audit`: System-wide network interface statistics tracking.
- `system_sensors_temperatures_audit`: System-wide thermal sensor tracking.
- `system_sensors_fans_audit`: System-wide fan speed tracking.
- `system_sensors_battery_audit`: System-wide battery status tracking.
- `system_boot_time_audit`: System boot time tracking.
- `system_cpu_freq_audit`: System CPU frequency tracking.
- `system_cpu_stats_audit`: System CPU stats tracking.
- `system_cpu_count_audit`: System CPU count tracking.
- `system_cpu_times_percent_audit`: System CPU times percentage tracking.
- `system_net_connections_audit`: System network connections tracking.
- `system_pids_audit`: System PIDs tracking.
- `system_cpu_times_audit`: System CPU times tracking.
- `system_disk_io_counters_audit`: System disk I/O counters tracking.
- `system_virtual_memory_audit`: System virtual memory tracking.
- `system_swap_memory_audit`: System swap memory tracking.
- `system_disk_usage_audit`: System disk usage tracking.
- `system_net_io_per_nic_audit`: System network I/O per NIC tracking.
- `system_disk_io_per_disk_audit`: System disk I/O per disk tracking.
- `system_cpu_times_per_cpu_audit`: System CPU times per CPU tracking.
- `system_cpu_times_percent_per_cpu_audit`: System CPU times percentage per CPU tracking.
- `system_net_if_stats_extended_audit`: Extended system network interface stats tracking.
- `system_disk_partitions_usage_audit`: System disk partition usage tracking.
- `system_cpu_freq_per_cpu_audit`: System CPU frequency per CPU tracking.
- `system_disk_partitions_all_audit`: All system disk partitions tracking.
- `system_net_if_addrs_detailed_audit`: Detailed system network interface addresses tracking.
- `system_net_if_addrs_v4_audit`: IPv4 network interface addresses tracking.
- `system_net_if_addrs_v6_audit`: IPv6 network interface addresses tracking.
- `system_disk_partitions_physical_audit`: Physical disk partitions tracking.
- `system_net_if_addrs_mac_audit`: MAC addresses for network interfaces tracking.
- `system_disk_partitions_fstype_audit`: File system types for disk partitions tracking.
- `system_cpu_times_percent_system_focused_audit`: System-focused CPU times percentage tracking.
- `system_net_if_addrs_netmask_audit`: Netmasks for network interfaces tracking.
- `system_disk_partitions_mountpoint_audit`: Mount points for disk partitions tracking.
- `system_cpu_times_percent_user_focused_audit`: User-focused CPU times percentage tracking.
- `system_net_if_addrs_broadcast_audit`: Broadcast addresses for network interfaces tracking.
- `system_disk_partitions_device_audit`: Devices for disk partitions tracking.
- `system_cpu_times_percent_idle_focused_audit`: Idle-focused CPU times percentage tracking.
- `system_net_if_addrs_ptp_audit`: PTP addresses for network interfaces tracking.
- `system_disk_partitions_opts_audit`: Options for disk partitions tracking.
- `system_cpu_times_percent_iowait_focused_audit`: I/O wait focused CPU times percentage tracking.
- `system_cpu_times_percent_irq_focused_audit`: IRQ focused CPU times percentage tracking.
- `system_cpu_times_percent_softirq_focused_audit`: Soft IRQ focused CPU times percentage tracking.
- `system_net_io_errors_audit`: System network I/O error tracking.
- `system_cpu_times_percent_steal_focused_audit`: Steal focused CPU times percentage tracking.
- `system_cpu_times_percent_guest_focused_audit`: Guest focused CPU times percentage tracking.
- `system_disk_partitions_limits_audit`: Disk partition limits tracking.
- `system_cpu_times_percent_guest_nice_focused_audit`: Guest nice focused CPU times percentage tracking.
- `system_net_io_packets_audit`: System network I/O packet tracking.
- `system_disk_io_time_audit`: System disk I/O time tracking.
- `system_net_io_errout_audit`: System network I/O outgoing error tracking.
- `system_net_io_packets_sent_audit`: System-wide network packet sent tracking.
- `system_net_io_packets_recv_audit`: System-wide network packet received tracking.
- `system_disk_io_read_bytes_audit`: System-wide disk read byte tracking.
- `system_disk_io_write_bytes_audit`: System-wide disk write byte tracking.
- `system_net_io_sent_bytes_audit`: System-wide network sent byte tracking.
- `system_net_io_recv_bytes_audit`: System-wide network received byte tracking.
- `system_disk_io_read_count_audit`: System-wide disk read count tracking.
- `system_disk_io_write_count_audit`: System-wide disk write count tracking.
- `system_disk_io_read_time_audit`: System-wide disk read time tracking.
- `system_disk_io_write_time_audit`: System-wide disk write time tracking.
- `system_disk_io_busy_time_audit`: System-wide disk busy time tracking.
- `system_cpu_stats_ctx_switches_focused_audit`: System-wide context switch focused tracking.
- `system_cpu_stats_interrupts_focused_audit`: System-wide interrupt focused tracking.
- `system_cpu_stats_soft_interrupts_focused_audit`: System-wide soft interrupt focused tracking.
- `system_swap_memory_sin_total_audit`: System-wide swap-in total tracking.
- `system_swap_memory_sout_total_audit`: System-wide swap-out total tracking.
- `system_net_io_dropout_total_audit`: System-wide network dropout total tracking.
- `system_net_io_dropin_total_audit`: System-wide network dropin total tracking.
- `system_net_io_errout_total_audit`: System-wide network errout total tracking.
- `system_net_io_errin_total_audit`: System-wide network errin total tracking.
- `system_net_io_packets_sent_total_audit`: System-wide network packets sent total tracking.
- `system_net_io_packets_recv_total_audit`: System-wide network packets received total tracking.
- `system_disk_io_read_count_total_audit`: System-wide disk read count total tracking.
- `system_net_io_errors_total_audit`: System-wide network errors total tracking.
- `system_net_io_drop_total_audit`: System-wide network drop total tracking.
- `system_disk_io_write_count_total_audit`: System-wide disk write count total tracking.
- `system_disk_io_read_bytes_total_audit`: System-wide disk read bytes total tracking.
- `system_disk_io_write_bytes_total_audit`: System-wide disk write bytes total tracking.
- `system_disk_io_read_time_total_audit`: System-wide disk read time total tracking.
- `system_disk_io_write_time_total_audit`: System-wide disk write time total tracking.
- `system_disk_io_busy_time_total_audit`: System-wide disk busy time total tracking.
- `system_cpu_stats_ctx_switches_total_audit`: System-wide context switches total tracking.
- `system_cpu_stats_interrupts_total_audit`: System-wide interrupts total tracking.
- `system_cpu_stats_soft_interrupts_total_audit`: System-wide soft interrupts total tracking.
- `system_cpu_stats_syscalls_total_audit`: System-wide syscalls total tracking.
- `system_cpu_times_user_total_audit`: System-wide user cpu times total tracking.
- `system_cpu_times_system_total_audit`: System-wide system cpu times total tracking.
- `system_cpu_times_idle_total_audit`: System-wide idle cpu times total tracking.
- `system_cpu_times_nice_total_audit`: System-wide nice cpu times total tracking.
- `system_cpu_times_iowait_total_audit`: System-wide iowait cpu times total tracking.
- `system_cpu_times_irq_total_audit`: System-wide irq cpu times total tracking.
- `system_memory_buffers_audit`: System-wide memory buffers tracking.
- `system_memory_cached_audit`: System-wide memory cached tracking.
- `system_memory_percent_avg_audit`: System-wide average memory usage percentage tracking.
- `system_memory_available_avg_audit`: System-wide average available memory tracking.
- `system_memory_used_avg_audit`: System-wide average used memory tracking.
- `system_memory_free_avg_audit`: System-wide average free memory tracking.

## 5. Metadata
- **APP_VERSION**: 2.10.5
- **BUILD_TIMESTAMP**: 2026-02-02T01:15:00Z
- **GIT_COMMIT**: v725-supreme-apex-adele-verification
- **OPERATIONAL_APEX**: v725 SUPREME APEX VERIFICATION ADELE- `system_pids_count_ultimate_audit`: System-wide PID count tracking.
- `system_boot_time_ultimate_audit`: System boot time tracking.
- `system_users_count_ultimate_audit`: System-wide logged-in users count tracking.
