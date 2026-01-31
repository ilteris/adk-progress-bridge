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

DISK_USAGE_PERCENT = Gauge(
    "adk_disk_usage_percent",
    "Disk usage percentage of the root filesystem"
)

SYSTEM_MEMORY_AVAILABLE = Gauge(
    "adk_system_memory_available_bytes",
    "Available system memory in bytes"
)

PAGE_FAULTS_MINOR = Gauge(
    "adk_page_faults_minor",
    "Number of minor page faults"
)

PAGE_FAULTS_MAJOR = Gauge(
    "adk_page_faults_major",
    "Number of major page faults"
)

# v335 Supreme Metrics
SYSTEM_CPU_COUNT = Gauge(
    "adk_system_cpu_count",
    "Total number of CPUs in the system"
)

SYSTEM_BOOT_TIME = Gauge(
    "adk_system_boot_time_seconds",
    "System boot time in seconds since epoch"
)

SWAP_MEMORY_USAGE_PERCENT = Gauge(
    "adk_swap_memory_usage_percent",
    "System swap memory usage percentage"
)

SYSTEM_NETWORK_BYTES_SENT = Gauge(
    "adk_system_network_bytes_sent",
    "Total system bytes sent over the network"
)

SYSTEM_NETWORK_BYTES_RECV = Gauge(
    "adk_system_network_bytes_recv",
    "Total system bytes received over the network"
)

# v336 Supreme Apex Ultra Millennium Metrics
SYSTEM_CPU_FREQUENCY = Gauge(
    "adk_system_cpu_frequency_current_mhz",
    "Current CPU frequency in MHz"
)

SYSTEM_DISK_READ_BYTES = Gauge(
    "adk_system_disk_read_bytes_total",
    "Total bytes read from disk"
)

SYSTEM_DISK_WRITE_BYTES = Gauge(
    "adk_system_disk_write_bytes_total",
    "Total bytes written to disk"
)

PROCESS_CONNECTIONS_COUNT = Gauge(
    "adk_process_connections_count",
    "Number of network connections for the current process"
)

SYSTEM_LOAD_1M = Gauge(
    "adk_system_load_1m",
    "System load average over the last 1 minute"
)

TOTAL_TASKS_STARTED = Counter(
    "adk_total_tasks_started_total",
    "Total number of tasks started since application launch"
)

# v337 Supreme Apex Ultra Millennium Omega Metrics
SYSTEM_LOAD_5M = Gauge(
    "adk_system_load_5m",
    "System load average over the last 5 minutes"
)

SYSTEM_LOAD_15M = Gauge(
    "adk_system_load_15m",
    "System load average over the last 15 minutes"
)

PROCESS_MEMORY_RSS = Gauge(
    "adk_process_memory_rss_bytes",
    "Resident Set Size memory usage in bytes"
)

PROCESS_MEMORY_VMS = Gauge(
    "adk_process_memory_vms_bytes",
    "Virtual Memory Size usage in bytes"
)

SYSTEM_MEMORY_TOTAL = Gauge(
    "adk_system_memory_total_bytes",
    "Total system memory in bytes"
)

SYSTEM_CPU_USAGE_USER = Gauge(
    "adk_system_cpu_usage_user_percent",
    "System-wide CPU usage percentage in user mode"
)

SYSTEM_CPU_USAGE_SYSTEM = Gauge(
    "adk_system_cpu_usage_system_percent",
    "System-wide CPU usage percentage in system mode"
)

SYSTEM_UPTIME = Gauge(
    "adk_system_uptime_seconds",
    "System uptime in seconds"
)

# v338 Supreme Apex Ultra Millennium Omega Plus Metrics
SYSTEM_CPU_USAGE_IDLE = Gauge(
    "adk_system_cpu_usage_idle_percent",
    "System-wide CPU usage percentage in idle mode"
)

PROCESS_CPU_USAGE_USER = Gauge(
    "adk_process_cpu_usage_user_seconds",
    "Total user CPU time spent by the process in seconds"
)

PROCESS_CPU_USAGE_SYSTEM = Gauge(
    "adk_process_cpu_usage_system_seconds",
    "Total system CPU time spent by the process in seconds"
)

SYSTEM_MEMORY_USED = Gauge(
    "adk_system_memory_used_bytes",
    "Used system memory in bytes"
)

SYSTEM_MEMORY_FREE = Gauge(
    "adk_system_memory_free_bytes",
    "Free system memory in bytes"
)

SYSTEM_NETWORK_PACKETS_SENT = Gauge(
    "adk_system_network_packets_sent_total",
    "Total system packets sent over the network"
)

SYSTEM_NETWORK_PACKETS_RECV = Gauge(
    "adk_system_network_packets_recv_total",
    "Total system packets received over the network"
)

# v339 Supreme Apex Ultra Millennium Omega Plus Ultra Metrics
SYSTEM_SWAP_USED_BYTES = Gauge(
    "adk_system_swap_used_bytes",
    "Total used system swap memory in bytes"
)

SYSTEM_SWAP_FREE_BYTES = Gauge(
    "adk_system_swap_free_bytes",
    "Total free system swap memory in bytes"
)

PROCESS_IO_READ_BYTES = Gauge(
    "adk_process_io_read_bytes_total",
    "Total bytes read by the process"
)

PROCESS_IO_WRITE_BYTES = Gauge(
    "adk_process_io_write_bytes_total",
    "Total bytes written by the process"
)

PROCESS_IO_READ_COUNT = Gauge(
    "adk_process_io_read_count_total",
    "Total number of read operations by the process"
)

PROCESS_IO_WRITE_COUNT = Gauge(
    "adk_process_io_write_count_total",
    "Total number of write operations by the process"
)

# v340 Supreme Apex Ultra Millennium Omega Plus Ultra Ultimate Metrics
PROCESS_CPU_PERCENT_TOTAL = Gauge(
    "adk_process_cpu_percent_total",
    "Current process CPU usage percentage"
)

SYSTEM_NETWORK_ERRORS_IN = Gauge(
    "adk_system_network_errors_in_total",
    "Total system network receive errors"
)

SYSTEM_NETWORK_ERRORS_OUT = Gauge(
    "adk_system_network_errors_out_total",
    "Total system network transmit errors"
)

SYSTEM_NETWORK_DROPS_IN = Gauge(
    "adk_system_network_drops_in_total",
    "Total system network receive drops"
)

SYSTEM_NETWORK_DROPS_OUT = Gauge(
    "adk_system_network_drops_out_total",
    "Total system network transmit drops"
)

SYSTEM_MEMORY_ACTIVE_BYTES = Gauge(
    "adk_system_memory_active_bytes",
    "System-wide active memory in bytes"
)

SYSTEM_MEMORY_INACTIVE_BYTES = Gauge(
    "adk_system_memory_inactive_bytes",
    "System-wide inactive memory in bytes"
)

# v341 God Tier Omega Plus Ultra Metrics
SYSTEM_CPU_INTERRUPTS = Gauge(
    "adk_system_cpu_interrupts_total",
    "Total number of interrupts since boot"
)

SYSTEM_CPU_SOFT_INTERRUPTS = Gauge(
    "adk_system_cpu_soft_interrupts_total",
    "Total number of soft interrupts since boot"
)

SYSTEM_CPU_SYSCALLS = Gauge(
    "adk_system_cpu_syscalls_total",
    "Total number of system calls since boot"
)

PROCESS_MEMORY_SHARED_BYTES = Gauge(
    "adk_process_memory_shared_bytes",
    "Shared memory usage of the process in bytes"
)

# v341 additional
PROCESS_MEMORY_TEXT_BYTES = Gauge(
    "adk_process_memory_text_bytes",
    "Text segment memory usage of the process in bytes"
)

PROCESS_MEMORY_DATA_BYTES = Gauge(
    "adk_process_memory_data_bytes",
    "Data segment memory usage of the process in bytes"
)

PROCESS_NUM_THREADS = Gauge(
    "adk_process_num_threads",
    "Number of threads used by the process"
)

# v342 Ascension Singularity Metrics
SYSTEM_CPU_STEAL = Gauge(
    "adk_system_cpu_steal_percent",
    "Time spent in other operating systems when running in a virtualized environment"
)

SYSTEM_CPU_GUEST = Gauge(
    "adk_system_cpu_guest_percent",
    "Time spent running a virtual CPU for guest operating systems"
)

SYSTEM_MEMORY_BUFFERS = Gauge(
    "adk_system_memory_buffers_bytes",
    "System memory used for temporary storage of raw disk blocks"
)

SYSTEM_MEMORY_CACHED = Gauge(
    "adk_system_memory_cached_bytes",
    "System memory used for temporary storage of files read from disk"
)

SYSTEM_DISK_PARTITIONS_COUNT = Gauge(
    "adk_system_disk_partitions_count",
    "Total number of mounted disk partitions"
)

SYSTEM_USERS_COUNT = Gauge(
    "adk_system_users_count",
    "Number of active system users"
)

PROCESS_CHILDREN_COUNT = Gauge(
    "adk_process_children_count",
    "Number of child processes"
)

# v343 Beyond Singularity Metrics
SYSTEM_CPU_IOWAIT = Gauge(
    "adk_system_cpu_iowait_percent",
    "Time spent waiting for I/O to complete"
)

SYSTEM_CPU_IRQ = Gauge(
    "adk_system_cpu_irq_percent",
    "Time spent servicing hardware interrupts"
)

SYSTEM_CPU_SOFTIRQ = Gauge(
    "adk_system_cpu_softirq_percent",
    "Time spent servicing software interrupts"
)

SYSTEM_MEMORY_SLAB = Gauge(
    "adk_system_memory_slab_bytes",
    "In-kernel data structures cache"
)

PROCESS_MEMORY_LIB = Gauge(
    "adk_process_memory_lib_bytes",
    "Memory used by shared libraries"
)

PROCESS_MEMORY_DIRTY = Gauge(
    "adk_process_memory_dirty_bytes",
    "Memory that has been modified and must be written to disk"
)

PROCESS_ENV_VAR_COUNT = Gauge(
    "adk_process_env_var_count",
    "Number of environment variables for the process"
)

# v344 Transcendence Metrics
PROCESS_MEMORY_USS = Gauge(
    "adk_process_memory_uss_bytes",
    "Unique Set Size memory usage of the process in bytes"
)

SYSTEM_MEMORY_WIRED = Gauge(
    "adk_system_memory_wired_bytes",
    "System memory that can never be paged out to disk (macOS)"
)

PROCESS_NICE = Gauge(
    "adk_process_nice_value",
    "The priority (niceness) of the process"
)

PROCESS_UPTIME = Gauge(
    "adk_process_uptime_seconds",
    "Uptime of the process in seconds"
)

# v345 Omnipotence Metrics
SYSTEM_CPU_CTX_SWITCHES = Gauge(
    "adk_system_cpu_context_switches_total",
    "Total number of system-wide context switches since boot"
)

SYSTEM_NETWORK_CONNECTIONS = Gauge(
    "adk_system_network_connections_count",
    "Total number of active network connections in the system"
)

PROCESS_CPU_AFFINITY = Gauge(
    "adk_process_cpu_affinity_count",
    "Number of CPUs the process is allowed to run on"
)

PROCESS_MEMORY_PAGE_FAULTS_TOTAL = Gauge(
    "adk_process_memory_page_faults_total",
    "Total number of page faults (minor + major) for the process"
)

# v346 Deification Metrics
SYSTEM_DISK_READ_COUNT_TOTAL = Gauge(
    "adk_system_disk_read_count_total",
    "Total number of system-wide disk read operations"
)

SYSTEM_DISK_WRITE_COUNT_TOTAL = Gauge(
    "adk_system_disk_write_count_total",
    "Total number of system-wide disk write operations"
)

SYSTEM_SWAP_IN_BYTES_TOTAL = Gauge(
    "adk_system_swap_in_bytes_total",
    "Total number of bytes swapped in from disk"
)

SYSTEM_SWAP_OUT_BYTES_TOTAL = Gauge(
    "adk_system_swap_out_bytes_total",
    "Total number of bytes swapped out to disk"
)

PROCESS_MEMORY_VMS_PERCENT = Gauge(
    "adk_process_memory_vms_percent",
    "Virtual memory size as a percentage of total system memory"
)

SYSTEM_CPU_PHYSICAL_COUNT = Gauge(
    "adk_system_cpu_physical_count",
    "Total number of physical CPUs in the system"
)

# v347 Singularity Ascension Metrics
SYSTEM_MEMORY_PERCENT = Gauge(
    "adk_system_memory_percent",
    "Total system memory usage percentage"
)

PROCESS_OPEN_FILES_COUNT = Gauge(
    "adk_process_open_files_count",
    "Total number of open files by the process"
)

SYSTEM_DISK_BUSY_TIME_MS = Gauge(
    "adk_system_disk_busy_time_ms_total",
    "Total time spent doing system-wide disk I/O in milliseconds"
)

SYSTEM_NETWORK_INTERFACES_COUNT = Gauge(
    "adk_system_network_interfaces_count",
    "Total number of network interfaces on the system"
)

PROCESS_THREADS_TOTAL_TIME_USER = Gauge(
    "adk_process_threads_total_time_user_seconds",
    "Total user CPU time across all process threads in seconds"
)

PROCESS_THREADS_TOTAL_TIME_SYSTEM = Gauge(
    "adk_process_threads_total_time_system_seconds",
    "Total system CPU time across all process threads in seconds"
)

# v348 Nirvana Metrics
SYSTEM_DISK_READ_TIME_MS = Gauge(
    "adk_system_disk_read_time_ms_total",
    "Total time spent reading from disk in milliseconds"
)

SYSTEM_DISK_WRITE_TIME_MS = Gauge(
    "adk_system_disk_write_time_ms_total",
    "Total time spent writing to disk in milliseconds"
)

PROCESS_MEMORY_MAPS_COUNT = Gauge(
    "adk_process_memory_maps_count",
    "Number of memory maps for the process"
)

SYSTEM_NETWORK_INTERFACES_UP_COUNT = Gauge(
    "adk_system_network_interfaces_up_count",
    "Number of network interfaces that are currently up"
)

PROCESS_CONTEXT_SWITCHES_TOTAL = Gauge(
    "adk_process_context_switches_total",
    "Total number of context switches (voluntary + involuntary) for the process"
)

# v349 Enlightenment Metrics
PROCESS_CPU_TIMES_CHILDREN_USER = Gauge(
    "adk_process_cpu_times_children_user_seconds",
    "User CPU time spent by child processes in seconds"
)

PROCESS_CPU_TIMES_CHILDREN_SYSTEM = Gauge(
    "adk_process_cpu_times_children_system_seconds",
    "System CPU time spent by child processes in seconds"
)

SYSTEM_NETWORK_INTERFACES_DOWN_COUNT = Gauge(
    "adk_system_network_interfaces_down_count",
    "Number of network interfaces that are currently down"
)

SYSTEM_DISK_READ_MERGED_COUNT = Gauge(
    "adk_system_disk_read_merged_count_total",
    "Total number of system-wide disk read merged operations"
)

SYSTEM_DISK_WRITE_MERGED_COUNT = Gauge(
    "adk_system_disk_write_merged_count_total",
    "Total number of system-wide disk write merged operations"
)

# v350 Apotheosis Metrics
SYSTEM_MEMORY_SHARED_BYTES = Gauge(
    "adk_system_memory_shared_bytes",
    "System memory used by shared memory (shmem)"
)

PROCESS_MEMORY_PSS_BYTES = Gauge(
    "adk_process_memory_pss_bytes",
    "Proportional Set Size memory usage of the process in bytes"
)

SYSTEM_NETWORK_INTERFACES_MTU_TOTAL = Gauge(
    "adk_system_network_interfaces_mtu_total",
    "Total sum of MTU values across all network interfaces"
)

PROCESS_MEMORY_SWAP_BYTES = Gauge(
    "adk_process_memory_swap_bytes",
    "Amount of memory swapped out to disk for the process"
)

SYSTEM_NETWORK_ERRORS_TOTAL = Gauge(
    "adk_system_network_errors_total",
    "Total sum of all network errors (in, out, drops) across all interfaces"
)

# v351 Ultima Metrics
SYSTEM_NETWORK_INTERFACES_SPEED_TOTAL_MBPS = Gauge(
    "adk_system_network_interfaces_speed_total_mbps",
    "Total sum of interface speeds in Mbps across all network interfaces"
)

SYSTEM_NETWORK_INTERFACES_DUPLEX_FULL_COUNT = Gauge(
    "adk_system_network_interfaces_duplex_full_count",
    "Total number of network interfaces in full duplex mode"
)

PROCESS_MEMORY_USS_PERCENT = Gauge(
    "adk_process_memory_uss_percent",
    "Unique Set Size memory usage as a percentage of total system memory"
)

BUILD_INFO = Info("adk_build", "Application build information")

def get_metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)