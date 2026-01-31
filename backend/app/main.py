import sys
import asyncio
import json
import uuid
import time
import os
import subprocess
import threading
import platform
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Query, Request, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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

from .bridge import registry, ProgressEvent, ProgressPayload, format_sse, input_manager
from .logger import logger
from .context import call_id_var, tool_name_var
from .auth import verify_api_key, verify_api_key_ws
from .metrics import (
    TASK_DURATION, TASKS_TOTAL, TASK_PROGRESS_STEPS_TOTAL, 
    ACTIVE_WS_CONNECTIONS, WS_MESSAGES_RECEIVED_TOTAL, WS_MESSAGES_SENT_TOTAL, BUILD_INFO,
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
    PROCESS_IO_READ_THROUGHPUT_BPS, PROCESS_IO_WRITE_THROUGHPUT_BPS
)

# Configuration Constants for WebSocket and Task Lifecycle Management
WS_HEARTBEAT_TIMEOUT = 60.0
CLEANUP_INTERVAL = 60.0
STALE_TASK_MAX_AGE = 300.0
WS_MESSAGE_SIZE_LIMIT = 1024 * 1024  # 1MB
MAX_CONCURRENT_TASKS = 100
APP_VERSION = "1.4.6"
APP_START_TIME = time.time()
GIT_COMMIT = "v356-the-omega"
OPERATIONAL_APEX = "THE OMEGA"

BUILD_INFO.info({"version": APP_VERSION, "git_commit": GIT_COMMIT})
ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "*").split(",")

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.peak_ws_connections = 0
    app.state.last_throughput_time = time.time()
    app.state.last_bytes_received = 0
    app.state.last_bytes_sent = 0
    
    # v356 process IO throughput state
    app.state.last_io_time = time.time()
    app.state.last_proc_read_bytes = 0
    app.state.last_proc_write_bytes = 0
    
    cleanup_task = asyncio.create_task(cleanup_background_task())
    logger.info("Background cleanup task started")
    yield
    cleanup_task.cancel()
    await registry.cleanup_tasks()
    logger.info("Server shutdown: Cleaned up active tasks")

async def cleanup_background_task():
    try:
        while True:
            await asyncio.sleep(CLEANUP_INTERVAL)
            await registry.cleanup_stale_tasks(max_age_seconds=STALE_TASK_MAX_AGE)
    except asyncio.CancelledError:
        logger.info("Background cleanup task cancelled")

def get_memory_usage_kb():
    if _process:
        try:
            return _process.memory_info().rss // 1024
        except:
            pass
    
    try:
        if sys.platform == "darwin":
            # Mac
            output = subprocess.check_output(["ps", "-o", "rss=", "-p", str(os.getpid())])
            return int(output.strip())
        elif sys.platform.startswith("linux"):
            # Linux
            with open("/proc/self/status", "r") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        return int(line.split()[1])
    except:
        pass
    return 0

def get_process_memory_bytes():
    if _process:
        try:
            info = _process.memory_info()
            return info.rss, info.vms
        except:
            pass
    return 0, 0

def get_memory_percent():
    if _process:
        try:
            return _process.memory_percent()
        except:
            pass
    return 0.0

def get_cpu_percent():
    if psutil:
        try:
            return psutil.cpu_percent(interval=None)
        except:
            pass
    return 0.0

def get_system_cpu_usage_breakdown():
    if psutil:
        try:
            times = psutil.cpu_times_percent(interval=None)
            return times.user, times.system
        except:
            pass
    return 0.0, 0.0

def get_open_fds():
    if _process:
        try:
            if hasattr(_process, "num_fds"):
                return _process.num_fds()
            elif hasattr(_process, "num_handles"):
                return _process.num_handles()
        except:
            pass
    return 0

def get_context_switches():
    if _process:
        try:
            switches = _process.num_ctx_switches()
            return switches.voluntary, switches.involuntary
        except:
            pass
    return 0, 0

def get_disk_usage_percent():
    if psutil:
        try:
            return psutil.disk_usage('/').percent
        except:
            pass
    return 0.0

def get_system_memory_info():
    if psutil:
        try:
            mem = psutil.virtual_memory()
            return mem.available, mem.total
        except:
            pass
    return 0, 0

def get_page_faults():
    if _process:
        try:
            mem = _process.memory_info()
            minor = getattr(mem, "pfaults", 0)
            major = getattr(mem, "pageins", 0)
            return minor, major
        except:
            pass
    return 0, 0


def get_system_cpu_idle_percent():
    if psutil:
        try:
            return psutil.cpu_times_percent(interval=None).idle
        except:
            pass
    return 0.0

def get_process_cpu_times_total():
    if _process:
        try:
            times = _process.cpu_times()
            return times.user, times.system
        except:
            pass
    return 0.0, 0.0

def get_system_memory_extended():
    if psutil:
        try:
            mem = psutil.virtual_memory()
            return mem.used, mem.free
        except:
            pass
    return 0, 0

def get_system_network_packets():
    if psutil:
        try:
            io = psutil.net_io_counters()
            return io.packets_sent, io.packets_recv
        except:
            pass
    return 0, 0

def get_system_network_io_per_nic():
    if psutil:
        try:
            return psutil.net_io_counters(pernic=True)
        except:
            pass
    return {}

def get_system_swap_extended():
    if psutil:
        try:
            swap = psutil.swap_memory()
            return swap.used, swap.free
        except:
            pass
    return 0, 0

def get_process_io_counters():
    if _process:
        try:
            io = _process.io_counters()
            return io.read_bytes, io.write_bytes, io.read_count, io.write_count
        except:
            pass
    return 0, 0, 0, 0
def get_swap_memory_percent():
    if psutil:
        try:
            return psutil.swap_memory().percent
        except:
            pass
    return 0.0

def get_network_io():
    if psutil:
        try:
            io = psutil.net_io_counters()
            return io.bytes_sent, io.bytes_recv
        except:
            pass
    return 0, 0

def get_cpu_frequency():
    if psutil:
        try:
            freq = psutil.cpu_freq()
            if freq:
                return freq.current
        except:
            pass
    return 0.0

def get_disk_io():
    if psutil:
        try:
            io = psutil.disk_io_counters()
            if io:
                return io.read_bytes, io.write_bytes
        except:
            pass
    return 0, 0

def get_process_connections_count():
    if _process:
        try:
            return len(_process.net_connections())
        except:
            pass
    return 0

# v340 Supreme Apex Ultra Millennium Omega Plus Ultra Ultimate Helpers
def get_process_cpu_percent():
    if _process:
        try:
            return _process.cpu_percent(interval=None)
        except:
            pass
    return 0.0

def get_system_network_advanced():
    if psutil:
        try:
            io = psutil.net_io_counters()
            return io.errin, io.errout, io.dropin, io.dropout
        except:
            pass
    return 0, 0, 0, 0

def get_system_memory_advanced():
    if psutil:
        try:
            mem = psutil.virtual_memory()
            active = getattr(mem, "active", 0)
            inactive = getattr(mem, "inactive", 0)
            return active, inactive
        except:
            pass
    return 0, 0

# v341 God Tier Helpers
def get_system_cpu_stats():
    if psutil:
        try:
            stats = psutil.cpu_stats()
            return stats.interrupts, stats.soft_interrupts, stats.syscalls
        except:
            pass
    return 0, 0, 0

def get_process_memory_advanced():
    if _process:
        try:
            mem = _process.memory_info()
            shared = getattr(mem, "shared", 0)
            text = getattr(mem, "text", 0)
            data = getattr(mem, "data", 0)
            return shared, text, data
        except:
            pass
    return 0, 0, 0

def get_process_num_threads():
    if _process:
        try:
            return _process.num_threads()
        except:
            pass
    return 0

# v342 Ascension Singularity Helpers
def get_system_cpu_times_advanced():
    if psutil:
        try:
            times = psutil.cpu_times_percent(interval=None)
            steal = getattr(times, "steal", 0.0)
            guest = getattr(times, "guest", 0.0)
            return steal, guest
        except:
            pass
    return 0.0, 0.0

def get_system_memory_extended_plus():
    if psutil:
        try:
            mem = psutil.virtual_memory()
            buffers = getattr(mem, "buffers", 0)
            cached = getattr(mem, "cached", 0)
            return buffers, cached
        except:
            pass
    return 0, 0

def get_system_disk_partitions_count():
    if psutil:
        try:
            return len(psutil.disk_partitions())
        except:
            pass
    return 0

def get_system_users_count():
    if psutil:
        try:
            return len(psutil.users())
        except:
            pass
    return 0

def get_process_children_count():
    if _process:
        try:
            return len(_process.children())
        except:
            pass
    return 0

# v343 Beyond Singularity Helpers
def get_system_cpu_times_beyond():
    if psutil:
        try:
            times = psutil.cpu_times_percent(interval=None)
            iowait = getattr(times, "iowait", 0.0)
            irq = getattr(times, "irq", 0.0)
            softirq = getattr(times, "softirq", 0.0)
            return iowait, irq, softirq
        except:
            pass
    return 0.0, 0.0, 0.0

def get_system_memory_beyond():
    if psutil:
        try:
            mem = psutil.virtual_memory()
            slab = getattr(mem, "slab", 0)
            return slab
        except:
            pass
    return 0

def get_process_memory_beyond():
    if _process:
        try:
            mem = _process.memory_info()
            lib = getattr(mem, "lib", 0)
            dirty = getattr(mem, "dirty", 0)
            return lib, dirty
        except:
            pass
    return 0, 0

def get_process_env_var_count():
    if _process:
        try:
            return len(_process.environ())
        except:
            pass
    return 0

# v344 Transcendence Helpers
def get_process_memory_uss():
    if _process:
        try:
            if hasattr(_process, "memory_full_info"):
                return _process.memory_full_info().uss
        except:
            pass
    return 0

def get_system_memory_wired():
    if psutil:
        try:
            mem = psutil.virtual_memory()
            return getattr(mem, "wired", 0)
        except:
            pass
    return 0

def get_process_nice():
    if _process:
        try:
            return _process.nice()
        except:
            pass
    return 0

# v345 Omnipotence Helpers
def get_system_cpu_stats_advanced():
    if psutil:
        try:
            return psutil.cpu_stats().ctx_switches
        except:
            pass
    return 0

def get_system_network_connections_count():
    if psutil:
        try:
            return len(psutil.net_connections(kind='all'))
        except:
            pass
    return 0

def get_process_cpu_affinity_count():
    if _process:
        try:
            if hasattr(_process, "cpu_affinity"):
                return len(_process.cpu_affinity())
        except:
            pass
    return 0

def get_process_memory_page_faults_total():
    minor, major = get_page_faults()
    return minor + major

# v346 Deification Helpers
def get_system_disk_io_counts():
    if psutil:
        try:
            io = psutil.disk_io_counters()
            if io:
                return io.read_count, io.write_count
        except:
            pass
    return 0, 0

def get_system_swap_io():
    if psutil:
        try:
            swap = psutil.swap_memory()
            return swap.sin, swap.sout
        except:
            pass
    return 0, 0

def get_process_memory_vms_percent():
    if _process and psutil:
        try:
            vms = _process.memory_info().vms
            total = psutil.virtual_memory().total
            if total > 0:
                return (vms / total) * 100
        except:
            pass
    return 0.0

def get_system_cpu_physical_count():
    if psutil:
        try:
            return psutil.cpu_count(logical=False) or 0
        except:
            pass
    return 0

# v347 Singularity Ascension Helpers
def get_system_memory_percent_total():
    if psutil:
        try:
            return psutil.virtual_memory().percent
        except:
            pass
    return 0.0

def get_process_open_files_count():
    if _process:
        try:
            return len(_process.open_files())
        except:
            pass
    return 0

def get_system_disk_busy_time():
    if psutil:
        try:
            io = psutil.disk_io_counters()
            return getattr(io, "busy_time", 0)
        except:
            pass
    return 0

def get_system_network_interfaces_count():
    if psutil:
        try:
            return len(psutil.net_if_addrs())
        except:
            pass
    return 0

def get_process_threads_times_total():
    if _process:
        try:
            user_total = 0.0
            system_total = 0.0
            for t in _process.threads():
                user_total += t.user_time
                system_total += t.system_time
            return user_total, system_total
        except:
            pass
    return 0.0, 0.0
# v348 Nirvana Helpers
def get_system_disk_io_times():
    if psutil:
        try:
            io = psutil.disk_io_counters()
            if io:
                return io.read_time, io.write_time
        except:
            pass
    return 0, 0

def get_process_memory_maps_count():
    if _process:
        try:
            return len(_process.memory_maps())
        except:
            pass
    return 0

def get_system_network_interfaces_up_count():
    if psutil:
        try:
            stats = psutil.net_if_stats()
            return sum(1 for s in stats.values() if s.isup)
        except:
            pass
    return 0

def get_process_context_switches_total():
    voluntary, involuntary = get_context_switches()
    return voluntary + involuntary

# v349 Enlightenment Helpers
def get_process_cpu_times_children():
    if _process:
        try:
            times = _process.cpu_times()
            return getattr(times, "children_user", 0.0), getattr(times, "children_system", 0.0)
        except:
            pass
    return 0.0, 0.0

def get_system_network_interfaces_down_count():
    if psutil:
        try:
            stats = psutil.net_if_stats()
            return sum(1 for s in stats.values() if not s.isup)
        except:
            pass
    return 0

def get_system_disk_io_merged():
    if psutil:
        try:
            io = psutil.disk_io_counters()
            if io:
                return getattr(io, "read_merged_count", 0), getattr(io, "write_merged_count", 0)
        except:
            pass
    return 0, 0

# v350 Apotheosis Helpers
def get_system_memory_shared():
    if psutil:
        try:
            return getattr(psutil.virtual_memory(), "shared", 0)
        except:
            pass
    return 0

def get_process_memory_pss():
    if _process:
        try:
            if hasattr(_process, "memory_full_info"):
                return getattr(_process.memory_full_info(), "pss", 0)
        except:
            pass
    return 0

def get_system_network_interfaces_mtu_total():
    if psutil:
        try:
            stats = psutil.net_if_stats()
            return sum(s.mtu for s in stats.values())
        except:
            pass
    return 0

def get_process_memory_swap():
    if _process:
        try:
            if hasattr(_process, "memory_full_info"):
                return getattr(_process.memory_full_info(), "swap", 0)
        except:
            pass
    return 0

def get_system_network_errors_total():
    if psutil:
        try:
            io = psutil.net_io_counters()
            return io.errin + io.errout + io.dropin + io.dropout
        except:
            pass
    return 0

# v351 Ultima Helpers
def get_system_network_speed_total():
    if psutil:
        try:
            stats = psutil.net_if_stats()
            return sum(s.speed for s in stats.values() if s.speed > 0)
        except:
            pass
    return 0

def get_system_network_duplex_full_count():
    if psutil:
        try:
            stats = psutil.net_if_stats()
            # NIC_DUPLEX_FULL is 2
            return sum(1 for s in stats.values() if getattr(s, "duplex", 0) == 2)
        except:
            pass
    return 0

def get_process_memory_uss_percent():
    if _process and psutil:
        try:
            uss = get_process_memory_uss()
            total = psutil.virtual_memory().total
            if total > 0:
                return (uss / total) * 100
        except:
            pass
    return 0.0

# v352 Omnipresence Helpers
def get_process_memory_pss_percent():
    if _process and psutil:
        try:
            pss = get_process_memory_pss()
            total = psutil.virtual_memory().total
            if total > 0:
                return (pss / total) * 100
        except:
            pass
    return 0.0

def get_system_process_count():
    if psutil:
        try:
            return len(psutil.pids())
        except:
            pass
    return 0

def get_system_memory_available_percent():
    if psutil:
        try:
            mem = psutil.virtual_memory()
            if mem.total > 0:
                return (mem.available / mem.total) * 100
        except:
            pass
    return 0.0

# v353 THE SOURCE Helpers
def get_system_cpu_cores_usage():
    if psutil:
        try:
            return psutil.cpu_percent(interval=None, percpu=True)
        except:
            pass
    return []

def get_system_disk_partitions_usage():
    if psutil:
        try:
            usage = {}
            for part in psutil.disk_partitions(all=False):
                if os.name == 'nt':
                    if 'cdrom' in part.opts or part.fstype == '':
                        continue
                try:
                    usage[part.mountpoint] = psutil.disk_usage(part.mountpoint).percent
                except:
                    continue
            return usage
        except:
            pass
    return {}

# v354 THE ONE Helpers
def get_process_resource_limits():
    limits = {}
    if resource:
        try:
            nofile_soft, nofile_hard = resource.getrlimit(resource.RLIMIT_NOFILE)
            limits["nofile_soft"] = nofile_soft
            limits["nofile_hard"] = nofile_hard
            
            as_soft, as_hard = resource.getrlimit(resource.RLIMIT_AS)
            limits["as_soft"] = as_soft
            limits["as_hard"] = as_hard
        except:
            pass
    return limits


def get_uptime_human(seconds: float) -> str:
    days, rem = divmod(int(seconds), 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    parts = []
    if days > 0: parts.append(f"{days}d")
    if hours > 0: parts.append(f"{hours}h")
    if minutes > 0: parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)

async def get_health_data():
    load_avg = os.getloadavg() if hasattr(os, "getloadavg") else (0, 0, 0)
    SYSTEM_LOAD_1M.set(load_avg[0])
    SYSTEM_LOAD_5M.set(load_avg[1])
    SYSTEM_LOAD_15M.set(load_avg[2])

    # Calculate totals from metrics
    ws_received_count = 0
    for m in WS_MESSAGES_RECEIVED_TOTAL.collect():
        for s in m.samples:
            if s.name.endswith("_total"):
                ws_received_count += s.value
                
    ws_sent_count = 0
    for m in WS_MESSAGES_SENT_TOTAL.collect():
        for s in m.samples:
            if s.name.endswith("_total"):
                ws_sent_count += s.value

    ws_bytes_received = int(WS_BYTES_RECEIVED_TOTAL._value.get())
    ws_bytes_sent = int(WS_BYTES_SENT_TOTAL._value.get())

    # Calculate throughput
    now = time.time()
    last_time = getattr(app.state, "last_throughput_time", APP_START_TIME)
    last_received = getattr(app.state, "last_bytes_received", 0)
    last_sent = getattr(app.state, "last_bytes_sent", 0)
    
    dt = now - last_time
    if dt >= 1.0:
        throughput_received = (ws_bytes_received - last_received) / dt
        throughput_sent = (ws_bytes_sent - last_sent) / dt
        WS_THROUGHPUT_RECEIVED_BPS.set(throughput_received)
        WS_THROUGHPUT_SENT_BPS.set(throughput_sent)
        app.state.last_throughput_time = now
        app.state.last_bytes_received = ws_bytes_received
        app.state.last_bytes_sent = ws_bytes_sent
    else:
        throughput_received = int(WS_THROUGHPUT_RECEIVED_BPS._value.get())
        throughput_sent = int(WS_THROUGHPUT_SENT_BPS._value.get())

    uptime_seconds = time.time() - APP_START_TIME
    SYSTEM_UPTIME.set(time.time() - (psutil.boot_time() if psutil else APP_START_TIME))

    mem_percent = get_memory_percent()
    MEMORY_PERCENT.set(mem_percent)
    cpu_percent = get_cpu_percent()
    CPU_USAGE_PERCENT.set(cpu_percent)
    open_fds = get_open_fds()
    OPEN_FDS.set(open_fds)
    thread_count = threading.active_count()
    THREAD_COUNT.set(thread_count)
    
    voluntary_ctx, involuntary_ctx = get_context_switches()
    CONTEXT_SWITCHES_VOLUNTARY.set(voluntary_ctx)
    CONTEXT_SWITCHES_INVOLUNTARY.set(involuntary_ctx)

    disk_usage = get_disk_usage_percent()
    DISK_USAGE_PERCENT.set(disk_usage)
    sys_mem_avail, sys_mem_total = get_system_memory_info()
    SYSTEM_MEMORY_AVAILABLE.set(sys_mem_avail)
    SYSTEM_MEMORY_TOTAL.set(sys_mem_total)
    minor_pf, major_pf = get_page_faults()
    PAGE_FAULTS_MINOR.set(minor_pf)
    PAGE_FAULTS_MAJOR.set(major_pf)

    # v335 metrics
    cpu_count = psutil.cpu_count() if psutil else os.cpu_count()
    SYSTEM_CPU_COUNT.set(cpu_count)
    boot_time = psutil.boot_time() if psutil else 0
    SYSTEM_BOOT_TIME.set(boot_time)
    swap_percent = get_swap_memory_percent()
    SWAP_MEMORY_USAGE_PERCENT.set(swap_percent)
    net_sent, net_recv = get_network_io()
    SYSTEM_NETWORK_BYTES_SENT.set(net_sent)
    SYSTEM_NETWORK_BYTES_RECV.set(net_recv)
    
    # v336 metrics
    cpu_freq = get_cpu_frequency()
    SYSTEM_CPU_FREQUENCY.set(cpu_freq)
    disk_read, disk_write = get_disk_io()
    SYSTEM_DISK_READ_BYTES.set(disk_read)
    SYSTEM_DISK_WRITE_BYTES.set(disk_write)
    proc_conn_count = get_process_connections_count()
    PROCESS_CONNECTIONS_COUNT.set(proc_conn_count)

    # v337 metrics
    rss, vms = get_process_memory_bytes()
    PROCESS_MEMORY_RSS.set(rss)
    PROCESS_MEMORY_VMS.set(vms)
    user_cpu, sys_cpu = get_system_cpu_usage_breakdown()
    SYSTEM_CPU_USAGE_USER.set(user_cpu)
    SYSTEM_CPU_USAGE_SYSTEM.set(sys_cpu)


    # v338 metrics
    idle_p = get_system_cpu_idle_percent()
    SYSTEM_CPU_USAGE_IDLE.set(idle_p)
    proc_user_cpu, proc_sys_cpu = get_process_cpu_times_total()
    PROCESS_CPU_USAGE_USER.set(proc_user_cpu)
    PROCESS_CPU_USAGE_SYSTEM.set(proc_sys_cpu)
    sys_mem_used, sys_mem_free = get_system_memory_extended()
    SYSTEM_MEMORY_USED.set(sys_mem_used)
    SYSTEM_MEMORY_FREE.set(sys_mem_free)
    sys_net_psent, sys_net_precv = get_system_network_packets()
    SYSTEM_NETWORK_PACKETS_SENT.set(sys_net_psent)
    SYSTEM_NETWORK_PACKETS_RECV.set(sys_net_precv)

    # v339 metrics
    sys_swap_used, sys_swap_free = get_system_swap_extended()
    SYSTEM_SWAP_USED_BYTES.set(sys_swap_used)
    SYSTEM_SWAP_FREE_BYTES.set(sys_swap_free)
    p_io_rb, p_io_wb, p_io_rc, p_io_wc = get_process_io_counters()
    PROCESS_IO_READ_BYTES.set(p_io_rb)
    PROCESS_IO_WRITE_BYTES.set(p_io_wb)
    PROCESS_IO_READ_COUNT.set(p_io_rc)
    PROCESS_IO_WRITE_COUNT.set(p_io_wc)

    # v340 metrics
    p_cpu_p = get_process_cpu_percent()
    PROCESS_CPU_PERCENT_TOTAL.set(p_cpu_p)
    n_errin, n_errout, n_dropin, n_dropout = get_system_network_advanced()
    SYSTEM_NETWORK_ERRORS_IN.set(n_errin)
    SYSTEM_NETWORK_ERRORS_OUT.set(n_errout)
    SYSTEM_NETWORK_DROPS_IN.set(n_dropin)
    SYSTEM_NETWORK_DROPS_OUT.set(n_dropout)
    m_active, m_inactive = get_system_memory_advanced()
    SYSTEM_MEMORY_ACTIVE_BYTES.set(m_active)
    SYSTEM_MEMORY_INACTIVE_BYTES.set(m_inactive)

    # v341 metrics
    s_ints, s_sints, s_sysc = get_system_cpu_stats()
    SYSTEM_CPU_INTERRUPTS.set(s_ints)
    SYSTEM_CPU_SOFT_INTERRUPTS.set(s_sints)
    SYSTEM_CPU_SYSCALLS.set(s_sysc)
    p_shared, p_text, p_data = get_process_memory_advanced()
    PROCESS_MEMORY_SHARED_BYTES.set(p_shared)
    PROCESS_MEMORY_TEXT_BYTES.set(p_text)
    PROCESS_MEMORY_DATA_BYTES.set(p_data)
    p_num_threads = get_process_num_threads()
    PROCESS_NUM_THREADS.set(p_num_threads)

    # v342 metrics
    s_steal, s_guest = get_system_cpu_times_advanced()
    SYSTEM_CPU_STEAL.set(s_steal)
    SYSTEM_CPU_GUEST.set(s_guest)
    m_buffers, m_cached = get_system_memory_extended_plus()
    SYSTEM_MEMORY_BUFFERS.set(m_buffers)
    SYSTEM_MEMORY_CACHED.set(m_cached)
    d_part_count = get_system_disk_partitions_count()
    SYSTEM_DISK_PARTITIONS_COUNT.set(d_part_count)
    u_count = get_system_users_count()
    SYSTEM_USERS_COUNT.set(u_count)
    p_children_count = get_process_children_count()
    PROCESS_CHILDREN_COUNT.set(p_children_count)

    # v343 metrics
    s_iowait, s_irq, s_softirq = get_system_cpu_times_beyond()
    SYSTEM_CPU_IOWAIT.set(s_iowait)
    SYSTEM_CPU_IRQ.set(s_irq)
    SYSTEM_CPU_SOFTIRQ.set(s_softirq)
    m_slab = get_system_memory_beyond()
    SYSTEM_MEMORY_SLAB.set(m_slab)
    p_lib, p_dirty = get_process_memory_beyond()
    PROCESS_MEMORY_LIB.set(p_lib)
    PROCESS_MEMORY_DIRTY.set(p_dirty)
    p_env_count = get_process_env_var_count()
    PROCESS_ENV_VAR_COUNT.set(p_env_count)

    # v344 metrics
    p_uss = get_process_memory_uss()
    PROCESS_MEMORY_USS.set(p_uss)
    m_wired = get_system_memory_wired()
    SYSTEM_MEMORY_WIRED.set(m_wired)
    p_nice = get_process_nice()
    PROCESS_NICE.set(p_nice)
    PROCESS_UPTIME.set(uptime_seconds)

    # v345 metrics
    s_ctx = get_system_cpu_stats_advanced()
    SYSTEM_CPU_CTX_SWITCHES.set(s_ctx)
    s_conn_count = get_system_network_connections_count()
    SYSTEM_NETWORK_CONNECTIONS.set(s_conn_count)
    p_affinity = get_process_cpu_affinity_count()
    PROCESS_CPU_AFFINITY.set(p_affinity)
    p_pf_total = get_process_memory_page_faults_total()
    PROCESS_MEMORY_PAGE_FAULTS_TOTAL.set(p_pf_total)

    # v346 metrics
    sd_rc, sd_wc = get_system_disk_io_counts()
    SYSTEM_DISK_READ_COUNT_TOTAL.set(sd_rc)
    SYSTEM_DISK_WRITE_COUNT_TOTAL.set(sd_wc)
    ss_sin, ss_sout = get_system_swap_io()
    SYSTEM_SWAP_IN_BYTES_TOTAL.set(ss_sin)
    SYSTEM_SWAP_OUT_BYTES_TOTAL.set(ss_sout) # fixed naming
    p_vms_p = get_process_memory_vms_percent()
    PROCESS_MEMORY_VMS_PERCENT.set(p_vms_p)
    s_cpu_phys = get_system_cpu_physical_count()
    SYSTEM_CPU_PHYSICAL_COUNT.set(s_cpu_phys)

    # v347 metrics
    sm_percent = get_system_memory_percent_total()
    SYSTEM_MEMORY_PERCENT.set(sm_percent)
    p_open_files = get_process_open_files_count()
    PROCESS_OPEN_FILES_COUNT.set(p_open_files)
    sd_busy = get_system_disk_busy_time()
    SYSTEM_DISK_BUSY_TIME_MS.set(sd_busy)
    sn_if_count = get_system_network_interfaces_count()
    SYSTEM_NETWORK_INTERFACES_COUNT.set(sn_if_count)
    pt_user, pt_sys = get_process_threads_times_total()
    PROCESS_THREADS_TOTAL_TIME_USER.set(pt_user)
    PROCESS_THREADS_TOTAL_TIME_SYSTEM.set(pt_sys)

    # v348 metrics
    sd_rt, sd_wt = get_system_disk_io_times()
    SYSTEM_DISK_READ_TIME_MS.set(sd_rt)
    SYSTEM_DISK_WRITE_TIME_MS.set(sd_wt)
    p_mem_maps = get_process_memory_maps_count()
    PROCESS_MEMORY_MAPS_COUNT.set(p_mem_maps)
    sn_if_up = get_system_network_interfaces_up_count()
    SYSTEM_NETWORK_INTERFACES_UP_COUNT.set(sn_if_up)
    p_ctx_total = get_process_context_switches_total()
    PROCESS_CONTEXT_SWITCHES_TOTAL.set(p_ctx_total)

    # v349 metrics
    p_child_u, p_child_s = get_process_cpu_times_children()
    PROCESS_CPU_TIMES_CHILDREN_USER.set(p_child_u)
    PROCESS_CPU_TIMES_CHILDREN_SYSTEM.set(p_child_s)
    sn_if_down = get_system_network_interfaces_down_count()
    SYSTEM_NETWORK_INTERFACES_DOWN_COUNT.set(sn_if_down)
    sd_rm, sd_wm = get_system_disk_io_merged()
    SYSTEM_DISK_READ_MERGED_COUNT.set(sd_rm)
    SYSTEM_DISK_WRITE_MERGED_COUNT.set(sd_wm)

    # v350 metrics
    m_shared = get_system_memory_shared()
    SYSTEM_MEMORY_SHARED_BYTES.set(m_shared)
    p_pss = get_process_memory_pss()
    PROCESS_MEMORY_PSS_BYTES.set(p_pss)
    sn_mtu_total = get_system_network_interfaces_mtu_total()
    SYSTEM_NETWORK_INTERFACES_MTU_TOTAL.set(sn_mtu_total)
    p_swap = get_process_memory_swap()
    PROCESS_MEMORY_SWAP_BYTES.set(p_swap)
    sn_err_total = get_system_network_errors_total()
    SYSTEM_NETWORK_ERRORS_TOTAL.set(sn_err_total)

    # v351 metrics
    sn_speed_total = get_system_network_speed_total()
    SYSTEM_NETWORK_INTERFACES_SPEED_TOTAL_MBPS.set(sn_speed_total)
    sn_duplex_full = get_system_network_duplex_full_count()
    SYSTEM_NETWORK_INTERFACES_DUPLEX_FULL_COUNT.set(sn_duplex_full)
    p_uss_p = get_process_memory_uss_percent()
    PROCESS_MEMORY_USS_PERCENT.set(p_uss_p)

    # v352 metrics
    p_pss_p = get_process_memory_pss_percent()
    PROCESS_MEMORY_PSS_PERCENT.set(p_pss_p)
    s_proc_count = get_system_process_count()
    SYSTEM_PROCESS_COUNT.set(s_proc_count)
    s_load_1m_p = (load_avg[0] / cpu_count * 100) if cpu_count > 0 else 0.0
    SYSTEM_CPU_LOAD_1M_PERCENT.set(s_load_1m_p)
    sm_avail_p = get_system_memory_available_percent()
    SYSTEM_MEMORY_AVAILABLE_PERCENT.set(sm_avail_p)

    # v353 metrics
    cpu_cores_p = get_system_cpu_cores_usage()
    for i, p in enumerate(cpu_cores_p):
        SYSTEM_CPU_CORES_USAGE_PERCENT.labels(core=str(i)).set(p)
    
    disk_p_u = get_system_disk_partitions_usage()
    for part, p in disk_p_u.items():
        SYSTEM_DISK_PARTITIONS_USAGE_PERCENT.labels(partition=part).set(p)
        
    net_io_per_nic = get_system_network_io_per_nic()
    for nic, io in net_io_per_nic.items():
        SYSTEM_NETWORK_INTERFACES_BYTES_SENT.labels(interface=nic).set(io.bytes_sent)
        SYSTEM_NETWORK_INTERFACES_BYTES_RECV.labels(interface=nic).set(io.bytes_recv)

    # v354 THE ONE
    s_load_5m_p = (load_avg[1] / cpu_count * 100) if cpu_count > 0 else 0.0
    s_load_15m_p = (load_avg[2] / cpu_count * 100) if cpu_count > 0 else 0.0
    SYSTEM_LOAD_5M_PERCENT.set(s_load_5m_p)
    SYSTEM_LOAD_15M_PERCENT.set(s_load_15m_p)
    
    p_limits = get_process_resource_limits()
    if "nofile_soft" in p_limits:
        PROCESS_LIMIT_NOFILE_SOFT.set(p_limits["nofile_soft"])
        PROCESS_LIMIT_NOFILE_HARD.set(p_limits["nofile_hard"])
        PROCESS_LIMIT_AS_SOFT.set(p_limits["as_soft"])
        PROCESS_LIMIT_AS_HARD.set(p_limits["as_hard"])

    # v355 THE SINGULARITY
    nofile_util = (open_fds / p_limits["nofile_soft"] * 100) if "nofile_soft" in p_limits and p_limits["nofile_soft"] > 0 else 0.0
    PROCESS_LIMIT_NOFILE_UTILIZATION_PERCENT.set(nofile_util)
    
    as_util = (vms / p_limits["as_soft"] * 100) if "as_soft" in p_limits and p_limits["as_soft"] > 0 else 0.0
    PROCESS_LIMIT_AS_UTILIZATION_PERCENT.set(as_util)

    # v356 THE OMEGA
    last_io_time = getattr(app.state, "last_io_time", APP_START_TIME)
    last_p_rb = getattr(app.state, "last_proc_read_bytes", 0)
    last_p_wb = getattr(app.state, "last_proc_write_bytes", 0)
    
    io_dt = now - last_io_time
    if io_dt >= 1.0:
        p_io_read_bps = (p_io_rb - last_p_rb) / io_dt
        p_io_write_bps = (p_io_wb - last_p_wb) / io_dt
        PROCESS_IO_READ_THROUGHPUT_BPS.set(p_io_read_bps)
        PROCESS_IO_WRITE_THROUGHPUT_BPS.set(p_io_write_bps)
        app.state.last_io_time = now
        app.state.last_proc_read_bytes = p_io_rb
        app.state.last_proc_write_bytes = p_io_wb
    else:
        p_io_read_bps = int(PROCESS_IO_READ_THROUGHPUT_BPS._value.get())
        p_io_write_bps = int(PROCESS_IO_WRITE_THROUGHPUT_BPS._value.get())

    active_tasks_list = await registry.list_active_tasks()
    tools_summary = {}
    for t in active_tasks_list:
        tools_summary[t["tool_name"]] = tools_summary.get(t["tool_name"], 0) + 1

    # Task success rate
    total_finished = 0
    total_success = 0
    for m in TASKS_TOTAL.collect():
        for s in m.samples:
            total_finished += s.value
            if s.labels.get("status") == "success":
                total_success += s.value
    
    success_rate = (total_success / total_finished * 100) if total_finished > 0 else 100.0

    return { 
        "status": "healthy", 
        "version": APP_VERSION, 
        "git_commit": GIT_COMMIT,
        "operational_apex": OPERATIONAL_APEX, 
        "python_version": sys.version, 
        "python_implementation": platform.python_implementation(),
        "system_platform": sys.platform, 
        "cpu_count": cpu_count,
        "cpu_physical_count": s_cpu_phys,
        "cpu_frequency_current_mhz": cpu_freq,
        "cpu_usage_percent": cpu_percent,
        "system_cpu_idle_percent": idle_p,
        "system_cpu_usage": {
            "user_percent": user_cpu,
            "system_percent": sys_cpu,
            "idle_percent": idle_p,
            "steal_percent": s_steal,
            "guest_percent": s_guest,
            "iowait_percent": s_iowait,
            "irq_percent": s_irq,
            "softirq_percent": s_softirq,
            "load_1m_percent": s_load_1m_p,
            "load_5m_percent": s_load_5m_p,
            "load_15m_percent": s_load_15m_p,
            "cores": cpu_cores_p
        },
        "system_cpu_stats": {
            "interrupts": s_ints,
            "soft_interrupts": s_sints,
            "syscalls": s_sysc,
            "context_switches": s_ctx
        },
        "thread_count": thread_count,
        "open_fds": open_fds,
        "process_open_files_count": p_open_files,
        "process_resource_limits": p_limits,
        "process_resource_utilization_percent": {
            "nofile": nofile_util,
            "as": as_util
        },
        "context_switches": {
            "voluntary": voluntary_ctx,
            "involuntary": involuntary_ctx
        },
        "page_faults": {
            "minor": minor_pf,
            "major": major_pf,
            "total": p_pf_total
        },
        "swap_memory_usage_percent": swap_percent,
        "system_swap_memory": {
            "used_bytes": sys_swap_used,
            "free_bytes": sys_swap_free,
            "sin_bytes": ss_sin,
            "sout_bytes": ss_sout
        },
        "boot_time_seconds": boot_time,
        "network_io_total": {
            "bytes_sent": net_sent,
            "bytes_recv": net_recv,
            "errin": n_errin,
            "errout": n_errout,
            "dropin": n_dropin,
            "dropout": n_dropout,
            "errors_total": sn_err_total,
            "interfaces_count": sn_if_count,
            "interfaces_up_count": sn_if_up,
            "interfaces_down_count": sn_if_down,
            "mtu_total": sn_mtu_total,
            "speed_total_mbps": sn_speed_total,
            "duplex_full_count": sn_duplex_full,
            "per_interface": {nic: {"bytes_sent": io.bytes_sent, "bytes_recv": io.bytes_recv} for nic, io in net_io_per_nic.items()}
        },
        "disk_io_total": {
            "read_bytes": disk_read,
            "write_bytes": disk_write,
            "read_count": sd_rc,
            "write_count": sd_wc,
            "read_merged_count": sd_rm,
            "write_merged_count": sd_wm,
            "busy_time_ms": sd_busy,
            "partitions_usage_percent": disk_p_u
        },
        "system_network_connections_count": s_conn_count,
        "process_connections_count": proc_conn_count,
        "system_load_1m": load_avg[0],
        "system_load_5m": load_avg[1],
        "system_load_15m": load_avg[2],
        "system_process_count": s_proc_count,
        "active_ws_connections": int(ACTIVE_WS_CONNECTIONS._value.get()),
        "peak_ws_connections": getattr(app.state, "peak_ws_connections", 0),
        "ws_messages_received": int(ws_received_count),
        "ws_messages_sent": int(ws_sent_count),
        "ws_bytes_received": ws_bytes_received,
        "ws_bytes_sent": ws_bytes_sent,
        "ws_throughput_bps": {
            "received": throughput_received,
            "sent": throughput_sent
        },
        "load_avg": load_avg,
        "disk_usage_percent": disk_usage,
        "memory_rss_bytes": rss,
        "memory_vms_bytes": vms,
        "memory_percent": mem_percent,
        "system_memory_available_bytes": sys_mem_avail, # backward compatibility
        "system_memory": {
            "available_bytes": sys_mem_avail,
            "total_bytes": sys_mem_total,
            "used_bytes": sys_mem_used,
            "free_bytes": sys_mem_free,
            "active_bytes": m_active,
            "inactive_bytes": m_inactive,
            "buffers_bytes": m_buffers,
            "cached_bytes": m_cached,
            "slab_bytes": m_slab,
            "wired_bytes": m_wired,
            "shared_bytes": m_shared,
            "percent": sm_percent,
            "available_percent": sm_avail_p
        },
        "system_memory_extended": { # backward compatibility
            "used_bytes": sys_mem_used,
            "free_bytes": sys_mem_free
        },
        "process_io_counters": {
            "read_bytes": p_io_rb,
            "write_bytes": p_io_wb,
            "read_count": p_io_rc,
            "write_count": p_io_wc,
            "read_throughput_bps": p_io_read_bps,
            "write_throughput_bps": p_io_write_bps
        },
        "process_cpu_usage": {
            "user_seconds": proc_user_cpu,
            "system_seconds": proc_sys_cpu,
            "percent": p_cpu_p,
            "affinity_count": p_affinity,
            "children_user_seconds": p_child_u,
            "children_system_seconds": p_child_s
        },
        "process_threads_cpu_usage": {
            "total_user_seconds": pt_user,
            "total_system_seconds": pt_sys
        },
        "system_disk_io_times_ms": {
            "read_time": sd_rt,
            "write_time": sd_wt
        },
        "process_memory_maps_count": p_mem_maps,
        "system_network_interfaces_up_count": sn_if_up,
        "process_context_switches_total": p_ctx_total,

        "process_memory_advanced": {
            "shared_bytes": p_shared,
            "text_bytes": p_text,
            "data_bytes": p_data,
            "lib_bytes": p_lib,
            "dirty_bytes": p_dirty,
            "uss_bytes": p_uss,
            "pss_bytes": p_pss,
            "swap_bytes": p_swap,
            "vms_percent": p_vms_p,
            "uss_percent": p_uss_p,
            "pss_percent": p_pss_p
        },
        "process_env_var_count": p_env_count,
        "process_nice_value": p_nice,
        "process_uptime_seconds": uptime_seconds,
        "process_num_threads": p_num_threads,
        "process_children_count": p_children_count,
        "system_network_packets": {
            "sent": sys_net_psent,
            "recv": sys_net_precv
        },
        "system_disk_partitions_count": d_part_count,
        "system_users_count": u_count,
        "registry_size": registry.active_task_count, 
        "peak_registry_size": registry.peak_active_tasks,
        "total_tasks_started": registry.total_tasks_started,
        "task_success_rate_percent": success_rate,
        "registry_summary": tools_summary,
        "uptime_seconds": uptime_seconds,
        "system_uptime_seconds": int(SYSTEM_UPTIME._value.get()),
        "uptime_human": get_uptime_human(uptime_seconds),
        "start_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(APP_START_TIME)), 
        "timestamp": now,
        "config": {
            "ws_heartbeat_timeout": WS_HEARTBEAT_TIMEOUT,
            "cleanup_interval": CLEANUP_INTERVAL,
            "stale_task_max_age": STALE_TASK_MAX_AGE,
            "ws_message_size_limit": WS_MESSAGE_SIZE_LIMIT,
            "max_concurrent_tasks": MAX_CONCURRENT_TASKS,
            "allowed_origins": ALLOWED_ORIGINS
        }
    }

app = FastAPI(
    title="ADK Progress Bridge",
    description="A bridge between long-running agent tools and a real-time progress TUI/Frontend.",
    version=APP_VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TaskStartRequest(BaseModel):
    args: Dict[str, Any] = {}

class TaskStartResponse(BaseModel):
    call_id: str
    stream_url: str

class InputProvideRequest(BaseModel):
    call_id: str
    value: Any

AUTH_RESPONSES = {401: {"description": "Unauthorized"}}

@app.get("/tools", response_model=List[str], responses=AUTH_RESPONSES)
async def list_tools(authenticated: bool = Depends(verify_api_key)):
    return registry.list_tools()

@app.get("/tasks", responses=AUTH_RESPONSES)
async def list_active_tasks(authenticated: bool = Depends(verify_api_key)):
    return await registry.list_active_tasks()

@app.post("/start_task/{tool_name}", response_model=TaskStartResponse, responses=AUTH_RESPONSES)
async def start_task(
    tool_name: str, 
    request: Optional[TaskStartRequest] = None, 
    authenticated: bool = Depends(verify_api_key)
):
    if registry.active_task_count >= MAX_CONCURRENT_TASKS:
        raise HTTPException(
            status_code=503, 
            detail=f"Server busy: Maximum concurrent tasks ({MAX_CONCURRENT_TASKS}) reached."
        )

    tool = registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")
    
    call_id = str(uuid.uuid4())
    args = request.args if request else {}
    
    try:
        gen = tool(**args)
        await registry.store_task(call_id, gen, tool_name)
    except Exception as e:
        logger.error(f"Error starting tool {tool_name}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    return TaskStartResponse(
        call_id=call_id,
        stream_url=f"/stream/{call_id}"
    )

@app.get("/stream/{call_id}", responses=AUTH_RESPONSES)
@app.get("/stream", responses=AUTH_RESPONSES)
async def stream_task(
    call_id: Optional[str] = None,
    cid: Optional[str] = Query(None, alias="call_id"),
    authenticated: bool = Depends(verify_api_key)
):
    actual_call_id = call_id or cid
    if not actual_call_id:
        raise HTTPException(status_code=400, detail="call_id is required")

    task_data = await registry.get_task(actual_call_id)
    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found or already being streamed")
    
    gen = task_data["gen"]
    tool_name = task_data["tool_name"]

    async def event_generator():
        call_id_var.set(actual_call_id)
        tool_name_var.set(tool_name)
        start_time = time.perf_counter()
        status = "success"
        try:
            async for item in gen:
                if isinstance(item, ProgressPayload):
                    TASK_PROGRESS_STEPS_TOTAL.labels(tool_name=tool_name).inc()
                    event = ProgressEvent(call_id=actual_call_id, type="progress", payload=item)
                elif isinstance(item, dict) and item.get("type") == "input_request":
                    event = ProgressEvent(call_id=actual_call_id, type="input_request", payload=item["payload"])
                else:
                    event = ProgressEvent(call_id=actual_call_id, type="result", payload=item)
                yield await format_sse(event)
        except asyncio.CancelledError:
            status = "cancelled"
            logger.info(f"Task {actual_call_id} was cancelled by client")
            await gen.aclose()
        except Exception as e:
            status = "error"
            logger.error(f"Error during task {actual_call_id} execution: {e}")
            error_event = ProgressEvent(call_id=actual_call_id, type="error", payload={"detail": str(e)})
            yield await format_sse(error_event)
        finally:
            duration = time.perf_counter() - start_time
            TASK_DURATION.labels(tool_name=tool_name).observe(duration)
            TASKS_TOTAL.labels(tool_name=tool_name, status=status).inc()
            await registry.remove_task(actual_call_id)
            logger.info(f"Stream finished for task: {actual_call_id} (duration: {duration:.2f}s, status: {status})")

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/provide_input", responses=AUTH_RESPONSES)
async def provide_input(request: InputProvideRequest, authenticated: bool = Depends(verify_api_key)):
    if await input_manager.provide_input(request.call_id, request.value):
        return {"status": "input accepted"}
    else:
        raise HTTPException(status_code=404, detail=f"No task waiting for input with call_id: {request.call_id}")

@app.post("/stop_task/{call_id}", responses=AUTH_RESPONSES)
@app.post("/stop_task", responses=AUTH_RESPONSES)
async def stop_task(
    call_id: Optional[str] = None, 
    cid: Optional[str] = Query(None, alias="call_id"),
    authenticated: bool = Depends(verify_api_key)
):
    actual_call_id = call_id or cid
    if not actual_call_id:
        raise HTTPException(status_code=400, detail="call_id is required")
    task_data = await registry.get_task_no_consume(actual_call_id)
    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found or already finished")
    await task_data["gen"].aclose()
    if not task_data["consumed"]:
        await registry.remove_task(actual_call_id)
    return {"status": "stop signal sent"}

@app.get("/health") 
async def health_check(): 
    return await get_health_data()

@app.get("/version") 
async def get_version(): 
    return {
        "version": APP_VERSION, 
        "git_commit": GIT_COMMIT,
        "status": OPERATIONAL_APEX, 
        "timestamp": time.time()
    } 

@app.get("/metrics")
async def metrics():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    
    # Update gauges before returning
    MEMORY_PERCENT.set(get_memory_percent())
    CPU_USAGE_PERCENT.set(get_cpu_percent())
    OPEN_FDS.set(get_open_fds())
    THREAD_COUNT.set(threading.active_count())
    v, i = get_context_switches()
    CONTEXT_SWITCHES_VOLUNTARY.set(v)
    CONTEXT_SWITCHES_INVOLUNTARY.set(i)
    DISK_USAGE_PERCENT.set(get_disk_usage_percent())
    avail, total = get_system_memory_info()
    SYSTEM_MEMORY_AVAILABLE.set(avail)
    SYSTEM_MEMORY_TOTAL.set(total)
    min_pf, maj_pf = get_page_faults()
    PAGE_FAULTS_MINOR.set(min_pf)
    PAGE_FAULTS_MAJOR.set(maj_pf)
    
    cpu_count = psutil.cpu_count() if psutil else os.cpu_count()
    SYSTEM_CPU_COUNT.set(cpu_count)
    SYSTEM_BOOT_TIME.set(psutil.boot_time() if psutil else 0)
    SWAP_MEMORY_USAGE_PERCENT.set(get_swap_memory_percent())
    net_sent, net_recv = get_network_io()
    SYSTEM_NETWORK_BYTES_SENT.set(net_sent)
    SYSTEM_NETWORK_BYTES_RECV.set(net_recv)
    
    # v336
    SYSTEM_CPU_FREQUENCY.set(get_cpu_frequency())
    disk_read, disk_write = get_disk_io()
    SYSTEM_DISK_READ_BYTES.set(disk_read)
    SYSTEM_DISK_WRITE_BYTES.set(disk_write)
    PROCESS_CONNECTIONS_COUNT.set(get_process_connections_count())
    load_avg = os.getloadavg() if hasattr(os, "getloadavg") else (0, 0, 0)
    SYSTEM_LOAD_1M.set(load_avg[0])

    # v337
    SYSTEM_LOAD_5M.set(load_avg[1])
    SYSTEM_LOAD_15M.set(load_avg[2])
    rss, vms = get_process_memory_bytes()
    PROCESS_MEMORY_RSS.set(rss)
    PROCESS_MEMORY_VMS.set(vms)
    user_cpu, sys_cpu = get_system_cpu_usage_breakdown()
    SYSTEM_CPU_USAGE_USER.set(user_cpu)
    SYSTEM_CPU_USAGE_SYSTEM.set(sys_cpu)
    SYSTEM_UPTIME.set(time.time() - (psutil.boot_time() if psutil else APP_START_TIME))

    # v338
    SYSTEM_CPU_USAGE_IDLE.set(get_system_cpu_idle_percent())
    p_user_cpu, p_sys_cpu = get_process_cpu_times_total()
    PROCESS_CPU_USAGE_USER.set(p_user_cpu)
    PROCESS_CPU_USAGE_SYSTEM.set(p_sys_cpu)
    s_used, s_free = get_system_memory_extended()
    SYSTEM_MEMORY_USED.set(s_used)
    SYSTEM_MEMORY_FREE.set(s_free)
    s_net_psent, s_net_precv = get_system_network_packets()
    SYSTEM_NETWORK_PACKETS_SENT.set(s_net_psent)
    SYSTEM_NETWORK_PACKETS_RECV.set(s_net_precv)

    # v339
    ss_used, ss_free = get_system_swap_extended()
    SYSTEM_SWAP_USED_BYTES.set(ss_used)
    SYSTEM_SWAP_FREE_BYTES.set(ss_free)
    pi_rb, pi_wb, pi_rc, pi_wc = get_process_io_counters()
    PROCESS_IO_READ_BYTES.set(pi_rb)
    PROCESS_IO_WRITE_BYTES.set(pi_wb)
    PROCESS_IO_READ_COUNT.set(pi_rc)
    PROCESS_IO_WRITE_COUNT.set(pi_wc)

    # v340
    PROCESS_CPU_PERCENT_TOTAL.set(get_process_cpu_percent())
    sn_errin, sn_errout, sn_dropin, sn_dropout = get_system_network_advanced()
    SYSTEM_NETWORK_ERRORS_IN.set(sn_errin)
    SYSTEM_NETWORK_ERRORS_OUT.set(sn_errout)
    SYSTEM_NETWORK_DROPS_IN.set(sn_dropin)
    SYSTEM_NETWORK_DROPS_OUT.set(sn_dropout)
    sm_active, sm_inactive = get_system_memory_advanced()
    SYSTEM_MEMORY_ACTIVE_BYTES.set(sm_active)
    SYSTEM_MEMORY_INACTIVE_BYTES.set(sm_inactive)

    # v341
    ints, sints, sysc = get_system_cpu_stats()
    SYSTEM_CPU_INTERRUPTS.set(ints)
    SYSTEM_CPU_SOFT_INTERRUPTS.set(sints)
    SYSTEM_CPU_SYSCALLS.set(sysc)
    pshared, ptext, pdata = get_process_memory_advanced()
    PROCESS_MEMORY_SHARED_BYTES.set(pshared)
    PROCESS_MEMORY_TEXT_BYTES.set(ptext)
    PROCESS_MEMORY_DATA_BYTES.set(pdata)
    PROCESS_NUM_THREADS.set(get_process_num_threads())

    # v342
    steal, guest = get_system_cpu_times_advanced()
    SYSTEM_CPU_STEAL.set(steal)
    SYSTEM_CPU_GUEST.set(guest)
    mbuff, mcach = get_system_memory_extended_plus()
    SYSTEM_MEMORY_BUFFERS.set(mbuff)
    SYSTEM_MEMORY_CACHED.set(mcach)
    SYSTEM_DISK_PARTITIONS_COUNT.set(get_system_disk_partitions_count())
    SYSTEM_USERS_COUNT.set(get_system_users_count())
    PROCESS_CHILDREN_COUNT.set(get_process_children_count())

    # v343 Beyond Singularity
    bw_iowait, bw_irq, bw_softirq = get_system_cpu_times_beyond()
    SYSTEM_CPU_IOWAIT.set(bw_iowait)
    SYSTEM_CPU_IRQ.set(bw_irq)
    SYSTEM_CPU_SOFTIRQ.set(bw_softirq)
    SYSTEM_MEMORY_SLAB.set(get_system_memory_beyond())
    bw_lib, bw_dirty = get_process_memory_beyond()
    PROCESS_MEMORY_LIB.set(bw_lib)
    PROCESS_MEMORY_DIRTY.set(bw_dirty)
    PROCESS_ENV_VAR_COUNT.set(get_process_env_var_count())

    # v344 Transcendence
    PROCESS_MEMORY_USS.set(get_process_memory_uss())
    SYSTEM_MEMORY_WIRED.set(get_system_memory_wired())
    PROCESS_NICE.set(get_process_nice())
    PROCESS_UPTIME.set(time.time() - APP_START_TIME)

    # v345 Omnipotence
    SYSTEM_CPU_CTX_SWITCHES.set(get_system_cpu_stats_advanced())
    SYSTEM_NETWORK_CONNECTIONS.set(get_system_network_connections_count())
    PROCESS_CPU_AFFINITY.set(get_process_cpu_affinity_count())
    PROCESS_MEMORY_PAGE_FAULTS_TOTAL.set(get_process_memory_page_faults_total())

    # v346 Deification
    sd_read_c, sd_write_c = get_system_disk_io_counts()
    SYSTEM_DISK_READ_COUNT_TOTAL.set(sd_read_c)
    SYSTEM_DISK_WRITE_COUNT_TOTAL.set(sd_write_c)
    ss_swap_in, ss_swap_out = get_system_swap_io()
    SYSTEM_SWAP_IN_BYTES_TOTAL.set(ss_swap_in)
    SYSTEM_SWAP_OUT_BYTES_TOTAL.set(ss_swap_out)
    PROCESS_MEMORY_VMS_PERCENT.set(get_process_memory_vms_percent())
    SYSTEM_CPU_PHYSICAL_COUNT.set(get_system_cpu_physical_count())

    # v347 Singularity Ascension
    SYSTEM_MEMORY_PERCENT.set(get_system_memory_percent_total())
    PROCESS_OPEN_FILES_COUNT.set(get_process_open_files_count())
    SYSTEM_DISK_BUSY_TIME_MS.set(get_system_disk_busy_time())
    SYSTEM_NETWORK_INTERFACES_COUNT.set(get_system_network_interfaces_count())
    pu, ps = get_process_threads_times_total()
    PROCESS_THREADS_TOTAL_TIME_USER.set(pu)
    PROCESS_THREADS_TOTAL_TIME_SYSTEM.set(ps)

    # v348 Nirvana
    n_sd_rt, n_sd_wt = get_system_disk_io_times()
    SYSTEM_DISK_READ_TIME_MS.set(n_sd_rt)
    SYSTEM_DISK_WRITE_TIME_MS.set(n_sd_wt)
    PROCESS_MEMORY_MAPS_COUNT.set(get_process_memory_maps_count())
    SYSTEM_NETWORK_INTERFACES_UP_COUNT.set(get_system_network_interfaces_up_count())
    PROCESS_CONTEXT_SWITCHES_TOTAL.set(get_process_context_switches_total())

    # v349 Enlightenment
    e_p_child_u, e_p_child_s = get_process_cpu_times_children()
    PROCESS_CPU_TIMES_CHILDREN_USER.set(e_p_child_u)
    PROCESS_CPU_TIMES_CHILDREN_SYSTEM.set(e_p_child_s)
    SYSTEM_NETWORK_INTERFACES_DOWN_COUNT.set(get_system_network_interfaces_down_count())
    e_sd_rm, e_sd_wm = get_system_disk_io_merged()
    SYSTEM_DISK_READ_MERGED_COUNT.set(e_sd_rm)
    SYSTEM_DISK_WRITE_MERGED_COUNT.set(e_sd_wm)

    # v350 Apotheosis
    SYSTEM_MEMORY_SHARED_BYTES.set(get_system_memory_shared())
    PROCESS_MEMORY_PSS_BYTES.set(get_process_memory_pss())
    SYSTEM_NETWORK_INTERFACES_MTU_TOTAL.set(get_system_network_interfaces_mtu_total())
    PROCESS_MEMORY_SWAP_BYTES.set(get_process_memory_swap())
    SYSTEM_NETWORK_ERRORS_TOTAL.set(get_system_network_errors_total())

    # v351 Ultima
    SYSTEM_NETWORK_INTERFACES_SPEED_TOTAL_MBPS.set(get_system_network_speed_total())
    SYSTEM_NETWORK_INTERFACES_DUPLEX_FULL_COUNT.set(get_system_network_duplex_full_count())
    PROCESS_MEMORY_USS_PERCENT.set(get_process_memory_uss_percent())

    # v352 Omnipresence
    SYSTEM_PROCESS_COUNT.set(get_system_process_count())
    PROCESS_MEMORY_PSS_PERCENT.set(get_process_memory_pss_percent())
    SYSTEM_CPU_LOAD_1M_PERCENT.set((load_avg[0] / cpu_count * 100) if cpu_count > 0 else 0.0)
    SYSTEM_MEMORY_AVAILABLE_PERCENT.set(get_system_memory_available_percent())

    # v353 THE SOURCE
    cpu_cores_p = get_system_cpu_cores_usage()
    for i, p in enumerate(cpu_cores_p):
        SYSTEM_CPU_CORES_USAGE_PERCENT.labels(core=str(i)).set(p)
    
    disk_p_u = get_system_disk_partitions_usage()
    for part, p in disk_p_u.items():
        SYSTEM_DISK_PARTITIONS_USAGE_PERCENT.labels(partition=part).set(p)
        
    net_io_per_nic = get_system_network_io_per_nic()
    for nic, io in net_io_per_nic.items():
        SYSTEM_NETWORK_INTERFACES_BYTES_SENT.labels(interface=nic).set(io.bytes_sent)
        SYSTEM_NETWORK_INTERFACES_BYTES_RECV.labels(interface=nic).set(io.bytes_recv)

    # v354 THE ONE
    SYSTEM_LOAD_5M_PERCENT.set((load_avg[1] / cpu_count * 100) if cpu_count > 0 else 0.0)
    SYSTEM_LOAD_15M_PERCENT.set((load_avg[2] / cpu_count * 100) if cpu_count > 0 else 0.0)
    p_limits = get_process_resource_limits()
    if "nofile_soft" in p_limits:
        PROCESS_LIMIT_NOFILE_SOFT.set(p_limits["nofile_soft"])
        PROCESS_LIMIT_NOFILE_HARD.set(p_limits["nofile_hard"])
        PROCESS_LIMIT_AS_SOFT.set(p_limits["as_soft"])
        PROCESS_LIMIT_AS_HARD.set(p_limits["as_hard"])

    # v355 THE SINGULARITY
    open_fds = get_open_fds()
    if "nofile_soft" in p_limits and p_limits["nofile_soft"] > 0:
        PROCESS_LIMIT_NOFILE_UTILIZATION_PERCENT.set((open_fds / p_limits["nofile_soft"]) * 100)
    
    if "as_soft" in p_limits and p_limits["as_soft"] > 0:
        rss, vms = get_process_memory_bytes()
        PROCESS_LIMIT_AS_UTILIZATION_PERCENT.set((vms / p_limits["as_soft"]) * 100)

    # v356 THE OMEGA
    now = time.time()
    last_io_time = getattr(app.state, "last_io_time", APP_START_TIME)
    p_io_rb, p_io_wb, _, _ = get_process_io_counters()
    last_p_rb = getattr(app.state, "last_proc_read_bytes", 0)
    last_p_wb = getattr(app.state, "last_proc_write_bytes", 0)
    
    io_dt = now - last_io_time
    if io_dt >= 1.0:
        p_io_read_bps = (p_io_rb - last_p_rb) / io_dt
        p_io_write_bps = (p_io_wb - last_p_wb) / io_dt
        PROCESS_IO_READ_THROUGHPUT_BPS.set(p_io_read_bps)
        PROCESS_IO_WRITE_THROUGHPUT_BPS.set(p_io_write_bps)
        app.state.last_io_time = now
        app.state.last_proc_read_bytes = p_io_rb
        app.state.last_proc_write_bytes = p_io_wb
    
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    conn_start_time = time.perf_counter()
    ACTIVE_WS_CONNECTIONS.inc()
    
    # Update peak connections
    current_ws = int(ACTIVE_WS_CONNECTIONS._value.get())
    if current_ws > getattr(app.state, "peak_ws_connections", 0):
        app.state.peak_ws_connections = current_ws
        PEAK_ACTIVE_WS_CONNECTIONS.set(current_ws)
        
    active_tasks: Dict[str, asyncio.Task] = {}
    try:
        try:
            await verify_api_key_ws(websocket)
        except HTTPException:
            return

        logger.info("WebSocket connection established")
        send_lock = asyncio.Lock()

        async def safe_send_json(data: dict):
            async with send_lock:
                try:
                    msg_type = data.get("type", "unknown")
                    WS_MESSAGES_SENT_TOTAL.labels(message_type=msg_type).inc()
                    json_str = json.dumps(data)
                    WS_BYTES_SENT_TOTAL.inc(len(json_str))
                    await websocket.send_text(json_str)
                except Exception as e:
                    logger.error(f"Error sending WS message: {e}")
                    raise

        while True:
            try:
                # Use raw receive to handle both text and binary frames gracefully
                msg = await asyncio.wait_for(websocket.receive(), timeout=WS_HEARTBEAT_TIMEOUT)
                
                if msg["type"] == "websocket.disconnect":
                    logger.info("WebSocket disconnected by client")
                    break
                
                if msg["type"] != "websocket.receive":
                    continue

                if "bytes" in msg:
                    WS_BYTES_RECEIVED_TOTAL.inc(len(msg["bytes"]))
                    WS_MESSAGES_RECEIVED_TOTAL.labels(message_type="binary").inc()
                    logger.warning("Received binary frame over WebSocket")
                    await safe_send_json({
                        "type": "error",
                        "payload": {"detail": "Binary messages are not supported. Please send JSON text."}
                    })
                    continue
                
                data = msg.get("text", "")
                WS_BYTES_RECEIVED_TOTAL.inc(len(data))
                
                if len(data) > WS_MESSAGE_SIZE_LIMIT:
                    WS_MESSAGES_RECEIVED_TOTAL.labels(message_type="oversized").inc()
                    logger.warning(f"WebSocket message exceeded size limit: {len(data)} bytes")
                    await safe_send_json({
                        "type": "error",
                        "payload": {"detail": f"Message too large (max {WS_MESSAGE_SIZE_LIMIT} bytes)"}
                    })
                    continue

                req_start_time = time.perf_counter()
                message = json.loads(data)
                if not isinstance(message, dict):
                    WS_MESSAGES_RECEIVED_TOTAL.labels(message_type="invalid_format").inc()
                    logger.warning(f"Received non-dictionary message over WebSocket: {type(message)}")
                    await safe_send_json({
                        "type": "error",
                        "payload": {"detail": "Message must be a JSON object (dictionary)"}
                    })
                    continue
                
                msg_type = message.get("type", "unknown")
                WS_MESSAGES_RECEIVED_TOTAL.labels(message_type=msg_type).inc()
            except asyncio.TimeoutError:
                logger.warning("WebSocket heartbeat timeout exceeded")
                break
            except json.JSONDecodeError:
                WS_MESSAGES_RECEIVED_TOTAL.labels(message_type="invalid_json").inc()
                logger.warning("Received invalid JSON over WebSocket")
                await safe_send_json({
                    "type": "error",
                    "payload": {"detail": "Invalid JSON received"}
                })
                continue
            except Exception as e:
                logger.error(f"Error receiving WS message: {e}")
                break
            
            request_id = message.get("request_id")
            
            try:
                if msg_type == "ping":
                    await safe_send_json({"type": "pong"})
                elif msg_type == "list_tools":
                    tools = registry.list_tools()
                    await safe_send_json({
                        "type": "tools_list",
                        "tools": tools,
                        "request_id": request_id
                    })
                elif msg_type == "list_active_tasks":
                    tasks = await registry.list_active_tasks()
                    await safe_send_json({
                        "type": "active_tasks_list",
                        "tasks": tasks,
                        "request_id": request_id
                    })
                elif msg_type == "get_health":
                    health_data = await get_health_data()
                    await safe_send_json({
                        "type": "health_data",
                        "data": health_data,
                        "request_id": request_id
                    })
                elif msg_type == "start":
                    if registry.active_task_count >= MAX_CONCURRENT_TASKS:
                        await safe_send_json({
                            "type": "error",
                            "request_id": request_id,
                            "payload": {"detail": f"Server busy: Maximum concurrent tasks ({MAX_CONCURRENT_TASKS}) reached."}
                        })
                    else:
                        tool_name = tool_name = message.get("tool_name")
                        args = message.get("args", {})
                        tool = registry.get_tool(tool_name)
                        if not tool:
                            await safe_send_json({
                                "type": "error",
                                "request_id": request_id,
                                "payload": {"detail": f"Tool not found: {tool_name}"}
                            })
                        else:
                            call_id = str(uuid.uuid4())
                            try:
                                gen = tool(**args)
                                await registry.store_task(call_id, gen, tool_name)
                                await registry.mark_consumed(call_id)
                                await safe_send_json({
                                    "type": "task_started", 
                                    "call_id": call_id, 
                                    "tool_name": tool_name, 
                                    "request_id": request_id
                                })
                                task = asyncio.create_task(run_ws_generator(safe_send_json, call_id, tool_name, gen, active_tasks))
                                active_tasks[call_id] = task
                            except Exception as e:
                                logger.error(f"Failed to start tool {tool_name} via WS: {e}", extra={"tool_name": tool_name})
                                await safe_send_json({
                                    "type": "error",
                                    "call_id": call_id,
                                    "request_id": request_id,
                                    "payload": {"detail": str(e)}
                                })
                elif msg_type == "stop":
                    call_id = message.get("call_id")
                    if call_id in active_tasks:
                        logger.info(f"Stopping task {call_id} via WebSocket request", extra={"call_id": call_id})
                        active_tasks[call_id].cancel()
                        await safe_send_json({
                            "call_id": call_id,
                            "type": "progress",
                            "payload": {"step": "Cancelled", "pct": 0, "log": "Task stopped by user."}
                        })
                        await safe_send_json({
                            "type": "stop_success",
                            "call_id": call_id,
                            "request_id": request_id
                        })
                    else:
                        # Try to stop task that might be in the registry but not in active_tasks (e.g. not being streamed yet)
                        task_data = await registry.get_task_no_consume(call_id)
                        if task_data:
                            logger.info(f"Stopping non-streamed task {call_id} via WebSocket request", extra={"call_id": call_id})
                            await task_data["gen"].aclose()
                            if not task_data["consumed"]:
                                await registry.remove_task(call_id)
                            await safe_send_json({
                                "type": "stop_success",
                                "call_id": call_id,
                                "request_id": request_id
                            })
                        else:
                            await safe_send_json({
                                "type": "error",
                                "call_id": call_id,
                                "request_id": request_id, 
                                "payload": {"detail": f"No active task found with call_id: {call_id}"}
                            })
                elif msg_type == "subscribe":
                    call_id = message.get("call_id")
                    task_data = await registry.get_task(call_id)
                    if task_data:
                        tool_name = task_data["tool_name"]
                        gen = task_data["gen"]
                        await safe_send_json({
                            "type": "task_started", 
                            "call_id": call_id, 
                            "tool_name": tool_name, 
                            "request_id": request_id
                        })
                        task = asyncio.create_task(run_ws_generator(safe_send_json, call_id, tool_name, gen, active_tasks))
                        active_tasks[call_id] = task
                    else:
                        await safe_send_json({
                            "type": "error",
                            "call_id": call_id,
                            "request_id": request_id, 
                            "payload": {"detail": f"Task not found or already being streamed: {call_id}"}
                        })
                elif msg_type == "input":
                    call_id = message.get("call_id")
                    value = message.get("value")
                    if await input_manager.provide_input(call_id, value):
                        logger.info(f"Input received for task {call_id}", extra={"call_id": call_id})
                        await safe_send_json({
                            "type": "input_success",
                            "call_id": call_id,
                            "request_id": request_id
                        })
                    else:
                        await safe_send_json({
                            "type": "error",
                            "call_id": call_id,
                            "request_id": request_id, 
                            "payload": {"detail": f"No task waiting for input with call_id: {call_id}"}
                        })
                else:
                    logger.warning(f"Unknown WebSocket message type: {msg_type}", extra={"ws_message": message})
                    await safe_send_json({
                        "type": "error",
                        "request_id": request_id, 
                        "payload": {"detail": f"Unknown message type: {msg_type}"}
                    })
            finally:
                req_latency = time.perf_counter() - req_start_time
                WS_REQUEST_LATENCY.labels(message_type=msg_type).observe(req_latency)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        ACTIVE_WS_CONNECTIONS.dec()
        conn_duration = time.perf_counter() - conn_start_time
        WS_CONNECTION_DURATION.observe(conn_duration)
        if active_tasks:
            logger.info(f"Cleaning up {len(active_tasks)} WebSocket tasks due to disconnect/timeout")
            for task in active_tasks.values():
                task.cancel()

async def run_ws_generator(send_fn, call_id: str, tool_name: str, gen, active_tasks: Dict[str, asyncio.Task]):
    call_id_var.set(call_id)
    tool_name_var.set(tool_name)
    start_time = time.perf_counter()
    status = "success"
    logger.info(f"Starting WS execution for task: {call_id}")
    try:
        async for item in gen:
            if isinstance(item, ProgressPayload):
                TASK_PROGRESS_STEPS_TOTAL.labels(tool_name=tool_name).inc()
                event = ProgressEvent(call_id=call_id, type="progress", payload=item)
            elif isinstance(item, dict) and item.get("type") == "input_request":
                event = ProgressEvent(call_id=call_id, type="input_request", payload=item["payload"])
            else:
                event = ProgressEvent(call_id=call_id, type="result", payload=item)
            await send_fn(event.model_dump())
    except asyncio.CancelledError:
        status = "cancelled"
        logger.info(f"WS task {call_id} cancelled")
    except Exception as e:
        status = "error"
        logger.error(f"WS task {call_id} error: {e}")
        await send_fn({"type": "error", "call_id": call_id, "payload": {"detail": str(e)}})
    finally:
        duration = time.perf_counter() - start_time
        TASK_DURATION.labels(tool_name=tool_name).observe(duration)
        TASKS_TOTAL.labels(tool_name=tool_name, status=status).inc()
        if call_id in active_tasks:
            del active_tasks[call_id]
        logger.info(f"WS task finished: {call_id} (duration: {duration:.2f}s, status: {status})")
from . import dummy_tool
