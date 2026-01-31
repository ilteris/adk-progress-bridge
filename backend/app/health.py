import os
import time
import sys
import threading
import platform
import asyncio
import json
from typing import Dict, Any, List, Optional
from .logger import logger
from .bridge import registry
from .metrics import (
    TASK_DURATION, TASKS_TOTAL, TASK_PROGRESS_STEPS_TOTAL, 
    ACTIVE_WS_CONNECTIONS, WS_MESSAGES_RECEIVED_TOTAL, WS_MESSAGES_SENT_TOTAL,
    PEAK_ACTIVE_TASKS, WS_BYTES_RECEIVED_TOTAL, WS_BYTES_SENT_TOTAL,
    WS_REQUEST_LATENCY, WS_CONNECTION_DURATION, MEMORY_PERCENT, TOTAL_TASKS_STARTED,
    CPU_USAGE_PERCENT, PEAK_ACTIVE_WS_CONNECTIONS, OPEN_FDS, THREAD_COUNT,
    WS_THROUGHPUT_RECEIVED_BPS, WS_THROUGHPUT_SENT_BPS,
    CONTEXT_SWITCHES_VOLUNTARY, CONTEXT_SWITCHES_INVOLUNTARY,
    DISK_USAGE_PERCENT, SYSTEM_MEMORY_AVAILABLE, PAGE_FAULTS_MINOR, PAGE_FAULTS_MAJOR,
    SYSTEM_CPU_COUNT, SYSTEM_BOOT_TIME, SWAP_MEMORY_USAGE_PERCENT,
    SYSTEM_NETWORK_BYTES_SENT, SYSTEM_NETWORK_BYTES_RECV,
    SYSTEM_CPU_FREQUENCY, SYSTEM_DISK_READ_BYTES, SYSTEM_DISK_WRITE_BYTES,
    PROCESS_CONNECTIONS_COUNT, SYSTEM_LOAD_1M,
    SYSTEM_LOAD_5M, SYSTEM_LOAD_15M, PROCESS_MEMORY_RSS, PROCESS_MEMORY_VMS,
    SYSTEM_MEMORY_TOTAL, SYSTEM_CPU_USAGE_USER, SYSTEM_CPU_USAGE_SYSTEM,
    SYSTEM_UPTIME, SYSTEM_CPU_USAGE_IDLE, PROCESS_CPU_USAGE_USER, PROCESS_CPU_USAGE_SYSTEM, 
    SYSTEM_MEMORY_USED, SYSTEM_MEMORY_FREE, SYSTEM_NETWORK_PACKETS_SENT, SYSTEM_NETWORK_PACKETS_RECV,
    SYSTEM_SWAP_USED_BYTES, SYSTEM_SWAP_FREE_BYTES, PROCESS_IO_READ_BYTES, PROCESS_IO_WRITE_BYTES,
    PROCESS_IO_READ_COUNT, PROCESS_IO_WRITE_COUNT,
    PROCESS_CPU_PERCENT_TOTAL, SYSTEM_NETWORK_ERRORS_IN, SYSTEM_NETWORK_ERRORS_OUT,
    SYSTEM_NETWORK_DROPS_IN, SYSTEM_NETWORK_DROPS_OUT,
    SYSTEM_MEMORY_ACTIVE_BYTES, SYSTEM_MEMORY_INACTIVE_BYTES,
    SYSTEM_CPU_INTERRUPTS, SYSTEM_CPU_SOFT_INTERRUPTS, SYSTEM_CPU_SYSCALLS,
    PROCESS_MEMORY_SHARED_BYTES, PROCESS_MEMORY_TEXT_BYTES, PROCESS_MEMORY_DATA_BYTES,
    PROCESS_NUM_THREADS,
    SYSTEM_CPU_STEAL, SYSTEM_CPU_GUEST, SYSTEM_MEMORY_BUFFERS, SYSTEM_MEMORY_CACHED,
    SYSTEM_DISK_PARTITIONS_COUNT, SYSTEM_USERS_COUNT, PROCESS_CHILDREN_COUNT, 
    SYSTEM_CPU_IOWAIT, SYSTEM_CPU_IRQ, SYSTEM_CPU_SOFTIRQ, SYSTEM_MEMORY_SLAB, 
    PROCESS_MEMORY_LIB, PROCESS_MEMORY_DIRTY, PROCESS_ENV_VAR_COUNT,
    PROCESS_MEMORY_USS, SYSTEM_MEMORY_WIRED, PROCESS_NICE, PROCESS_UPTIME,
    SYSTEM_CPU_CTX_SWITCHES, SYSTEM_NETWORK_CONNECTIONS, PROCESS_CPU_AFFINITY,
    PROCESS_MEMORY_PAGE_FAULTS_TOTAL,
    SYSTEM_DISK_READ_COUNT_TOTAL, SYSTEM_DISK_WRITE_COUNT_TOTAL,
    SYSTEM_SWAP_IN_BYTES_TOTAL, SYSTEM_SWAP_OUT_BYTES_TOTAL,
    PROCESS_MEMORY_VMS_PERCENT, SYSTEM_CPU_PHYSICAL_COUNT,
    SYSTEM_MEMORY_PERCENT, PROCESS_OPEN_FILES_COUNT, SYSTEM_DISK_BUSY_TIME_MS,
    SYSTEM_NETWORK_INTERFACES_COUNT, PROCESS_THREADS_TOTAL_TIME_USER, PROCESS_THREADS_TOTAL_TIME_SYSTEM, 
    SYSTEM_DISK_READ_TIME_MS, SYSTEM_DISK_WRITE_TIME_MS, PROCESS_MEMORY_MAPS_COUNT, 
    SYSTEM_NETWORK_INTERFACES_UP_COUNT, PROCESS_CONTEXT_SWITCHES_TOTAL,
    PROCESS_CPU_TIMES_CHILDREN_USER, PROCESS_CPU_TIMES_CHILDREN_SYSTEM,
    SYSTEM_NETWORK_INTERFACES_DOWN_COUNT, SYSTEM_DISK_READ_MERGED_COUNT, SYSTEM_DISK_WRITE_MERGED_COUNT,
    SYSTEM_MEMORY_SHARED_BYTES, PROCESS_MEMORY_PSS_BYTES, SYSTEM_NETWORK_INTERFACES_MTU_TOTAL,
    PROCESS_MEMORY_SWAP_BYTES, SYSTEM_NETWORK_ERRORS_TOTAL,
    SYSTEM_NETWORK_INTERFACES_SPEED_TOTAL_MBPS, SYSTEM_NETWORK_INTERFACES_DUPLEX_FULL_COUNT,
    PROCESS_MEMORY_USS_PERCENT,
    SYSTEM_PROCESS_COUNT, PROCESS_MEMORY_PSS_PERCENT,
    SYSTEM_CPU_LOAD_1M_PERCENT, SYSTEM_MEMORY_AVAILABLE_PERCENT,
    SYSTEM_CPU_CORES_USAGE_PERCENT, SYSTEM_DISK_PARTITIONS_USAGE_PERCENT,
    SYSTEM_NETWORK_INTERFACES_BYTES_SENT, SYSTEM_NETWORK_INTERFACES_BYTES_RECV,
    PROCESS_LIMIT_NOFILE_SOFT, PROCESS_LIMIT_NOFILE_HARD,
    PROCESS_LIMIT_AS_SOFT, PROCESS_LIMIT_AS_HARD,
    SYSTEM_LOAD_5M_PERCENT, SYSTEM_LOAD_15M_PERCENT,
    PROCESS_LIMIT_NOFILE_UTILIZATION_PERCENT, PROCESS_LIMIT_AS_UTILIZATION_PERCENT,
    PROCESS_IO_READ_THROUGHPUT_BPS, PROCESS_IO_WRITE_THROUGHPUT_BPS,
    SYSTEM_DISK_READ_THROUGHPUT_BPS, SYSTEM_DISK_WRITE_THROUGHPUT_BPS,
    SYSTEM_NETWORK_THROUGHPUT_RECV_BPS, SYSTEM_NETWORK_THROUGHPUT_SENT_BPS, 
    SYSTEM_CPU_CTX_SWITCH_RATE_BPS, SYSTEM_CPU_INTERRUPT_RATE_BPS, 
    WS_MESSAGE_SIZE_BYTES, WS_BINARY_FRAMES_REJECTED_TOTAL,
    SYSTEM_PAGE_FAULT_MINOR_RATE_BPS, SYSTEM_PAGE_FAULT_MAJOR_RATE_BPS,
    WS_CONNECTION_ERRORS_TOTAL,
    SYSTEM_CPU_SOFT_INTERRUPT_RATE_BPS, SYSTEM_CPU_SYSCALL_RATE_BPS
)

try:
    import psutil
    _process = psutil.Process()
except ImportError:
    psutil = None
    _process = None

try:
    import resource
except ImportError:
    resource = None

class HealthEngine:
    def __init__(self, app_start_time: float):
        self.app_start_time = app_start_time

    def collect_raw_metrics(self) -> Dict[str, Any]:
        raw = {}
        if psutil:
            try:
                mem = psutil.virtual_memory()
                raw.update({
                    'sys_mem_available': mem.available, 'sys_mem_total': mem.total, 'sys_mem_used': mem.used, 
                    'sys_mem_free': mem.free, 'sys_mem_percent': mem.percent, 'sys_mem_active': getattr(mem, "active", 0), 
                    'sys_mem_inactive': getattr(mem, "inactive", 0), 'sys_mem_buffers': getattr(mem, "buffers", 0), 
                    'sys_mem_cached': getattr(mem, "cached", 0), 'sys_mem_shared': getattr(mem, "shared", 0), 
                    'sys_mem_slab': getattr(mem, "slab", 0), 'sys_mem_wired': getattr(mem, "wired", 0)
                })
                swap = psutil.swap_memory()
                raw.update({
                    'sys_swap_total': swap.total, 'sys_swap_used': swap.used, 'sys_swap_free': swap.free, 
                    'sys_swap_percent': swap.percent, 'sys_swap_sin': swap.sin, 'sys_swap_sout': swap.sout
                })
                cpu_times = psutil.cpu_times_percent(interval=None)
                raw.update({
                    'sys_cpu_user': cpu_times.user, 'sys_cpu_system': cpu_times.system, 'sys_cpu_idle': cpu_times.idle, 
                    'sys_cpu_iowait': getattr(cpu_times, "iowait", 0.0), 'sys_cpu_irq': getattr(cpu_times, "irq", 0.0), 
                    'sys_cpu_softirq': getattr(cpu_times, "softirq", 0.0), 'sys_cpu_steal': getattr(cpu_times, "steal", 0.0), 
                    'sys_cpu_guest': getattr(cpu_times, "guest", 0.0)
                })
                raw.update({
                    'sys_cpu_percent': psutil.cpu_percent(interval=None), 'sys_cpu_count': psutil.cpu_count(), 
                    'sys_cpu_physical_count': psutil.cpu_count(logical=False) or 0
                })
                cpu_freq = psutil.cpu_freq()
                raw['sys_cpu_freq_current'] = cpu_freq.current if cpu_freq else 0.0
                cpu_stats = psutil.cpu_stats()
                raw.update({
                    'sys_cpu_ctx_switches': cpu_stats.ctx_switches, 'sys_cpu_interrupts': cpu_stats.interrupts, 
                    'sys_cpu_soft_interrupts': cpu_stats.soft_interrupts, 'sys_cpu_syscalls': cpu_stats.syscalls
                })
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    raw.update({
                        'sys_disk_read_bytes': disk_io.read_bytes, 'sys_disk_write_bytes': disk_io.write_bytes, 
                        'sys_disk_read_count': disk_io.read_count, 'sys_disk_write_count': disk_io.write_count, 
                        'sys_disk_read_time': disk_io.read_time, 'sys_disk_write_time': disk_io.write_time, 
                        'sys_disk_busy_time': getattr(disk_io, "busy_time", 0), 
                        'sys_disk_read_merged': getattr(disk_io, "read_merged_count", 0), 
                        'sys_disk_write_merged': getattr(disk_io, "write_merged_count", 0)
                    })
                raw.update({
                    'sys_disk_usage_percent': psutil.disk_usage('/').percent, 
                    'sys_disk_partitions_count': len(psutil.disk_partitions())
                })
                net_io = psutil.net_io_counters()
                raw.update({
                    'sys_net_bytes_sent': net_io.bytes_sent, 'sys_net_bytes_recv': net_io.bytes_recv, 
                    'sys_net_packets_sent': net_io.packets_sent, 'sys_net_packets_recv': net_io.packets_recv, 
                    'sys_net_errin': net_io.errin, 'sys_net_errout': net_io.errout, 
                    'sys_net_dropin': net_io.dropin, 'sys_net_dropout': net_io.dropout
                })
                raw.update({
                    'sys_net_interfaces_count': len(psutil.net_if_addrs()), 'sys_boot_time': psutil.boot_time(), 
                    'sys_users_count': len(psutil.users()), 'sys_process_count': len(psutil.pids())
                })
                try:
                    raw['sys_network_connections'] = len(psutil.net_connections(kind='all'))
                except Exception:
                    raw['sys_network_connections'] = 0
                
                if_stats = psutil.net_if_stats()
                raw.update({
                    'sys_net_interfaces_up': sum(1 for s in if_stats.values() if s.isup), 
                    'sys_net_interfaces_down': sum(1 for s in if_stats.values() if not s.isup), 
                    'sys_net_mtu_total': sum(s.mtu for s in if_stats.values()), 
                    'sys_net_speed_total': sum(s.speed for s in if_stats.values() if s.speed > 0), 
                    'sys_net_duplex_full': sum(1 for s in if_stats.values() if getattr(s, "duplex", 0) == 2)
                })
                load_avg = os.getloadavg() if hasattr(os, "getloadavg") else (0, 0, 0)
                raw.update({'sys_load_1m': load_avg[0], 'sys_load_5m': load_avg[1], 'sys_load_15m': load_avg[2], 'sys_cpu_cores_usage': psutil.cpu_percent(interval=None, percpu=True)})
                disk_part_usage = {}
                for part in psutil.disk_partitions(all=False):
                    try: disk_part_usage[part.mountpoint] = psutil.disk_usage(part.mountpoint).percent
                    except: continue
                raw['sys_disk_partitions_usage'] = disk_part_usage
                net_io_per_nic = psutil.net_io_counters(pernic=True)
                raw['sys_net_io_per_nic'] = {nic: {"bytes_sent": io.bytes_sent, "bytes_recv": io.bytes_recv} for nic, io in net_io_per_nic.items()}
            except Exception as e: logger.error(f"Error collecting system metrics: {e}")

        if _process:
            try:
                mem = _process.memory_info()
                raw.update({
                    'proc_rss': mem.rss, 'proc_vms': mem.vms, 'proc_shared': getattr(mem, "shared", 0), 
                    'proc_text': getattr(mem, "text", 0), 'proc_data': getattr(mem, "data", 0), 
                    'proc_lib': getattr(mem, "lib", 0), 'proc_dirty': getattr(mem, "dirty", 0), 
                    'proc_minor_pf': getattr(mem, "pfaults", 0), 'proc_major_pf': getattr(mem, "pageins", 0)
                })
                if hasattr(_process, "memory_full_info"):
                    try:
                        full_mem = _process.memory_full_info()
                        raw.update({'proc_uss': full_mem.uss, 'proc_pss': getattr(full_mem, "pss", 0), 'proc_swap': getattr(full_mem, "swap", 0)})
                    except: pass
                raw.update({'proc_mem_percent': _process.memory_percent(), 'proc_cpu_percent': _process.cpu_percent(interval=None)})
                cpu_times = _process.cpu_times()
                raw.update({'proc_cpu_user': cpu_times.user, 'proc_cpu_system': cpu_times.system, 'proc_cpu_children_user': getattr(cpu_times, "children_user", 0.0), 'proc_cpu_children_system': getattr(cpu_times, "children_system", 0.0)})
                raw.update({'proc_num_threads': _process.num_threads(), 'proc_num_fds': _process.num_fds() if hasattr(_process, "num_fds") else getattr(_process, "num_handles", 0)})
                ctx = _process.num_ctx_switches()
                raw.update({'proc_ctx_voluntary': ctx.voluntary, 'proc_ctx_involuntary': ctx.involuntary})
                
                if hasattr(_process, "io_counters"):
                    try:
                        io = _process.io_counters()
                        if io: raw.update({'proc_io_read_bytes': io.read_bytes, 'proc_io_write_bytes': io.write_bytes, 'proc_io_read_count': io.read_count, 'proc_io_write_count': io.write_count})
                    except: pass
                
                raw.update({
                    'proc_connections_count': len(_process.net_connections()), 
                    'proc_children_count': len(_process.children()), 
                    'proc_nice': _process.nice(), 
                    'proc_cpu_affinity_count': len(_process.cpu_affinity()) if hasattr(_process, "cpu_affinity") else 0
                })

                try: raw['proc_status'] = _process.status()
                except: raw['proc_status'] = "unknown"
                try: raw['proc_create_time'] = _process.create_time()
                except: raw['proc_create_time'] = 0.0
                
                try:
                    raw['proc_open_files_count'] = len(_process.open_files())
                except:
                    raw['proc_open_files_count'] = 0
                
                try:
                    raw['proc_memory_maps_count'] = len(_process.memory_maps())
                except:
                    raw['proc_memory_maps_count'] = 0
                
                try:
                    raw['proc_env_var_count'] = len(_process.environ())
                except:
                    raw['proc_env_var_count'] = 0

                u_total, s_total = 0.0, 0.0
                for t in _process.threads(): u_total += t.user_time; s_total += t.system_time
                raw.update({'proc_threads_user_time': u_total, 'proc_threads_system_time': s_total})
            except Exception as e: logger.error(f"Error collecting process metrics: {e}")

        if resource:
            try:
                raw['proc_limit_nofile_soft'], raw['proc_limit_nofile_hard'] = resource.getrlimit(resource.RLIMIT_NOFILE)
                raw['proc_limit_as_soft'], raw['proc_limit_as_hard'] = resource.getrlimit(resource.RLIMIT_AS)
            except: pass
        return raw

    async def get_health_data(self, app_state: Any, app_version: str, git_commit: str, operational_apex: str) -> Dict[str, Any]:
        raw, now = self.collect_raw_metrics(), time.time()
        uptime_seconds, cpu_count = now - self.app_start_time, raw.get('sys_cpu_count', 1)
        
        # Mapping to Prometheus Gauges
        gauge_mappings = {
            SYSTEM_LOAD_1M: raw.get('sys_load_1m', 0), SYSTEM_LOAD_5M: raw.get('sys_load_5m', 0), SYSTEM_LOAD_15M: raw.get('sys_load_15m', 0),
            SYSTEM_UPTIME: now - raw.get('sys_boot_time', now), SYSTEM_MEMORY_AVAILABLE: raw.get('sys_mem_available', 0),
            SYSTEM_MEMORY_TOTAL: raw.get('sys_mem_total', 0), SYSTEM_MEMORY_USED: raw.get('sys_mem_used', 0),
            SYSTEM_MEMORY_FREE: raw.get('sys_mem_free', 0), SYSTEM_MEMORY_PERCENT: raw.get('sys_mem_percent', 0),
            SYSTEM_MEMORY_ACTIVE_BYTES: raw.get('sys_mem_active', 0), SYSTEM_MEMORY_INACTIVE_BYTES: raw.get('sys_mem_inactive', 0),
            SYSTEM_MEMORY_BUFFERS: raw.get('sys_mem_buffers', 0), SYSTEM_MEMORY_CACHED: raw.get('sys_mem_cached', 0),
            SYSTEM_MEMORY_SHARED_BYTES: raw.get('sys_mem_shared', 0), SYSTEM_MEMORY_SLAB: raw.get('sys_mem_slab', 0),
            SYSTEM_MEMORY_WIRED: raw.get('sys_mem_wired', 0), SYSTEM_SWAP_USED_BYTES: raw.get('sys_swap_used', 0),
            SYSTEM_SWAP_FREE_BYTES: raw.get('sys_swap_free', 0), SWAP_MEMORY_USAGE_PERCENT: raw.get('sys_swap_percent', 0),
            SYSTEM_SWAP_IN_BYTES_TOTAL: raw.get('sys_swap_sin', 0), SYSTEM_SWAP_OUT_BYTES_TOTAL: raw.get('sys_swap_sout', 0),
            SYSTEM_CPU_COUNT: cpu_count, SYSTEM_CPU_PHYSICAL_COUNT: raw.get('sys_cpu_physical_count', 0),
            SYSTEM_CPU_USAGE_USER: raw.get('sys_cpu_user', 0), SYSTEM_CPU_USAGE_SYSTEM: raw.get('sys_cpu_system', 0),
            SYSTEM_CPU_USAGE_IDLE: raw.get('sys_cpu_idle', 0), SYSTEM_CPU_IOWAIT: raw.get('sys_cpu_iowait', 0),
            SYSTEM_CPU_IRQ: raw.get('sys_cpu_irq', 0), SYSTEM_CPU_SOFTIRQ: raw.get('sys_cpu_softirq', 0),
            SYSTEM_CPU_STEAL: raw.get('sys_cpu_steal', 0), SYSTEM_CPU_GUEST: raw.get('sys_cpu_guest', 0),
            SYSTEM_CPU_FREQUENCY: raw.get('sys_cpu_freq_current', 0), CPU_USAGE_PERCENT: raw.get('sys_cpu_percent', 0),
            SYSTEM_CPU_CTX_SWITCHES: raw.get('sys_cpu_ctx_switches', 0), SYSTEM_CPU_INTERRUPTS: raw.get('sys_cpu_interrupts', 0),
            SYSTEM_CPU_SOFT_INTERRUPTS: raw.get('sys_cpu_soft_interrupts', 0), SYSTEM_CPU_SYSCALLS: raw.get('sys_cpu_syscalls', 0),
            SYSTEM_DISK_READ_BYTES: raw.get('sys_disk_read_bytes', 0), SYSTEM_DISK_WRITE_BYTES: raw.get('sys_disk_write_bytes', 0),
            SYSTEM_DISK_READ_COUNT_TOTAL: raw.get('sys_disk_read_count', 0), SYSTEM_DISK_WRITE_COUNT_TOTAL: raw.get('sys_disk_write_count', 0),
            SYSTEM_DISK_READ_TIME_MS: raw.get('sys_disk_read_time', 0), SYSTEM_DISK_WRITE_TIME_MS: raw.get('sys_disk_write_time', 0),
            SYSTEM_DISK_BUSY_TIME_MS: raw.get('sys_disk_busy_time', 0), SYSTEM_DISK_READ_MERGED_COUNT: raw.get('sys_disk_read_merged', 0),
            SYSTEM_DISK_WRITE_MERGED_COUNT: raw.get('sys_disk_write_merged', 0), DISK_USAGE_PERCENT: raw.get('sys_disk_usage_percent', 0),
            SYSTEM_DISK_PARTITIONS_COUNT: raw.get('sys_disk_partitions_count', 0), SYSTEM_NETWORK_BYTES_SENT: raw.get('sys_net_bytes_sent', 0),
            SYSTEM_NETWORK_BYTES_RECV: raw.get('sys_net_bytes_recv', 0), SYSTEM_NETWORK_PACKETS_SENT: raw.get('sys_net_packets_sent', 0),
            SYSTEM_NETWORK_PACKETS_RECV: raw.get('sys_net_packets_recv', 0), SYSTEM_NETWORK_ERRORS_IN: raw.get('sys_net_errin', 0),
            SYSTEM_NETWORK_ERRORS_OUT: raw.get('sys_net_errout', 0), SYSTEM_NETWORK_DROPS_IN: raw.get('sys_net_dropin', 0),
            SYSTEM_NETWORK_DROPS_OUT: raw.get('sys_net_dropout', 0), SYSTEM_NETWORK_INTERFACES_COUNT: raw.get('sys_net_interfaces_count', 0),
            SYSTEM_NETWORK_INTERFACES_UP_COUNT: raw.get('sys_net_interfaces_up', 0), SYSTEM_NETWORK_INTERFACES_DOWN_COUNT: raw.get('sys_net_interfaces_down', 0),
            SYSTEM_NETWORK_INTERFACES_MTU_TOTAL: raw.get('sys_net_mtu_total', 0), SYSTEM_NETWORK_INTERFACES_SPEED_TOTAL_MBPS: raw.get('sys_net_speed_total', 0),
            SYSTEM_NETWORK_INTERFACES_DUPLEX_FULL_COUNT: raw.get('sys_net_duplex_full', 0), SYSTEM_BOOT_TIME: raw.get('sys_boot_time', 0),
            SYSTEM_USERS_COUNT: raw.get('sys_users_count', 0), SYSTEM_PROCESS_COUNT: raw.get('sys_process_count', 0),
            SYSTEM_NETWORK_CONNECTIONS: raw.get('sys_network_connections', 0), PROCESS_MEMORY_RSS: raw.get('proc_rss', 0),
            PROCESS_MEMORY_VMS: raw.get('proc_vms', 0), PROCESS_MEMORY_SHARED_BYTES: raw.get('proc_shared', 0),
            PROCESS_MEMORY_TEXT_BYTES: raw.get('proc_text', 0), PROCESS_MEMORY_DATA_BYTES: raw.get('proc_data', 0),
            PROCESS_MEMORY_LIB: raw.get('proc_lib', 0), PROCESS_MEMORY_DIRTY: raw.get('proc_dirty', 0),
            PAGE_FAULTS_MINOR: raw.get('proc_minor_pf', 0), PAGE_FAULTS_MAJOR: raw.get('proc_major_pf', 0),
            PROCESS_MEMORY_USS: raw.get('proc_uss', 0), PROCESS_MEMORY_PSS_BYTES: raw.get('proc_pss', 0),
            PROCESS_MEMORY_SWAP_BYTES: raw.get('proc_swap', 0), MEMORY_PERCENT: raw.get('proc_mem_percent', 0),
            PROCESS_CPU_USAGE_USER: raw.get('proc_cpu_user', 0), PROCESS_CPU_USAGE_SYSTEM: raw.get('proc_cpu_system', 0),
            PROCESS_CPU_TIMES_CHILDREN_USER: raw.get('proc_cpu_children_user', 0), PROCESS_CPU_TIMES_CHILDREN_SYSTEM: raw.get('proc_cpu_children_system', 0),
            PROCESS_CPU_PERCENT_TOTAL: raw.get('proc_cpu_percent', 0), PROCESS_NUM_THREADS: raw.get('proc_num_threads', 0),
            OPEN_FDS: raw.get('proc_num_fds', 0), PROCESS_OPEN_FILES_COUNT: raw.get('proc_open_files_count', 0),
            THREAD_COUNT: threading.active_count(), CONTEXT_SWITCHES_VOLUNTARY: raw.get('proc_ctx_voluntary', 0),
            CONTEXT_SWITCHES_INVOLUNTARY: raw.get('proc_ctx_involuntary', 0), PROCESS_IO_READ_BYTES: raw.get('proc_io_read_bytes', 0),
            PROCESS_IO_WRITE_BYTES: raw.get('proc_io_write_bytes', 0), PROCESS_IO_READ_COUNT: raw.get('proc_io_read_count', 0),
            PROCESS_IO_WRITE_COUNT: raw.get('proc_io_write_count', 0), PROCESS_CONNECTIONS_COUNT: raw.get('proc_connections_count', 0),
            PROCESS_CHILDREN_COUNT: raw.get('proc_children_count', 0), PROCESS_MEMORY_MAPS_COUNT: raw.get('proc_memory_maps_count', 0),
            PROCESS_ENV_VAR_COUNT: raw.get('proc_env_var_count', 0), PROCESS_NICE: raw.get('proc_nice', 0),
            PROCESS_CPU_AFFINITY: raw.get('proc_cpu_affinity_count', 0), PROCESS_UPTIME: uptime_seconds,
            PROCESS_THREADS_TOTAL_TIME_USER: raw.get('proc_threads_user_time', 0), PROCESS_THREADS_TOTAL_TIME_SYSTEM: raw.get('proc_threads_system_time', 0)
        }
        for gauge, val in gauge_mappings.items(): gauge.set(val)
        
        sn_err_total = raw.get('sys_net_errin', 0) + raw.get('sys_net_errout', 0) + raw.get('sys_net_dropin', 0) + raw.get('sys_net_dropout', 0)
        SYSTEM_NETWORK_ERRORS_TOTAL.set(sn_err_total)
        
        sys_mem_total = raw.get('sys_mem_total', 1) or 1
        PROCESS_MEMORY_VMS_PERCENT.set((raw.get('proc_vms', 0) / sys_mem_total) * 100)
        PROCESS_MEMORY_USS_PERCENT.set((raw.get('proc_uss', 0) / sys_mem_total) * 100)
        PROCESS_MEMORY_PSS_PERCENT.set((raw.get('proc_pss', 0) / sys_mem_total) * 100)
        PROCESS_MEMORY_PAGE_FAULTS_TOTAL.set(raw.get('proc_minor_pf', 0) + raw.get('proc_major_pf', 0))
        PROCESS_CONTEXT_SWITCHES_TOTAL.set(raw.get('proc_ctx_voluntary', 0) + raw.get('proc_ctx_involuntary', 0))

        if 'proc_limit_nofile_soft' in raw:
            PROCESS_LIMIT_NOFILE_SOFT.set(raw['proc_limit_nofile_soft']); PROCESS_LIMIT_NOFILE_HARD.set(raw['proc_limit_nofile_hard']); PROCESS_LIMIT_AS_SOFT.set(raw['proc_limit_as_soft']); PROCESS_LIMIT_AS_HARD.set(raw['proc_limit_as_hard'])
            PROCESS_LIMIT_NOFILE_UTILIZATION_PERCENT.set((raw.get('proc_num_fds', 0) / raw['proc_limit_nofile_soft'] * 100) if raw['proc_limit_nofile_soft'] > 0 else 0.0)
            PROCESS_LIMIT_AS_UTILIZATION_PERCENT.set((raw.get('proc_vms', 0) / raw['proc_limit_as_soft'] * 100) if raw['proc_limit_as_soft'] > 0 else 0.0)

        # Throughput calculations
        ws_rb, ws_sb = int(WS_BYTES_RECEIVED_TOTAL._value.get()), int(WS_BYTES_SENT_TOTAL._value.get())
        dt = now - getattr(app_state, "last_throughput_time", self.app_start_time)
        if dt >= 1.0:
            WS_THROUGHPUT_RECEIVED_BPS.set((ws_rb - getattr(app_state, "last_bytes_received", 0)) / dt)
            WS_THROUGHPUT_SENT_BPS.set((ws_sb - getattr(app_state, "last_bytes_sent", 0)) / dt)
            PROCESS_IO_READ_THROUGHPUT_BPS.set((raw.get('proc_io_read_bytes', 0) - getattr(app_state, "last_proc_read_bytes", 0)) / dt)
            PROCESS_IO_WRITE_THROUGHPUT_BPS.set((raw.get('proc_io_write_bytes', 0) - getattr(app_state, "last_proc_write_bytes", 0)) / dt)
            SYSTEM_DISK_READ_THROUGHPUT_BPS.set((raw.get('sys_disk_read_bytes', 0) - getattr(app_state, "last_sys_read_bytes", 0)) / dt)
            SYSTEM_DISK_WRITE_THROUGHPUT_BPS.set((raw.get('sys_disk_write_bytes', 0) - getattr(app_state, "last_sys_write_bytes", 0)) / dt)
            SYSTEM_NETWORK_THROUGHPUT_RECV_BPS.set((raw.get('sys_net_bytes_recv', 0) - getattr(app_state, "last_sys_net_recv_bytes", 0)) / dt)
            SYSTEM_NETWORK_THROUGHPUT_SENT_BPS.set((raw.get('sys_net_bytes_sent', 0) - getattr(app_state, "last_sys_net_sent_bytes", 0)) / dt)
            SYSTEM_CPU_CTX_SWITCH_RATE_BPS.set((raw.get('sys_cpu_ctx_switches', 0) - getattr(app_state, "last_sys_ctx_switches", 0)) / dt)
            SYSTEM_CPU_INTERRUPT_RATE_BPS.set((raw.get('sys_cpu_interrupts', 0) + raw.get('sys_cpu_soft_interrupts', 0) - getattr(app_state, "last_sys_interrupts", 0)) / dt)
            SYSTEM_CPU_SOFT_INTERRUPT_RATE_BPS.set((raw.get('sys_cpu_soft_interrupts', 0) - getattr(app_state, "last_sys_soft_interrupts", 0)) / dt)
            SYSTEM_CPU_SYSCALL_RATE_BPS.set((raw.get('sys_cpu_syscalls', 0) - getattr(app_state, "last_sys_syscalls", 0)) / dt)
            SYSTEM_PAGE_FAULT_MINOR_RATE_BPS.set((raw.get('proc_minor_pf', 0) - getattr(app_state, "last_sys_pf_minor", 0)) / dt)
            SYSTEM_PAGE_FAULT_MAJOR_RATE_BPS.set((raw.get('proc_major_pf', 0) - getattr(app_state, "last_sys_pf_major", 0)) / dt)
            
            app_state.last_throughput_time, app_state.last_bytes_received, app_state.last_bytes_sent = now, ws_rb, ws_sb
            app_state.last_proc_read_bytes, app_state.last_proc_write_bytes = raw.get('proc_io_read_bytes', 0), raw.get('proc_io_write_bytes', 0)
            app_state.last_sys_read_bytes, app_state.last_sys_write_bytes = raw.get('sys_disk_read_bytes', 0), raw.get('sys_disk_write_bytes', 0)
            app_state.last_sys_net_recv_bytes, app_state.last_sys_net_sent_bytes = raw.get('sys_net_bytes_recv', 0), raw.get('sys_net_bytes_sent', 0)
            app_state.last_sys_ctx_switches = raw.get('sys_cpu_ctx_switches', 0)
            app_state.last_sys_interrupts = raw.get('sys_cpu_interrupts', 0) + raw.get('sys_cpu_soft_interrupts', 0)
            app_state.last_sys_soft_interrupts = raw.get('sys_cpu_soft_interrupts', 0)
            app_state.last_sys_syscalls = raw.get('sys_cpu_syscalls', 0)
            app_state.last_sys_pf_minor, app_state.last_sys_pf_major = raw.get('proc_minor_pf', 0), raw.get('proc_major_pf', 0)

        # Summary calculations
        def sum_counter(counter):
            t = 0
            for m in counter.collect():
                for s in m.samples:
                    if s.name.endswith("_total"): t += s.value
            return t
        
        ws_rc, ws_sc = sum_counter(WS_MESSAGES_RECEIVED_TOTAL), sum_counter(WS_MESSAGES_SENT_TOTAL)
        total_finished, total_success = 0, 0
        for m in TASKS_TOTAL.collect():
            for s in m.samples:
                total_finished += s.value
                if s.labels.get("status") == "success": total_success += s.value
        success_rate = (total_success / total_finished * 100) if total_finished > 0 else 100.0
        ws_errs = {"auth_failure": 0, "protocol_error": 0, "other_error": 0}
        for m in WS_CONNECTION_ERRORS_TOTAL.collect():
            for s in m.samples: ws_errs[s.labels.get("error_type", "other_error")] = int(s.value)
        
        for i, p in enumerate(raw.get('sys_cpu_cores_usage', [])): SYSTEM_CPU_CORES_USAGE_PERCENT.labels(core=str(i)).set(p)
        for pt, p in raw.get('sys_disk_partitions_usage', {}).items(): SYSTEM_DISK_PARTITIONS_USAGE_PERCENT.labels(partition=pt).set(p)
        for nic, io in raw.get('sys_net_io_per_nic', {}).items():
            SYSTEM_NETWORK_INTERFACES_BYTES_SENT.labels(interface=nic).set(io['bytes_sent'])
            SYSTEM_NETWORK_INTERFACES_BYTES_RECV.labels(interface=nic).set(io['bytes_recv'])

        active_tasks_list = await registry.list_active_tasks()
        tools_summary = {}
        for t in active_tasks_list: tools_summary[t["tool_name"]] = tools_summary.get(t["tool_name"], 0) + 1

        return { 
            "status": "healthy", "version": app_version, "git_commit": git_commit, "operational_apex": operational_apex, 
            "python_version": sys.version, "python_implementation": platform.python_implementation(), "system_platform": sys.platform, 
            "cpu_count": raw.get('sys_cpu_count', 0), "cpu_physical_count": raw.get('sys_cpu_physical_count', 0), "cpu_frequency_current_mhz": raw.get('sys_cpu_freq_current', 0.0), "cpu_usage_percent": raw.get('sys_cpu_percent', 0.0),
            "system_cpu_idle_percent": raw.get('sys_cpu_idle', 0.0),
            "system_cpu_usage": {
                "user_percent": raw.get('sys_cpu_user', 0.0), "system_percent": raw.get('sys_cpu_system', 0.0), "idle_percent": raw.get('sys_cpu_idle', 0.0), "steal_percent": raw.get('sys_cpu_steal', 0.0),
                "guest_percent": raw.get('sys_cpu_guest', 0.0), "iowait_percent": raw.get('sys_cpu_iowait', 0.0), "irq_percent": raw.get('sys_cpu_irq', 0.0), "softirq_percent": raw.get('sys_cpu_softirq', 0.0),
                "load_1m_percent": (raw.get('sys_load_1m', 0) / cpu_count * 100) if cpu_count > 0 else 0.0, "load_5m_percent": (raw.get('sys_load_5m', 0) / cpu_count * 100) if cpu_count > 0 else 0.0,
                "load_15m_percent": (raw.get('sys_load_15m', 0) / cpu_count * 100) if cpu_count > 0 else 0.0, "cores": raw.get('sys_cpu_cores_usage', [])
            },
            "system_cpu_stats": {
                "interrupts": raw.get('sys_cpu_interrupts', 0), "soft_interrupts": raw.get('sys_cpu_soft_interrupts', 0), "syscalls": raw.get('sys_cpu_syscalls', 0),
                "soft_interrupt_rate_per_sec": float(SYSTEM_CPU_SOFT_INTERRUPT_RATE_BPS._value.get()), "syscall_rate_per_sec": float(SYSTEM_CPU_SYSCALL_RATE_BPS._value.get()),
                "context_switches": raw.get('sys_cpu_ctx_switches', 0), "context_switch_rate_per_sec": float(SYSTEM_CPU_CTX_SWITCH_RATE_BPS._value.get()), "interrupt_rate_per_sec": float(SYSTEM_CPU_INTERRUPT_RATE_BPS._value.get())
            },
            "thread_count": threading.active_count(), "open_fds": raw.get('proc_num_fds', 0), "process_open_files_count": raw.get('proc_open_files_count', 0),
            "process_resource_limits": {"nofile_soft": raw.get('proc_limit_nofile_soft', 0), "nofile_hard": raw.get('proc_limit_nofile_hard', 0), "as_soft": raw.get('proc_limit_as_soft', 0), "as_hard": raw.get('proc_limit_as_hard', 0)},
            "process_resource_utilization_percent": {"nofile": float(PROCESS_LIMIT_NOFILE_UTILIZATION_PERCENT._value.get()), "as": float(PROCESS_LIMIT_AS_UTILIZATION_PERCENT._value.get())},
            "context_switches": {"voluntary": raw.get('proc_ctx_voluntary', 0), "involuntary": raw.get('proc_ctx_involuntary', 0)},
            "page_faults": {
                "minor": raw.get('proc_minor_pf', 0), "major": raw.get('proc_major_pf', 0), "total": raw.get('proc_minor_pf', 0) + raw.get('proc_major_pf', 0),
                "minor_rate_per_sec": float(SYSTEM_PAGE_FAULT_MINOR_RATE_BPS._value.get()), "major_rate_per_sec": float(SYSTEM_PAGE_FAULT_MAJOR_RATE_BPS._value.get())
            },
            "swap_memory_usage_percent": raw.get('sys_swap_percent', 0.0),
            "system_swap_memory": {"used_bytes": raw.get('sys_swap_used', 0), "free_bytes": raw.get('sys_swap_free', 0), "sin_bytes": raw.get('sys_swap_sin', 0), "sout_bytes": raw.get('sys_swap_sout', 0)},
            "boot_time_seconds": raw.get('sys_boot_time', 0),
            "network_io_total": {
                "bytes_sent": raw.get('sys_net_bytes_sent', 0), "bytes_recv": raw.get('sys_net_bytes_recv', 0), "errin": raw.get('sys_net_errin', 0), "errout": raw.get('sys_net_errout', 0), "dropin": raw.get('sys_net_dropin', 0), "dropout": raw.get('sys_net_dropout', 0),
                "errors_total": sn_err_total, "interfaces_count": raw.get('sys_net_interfaces_count', 0), "interfaces_up_count": raw.get('sys_net_interfaces_up', 0), "interfaces_down_count": raw.get('sys_net_interfaces_down', 0), "mtu_total": raw.get('sys_net_mtu_total', 0),
                "speed_total_mbps": raw.get('sys_net_speed_total', 0), "duplex_full_count": raw.get('sys_net_duplex_full', 0), "read_throughput_bps": float(SYSTEM_NETWORK_THROUGHPUT_RECV_BPS._value.get()), "write_throughput_bps": float(SYSTEM_NETWORK_THROUGHPUT_SENT_BPS._value.get()),
                "recv_throughput_bps": float(SYSTEM_NETWORK_THROUGHPUT_RECV_BPS._value.get()), "sent_throughput_bps": float(SYSTEM_NETWORK_THROUGHPUT_SENT_BPS._value.get()), "per_interface": raw.get('sys_net_io_per_nic', {})
            },
            "disk_io_total": {
                "read_bytes": raw.get('sys_disk_read_bytes', 0), "write_bytes": raw.get('sys_disk_write_bytes', 0), "read_throughput_bps": float(SYSTEM_DISK_READ_THROUGHPUT_BPS._value.get()), "write_throughput_bps": float(SYSTEM_DISK_WRITE_THROUGHPUT_BPS._value.get()),
                "read_count": raw.get('sys_disk_read_count', 0), "write_count": raw.get('sys_disk_write_count', 0), "read_merged_count": raw.get('sys_disk_read_merged', 0), "write_merged_count": raw.get('sys_disk_write_merged', 0), "busy_time_ms": raw.get('sys_disk_busy_time', 0), "partitions_usage_percent": raw.get('sys_disk_partitions_usage', {})
            },
            "system_network_connections_count": raw.get('sys_network_connections', 0), "process_connections_count": raw.get('proc_connections_count', 0),
            "system_load_1m": raw.get('sys_load_1m', 0.0), "system_load_5m": raw.get('sys_load_5m', 0.0), "system_load_15m": raw.get('sys_load_15m', 0.0), "system_process_count": raw.get('sys_process_count', 0),
            "active_ws_connections": int(ACTIVE_WS_CONNECTIONS._value.get()), "peak_ws_connections": getattr(app_state, "peak_ws_connections", 0),
            "ws_messages_received": int(ws_rc), "ws_messages_sent": int(ws_sc), "ws_bytes_received": ws_rb, "ws_bytes_sent": ws_sb,
            "ws_throughput_bps": {"received": float(WS_THROUGHPUT_RECEIVED_BPS._value.get()), "sent": float(WS_THROUGHPUT_SENT_BPS._value.get())},
            "ws_binary_frames_rejected": int(WS_BINARY_FRAMES_REJECTED_TOTAL._value.get()), "ws_connection_errors": sum(ws_errs.values()), "ws_connection_errors_breakdown": ws_errs,
            "load_avg": [raw.get('sys_load_1m', 0.0), raw.get('sys_load_1m', 0.0), raw.get('sys_load_1m', 0.0)], "disk_usage_percent": raw.get('sys_disk_usage_percent', 0.0),
            "memory_rss_bytes": raw.get('proc_rss', 0), "memory_vms_bytes": raw.get('proc_vms', 0), "memory_percent": raw.get('proc_mem_percent', 0.0), "system_memory_available_bytes": raw.get('sys_mem_available', 0),
            "system_memory": {
                "available_bytes": raw.get('sys_mem_available', 0), "total_bytes": raw.get('sys_mem_total', 0), "used_bytes": raw.get('sys_mem_used', 0), "free_bytes": raw.get('sys_mem_free', 0), "active_bytes": raw.get('sys_mem_active', 0), "inactive_bytes": raw.get('sys_mem_inactive', 0),
                "buffers_bytes": raw.get('sys_mem_buffers', 0), "cached_bytes": raw.get('sys_mem_cached', 0), "slab_bytes": raw.get('sys_mem_slab', 0), "wired_bytes": raw.get('sys_mem_wired', 0), "shared_bytes": raw.get('sys_mem_shared', 0), "percent": raw.get('sys_mem_percent', 0.0), "available_percent": (raw.get('sys_mem_available', 0) / sys_mem_total * 100)
            },
            "system_memory_extended": {"used_bytes": raw.get('sys_mem_used', 0), "free_bytes": raw.get('sys_mem_free', 0)},
            "process_io_counters": {"read_bytes": raw.get('proc_io_read_bytes', 0), "write_bytes": raw.get('proc_io_write_bytes', 0), "read_count": raw.get('proc_io_read_count', 0), "write_count": raw.get('proc_io_write_count', 0), "read_throughput_bps": float(PROCESS_IO_READ_THROUGHPUT_BPS._value.get()), "write_throughput_bps": float(PROCESS_IO_WRITE_THROUGHPUT_BPS._value.get())},
            "process_cpu_usage": {"user_seconds": raw.get('proc_cpu_user', 0.0), "system_seconds": raw.get('proc_cpu_system', 0.0), "percent": raw.get('proc_cpu_percent', 0.0), "affinity_count": raw.get('proc_cpu_affinity_count', 0), "children_user_seconds": raw.get('proc_cpu_children_user', 0.0), "children_system_seconds": raw.get('proc_cpu_children_system', 0.0)},
            "process_threads_cpu_usage": {"total_user_seconds": raw.get('proc_threads_user_time', 0.0), "total_system_seconds": raw.get('proc_threads_system_time', 0.0)},
            "system_disk_io_times_ms": {"read_time": raw.get('sys_disk_read_time', 0), "write_time": raw.get('sys_disk_write_time', 0)},
            "process_memory_maps_count": raw.get('proc_memory_maps_count', 0), "system_network_interfaces_up_count": raw.get('sys_net_interfaces_up', 0), "process_context_switches_total": raw.get('proc_ctx_voluntary', 0) + raw.get('proc_ctx_involuntary', 0),
            "process_memory_advanced": {
                "shared_bytes": raw.get('proc_shared', 0), "text_bytes": raw.get('proc_text', 0), "data_bytes": raw.get('proc_data', 0), "lib_bytes": raw.get('proc_lib', 0), "dirty_bytes": raw.get('proc_dirty', 0), "uss_bytes": raw.get('proc_uss', 0), "pss_bytes": raw.get('proc_pss', 0), "swap_bytes": raw.get('proc_swap', 0),
                "vms_percent": (raw.get('proc_vms', 0) / sys_mem_total * 100), "uss_percent": (raw.get('proc_uss', 0) / sys_mem_total * 100), "pss_percent": (raw.get('proc_pss', 0) / sys_mem_total * 100)
            },
            "process_env_var_count": raw.get('proc_env_var_count', 0), "process_nice_value": raw.get('proc_nice', 0), "process_uptime_seconds": uptime_seconds, "process_num_threads": raw.get('proc_num_threads', 0), "process_children_count": raw.get('proc_children_count', 0),
            "process_status": raw.get('proc_status', 'unknown'), "process_create_time": raw.get('proc_create_time', 0.0),
            "system_network_packets": {"sent": raw.get('sys_net_packets_sent', 0), "recv": raw.get('sys_net_packets_recv', 0)},
            "system_disk_partitions_count": raw.get('sys_disk_partitions_count', 0), "system_users_count": raw.get('sys_users_count', 0),
            "registry_size": registry.active_task_count, "peak_registry_size": registry.peak_active_tasks, "total_tasks_started": registry.total_tasks_started, "task_success_rate_percent": success_rate, "registry_summary": tools_summary,
            "uptime_seconds": uptime_seconds, "system_uptime_seconds": int(now - raw.get('sys_boot_time', now)), "uptime_human": self.get_uptime_human(uptime_seconds), "start_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.app_start_time)), "timestamp": now
        }

    def get_uptime_human(self, seconds: float) -> str:
        days, rem = divmod(int(seconds), 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        parts = []
        if days > 0: parts.append(f"{days}d")
        if hours > 0: parts.append(f"{hours}h")
        if minutes > 0: parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        return " ".join(parts)

class BroadcastMetricsManager:
    def __init__(self, health_engine: HealthEngine, app: Any, version: str, commit: str, apex: str):
        self.health_engine = health_engine
        self.app = app
        self.version = version
        self.commit = commit
        self.apex = apex
        self.listeners: Dict[str, asyncio.Queue] = {}
        self.task: Optional[asyncio.Task] = None

    async def start(self):
        if self.task: return
        self.task = asyncio.create_task(self._run())
        logger.info("BroadcastMetricsManager started")

    async def stop(self):
        if self.task:
            self.task.cancel()
            try: await self.task
            except asyncio.CancelledError: pass
            self.task = None

    def subscribe(self, call_id: str) -> asyncio.Queue:
        queue = asyncio.Queue()
        self.listeners[call_id] = queue
        return queue

    def unsubscribe(self, call_id: str):
        if call_id in self.listeners:
            del self.listeners[call_id]

    async def _run(self):
        try:
            while True:
                await asyncio.sleep(3.0)
                if not self.listeners: continue
                metrics = await self.health_engine.get_health_data(self.app.state, self.version, self.commit, self.apex)
                for cid in list(self.listeners.keys()):
                    if cid not in self.listeners: continue
                    q = self.listeners[cid]
                    try:
                        while not q.empty(): q.get_nowait()
                        await q.put(metrics)
                    except Exception as e:
                        logger.error(f"Error pushing metrics: {e}")
        except asyncio.CancelledError: pass