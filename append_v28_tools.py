import os

def append_tools():
    tools_file = "backend/app/dummy_tool.py"
    
    new_tools = """
@progress_tool(name="system_process_num_ctx_switches_v28")
async def system_process_num_ctx_switches_v28(samples: int = 1):
    import psutil
    proc = psutil.Process()
    ctx = proc.num_ctx_switches()
    yield ProgressPayload(step="Querying", pct=50)
    await asyncio.sleep(0.01)
    yield {"status": "audit_complete", "voluntary": ctx.voluntary, "involuntary": ctx.involuntary}

@progress_tool(name="system_process_cpu_times_v28")
async def system_process_cpu_times_v28(samples: int = 1):
    import psutil
    proc = psutil.Process()
    times = proc.cpu_times()
    yield ProgressPayload(step="Querying", pct=50)
    await asyncio.sleep(0.01)
    yield {"status": "audit_complete", "user": times.user, "system": times.system}

@progress_tool(name="system_process_memory_info_v28")
async def system_process_memory_info_v28(samples: int = 1):
    import psutil
    proc = psutil.Process()
    mem = proc.memory_info()
    yield ProgressPayload(step="Querying", pct=50)
    await asyncio.sleep(0.01)
    yield {"status": "audit_complete", "rss": mem.rss, "vms": mem.vms}

@progress_tool(name="system_process_create_time_v28")
async def system_process_create_time_v28(samples: int = 1):
    import psutil
    proc = psutil.Process()
    val = proc.create_time()
    yield ProgressPayload(step="Querying", pct=50)
    await asyncio.sleep(0.01)
    yield {"status": "audit_complete", "value": val}

@progress_tool(name="system_process_status_v28")
async def system_process_status_v28(samples: int = 1):
    import psutil
    proc = psutil.Process()
    val = proc.status()
    yield ProgressPayload(step="Querying", pct=50)
    await asyncio.sleep(0.01)
    yield {"status": "audit_complete", "value": val}

@progress_tool(name="system_process_username_v28")
async def system_process_username_v28(samples: int = 1):
    import psutil
    proc = psutil.Process()
    val = proc.username()
    yield ProgressPayload(step="Querying", pct=50)
    await asyncio.sleep(0.01)
    yield {"status": "audit_complete", "value": val}

@progress_tool(name="system_process_cwd_v28")
async def system_process_cwd_v28(samples: int = 1):
    import psutil
    proc = psutil.Process()
    val = proc.cwd()
    yield ProgressPayload(step="Querying", pct=50)
    await asyncio.sleep(0.01)
    yield {"status": "audit_complete", "value": val}

@progress_tool(name="system_process_name_v28")
async def system_process_name_v28(samples: int = 1):
    import psutil
    proc = psutil.Process()
    val = proc.name()
    yield ProgressPayload(step="Querying", pct=50)
    await asyncio.sleep(0.01)
    yield {"status": "audit_complete", "value": val}

@progress_tool(name="system_process_ppid_v28")
async def system_process_ppid_v28(samples: int = 1):
    import psutil
    proc = psutil.Process()
    val = proc.ppid()
    yield ProgressPayload(step="Querying", pct=50)
    await asyncio.sleep(0.01)
    yield {"status": "audit_complete", "value": val}

@progress_tool(name="system_process_nice_v28")
async def system_process_nice_v28(samples: int = 1):
    import psutil
    proc = psutil.Process()
    val = proc.nice()
    yield ProgressPayload(step="Querying", pct=50)
    await asyncio.sleep(0.01)
    yield {"status": "audit_complete", "value": val}

@progress_tool(name="system_cpu_times_percent_v28")
async def system_cpu_times_percent_v28(interval: float = 0.1):
    import psutil
    val = psutil.cpu_times_percent(interval=interval)
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "user": val.user, "system": val.system, "idle": val.idle}

@progress_tool(name="system_cpu_stats_v28")
async def system_cpu_stats_v28(samples: int = 1):
    import psutil
    val = psutil.cpu_stats()
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "ctx_switches": val.ctx_switches, "interrupts": val.interrupts}

@progress_tool(name="system_virtual_memory_v28")
async def system_virtual_memory_v28(samples: int = 1):
    import psutil
    val = psutil.virtual_memory()
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "total": val.total, "available": val.available, "percent": val.percent}

@progress_tool(name="system_swap_memory_v28")
async def system_swap_memory_v28(samples: int = 1):
    import psutil
    val = psutil.swap_memory()
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "total": val.total, "used": val.used, "free": val.free, "percent": val.percent}

@progress_tool(name="system_net_io_counters_v28")
async def system_net_io_counters_v28(samples: int = 1):
    import psutil
    val = psutil.net_io_counters()
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "bytes_sent": val.bytes_sent, "bytes_recv": val.bytes_recv}

@progress_tool(name="system_disk_io_counters_v28")
async def system_disk_io_counters_v28(samples: int = 1):
    import psutil
    val = psutil.disk_io_counters()
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "read_count": val.read_count, "write_count": val.write_count}

@progress_tool(name="system_users_v28")
async def system_users_v28(samples: int = 1):
    import psutil
    val = psutil.users()
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "count": len(val)}

@progress_tool(name="system_boot_time_formatted_v28")
async def system_boot_time_formatted_v28(samples: int = 1):
    import psutil
    from datetime import datetime
    val = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "value": val}

@progress_tool(name="system_cpu_count_logical_v28")
async def system_cpu_count_logical_v28(samples: int = 1):
    import psutil
    val = psutil.cpu_count(logical=True)
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "value": val}

@progress_tool(name="system_cpu_count_physical_v28")
async def system_cpu_count_physical_v28(samples: int = 1):
    import psutil
    val = psutil.cpu_count(logical=False)
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "value": val}

@progress_tool(name="system_cpu_freq_v28")
async def system_cpu_freq_v28(samples: int = 1):
    import psutil
    val = psutil.cpu_freq()
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "current": val.current, "min": val.min, "max": val.max}

@progress_tool(name="system_disk_partitions_v28")
async def system_disk_partitions_v28(samples: int = 1):
    import psutil
    val = psutil.disk_partitions()
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "count": len(val)}

@progress_tool(name="system_sensors_battery_v28")
async def system_sensors_battery_v28(samples: int = 1):
    import psutil
    val = psutil.sensors_battery()
    yield ProgressPayload(step="Measuring", pct=50)
    if val:
        yield {"status": "audit_complete", "percent": val.percent, "power_plugged": val.power_plugged}
    else:
        yield {"status": "audit_complete", "percent": 100, "power_plugged": True}

@progress_tool(name="system_loadavg_v28")
async def system_loadavg_v28(samples: int = 1):
    import psutil
    val = psutil.getloadavg()
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "1m": val[0], "5m": val[1], "15m": val[2]}

@progress_tool(name="system_pid_list_count_v28")
async def system_pid_list_count_v28(samples: int = 1):
    import psutil
    val = psutil.pids()
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "value": len(val)}

@progress_tool(name="system_memory_available_gb_v28")
async def system_memory_available_gb_v28(samples: int = 1):
    import psutil
    val = psutil.virtual_memory().available / (1024**3)
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "value": val}

@progress_tool(name="system_memory_used_gb_v28")
async def system_memory_used_gb_v28(samples: int = 1):
    import psutil
    val = psutil.virtual_memory().used / (1024**3)
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "value": val}

@progress_tool(name="system_memory_total_gb_v28")
async def system_memory_total_gb_v28(samples: int = 1):
    import psutil
    val = psutil.virtual_memory().total / (1024**3)
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "value": val}

@progress_tool(name="system_cpu_usage_avg_v28")
async def system_cpu_usage_avg_v28(interval: float = 0.1):
    import psutil
    val = psutil.cpu_percent(interval=interval)
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "value": val}

@progress_tool(name="system_process_memory_rss_gb_v28")
async def system_process_memory_rss_gb_v28(samples: int = 1):
    import psutil
    proc = psutil.Process()
    val = proc.memory_info().rss / (1024**3)
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "value": val}

@progress_tool(name="system_process_threads_v28_check")
async def system_process_threads_v28_check(samples: int = 1):
    import psutil
    proc = psutil.Process()
    val = len(proc.threads())
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "value": val}

@progress_tool(name="system_process_open_files_v28_check")
async def system_process_open_files_v28_check(samples: int = 1):
    import psutil
    proc = psutil.Process()
    val = len(proc.open_files())
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "value": val}

@progress_tool(name="system_process_connections_v28_check")
async def system_process_connections_v28_check(samples: int = 1):
    import psutil
    proc = psutil.Process()
    val = len(proc.connections())
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "value": val}

@progress_tool(name="system_net_if_addrs_keys_v28")
async def system_net_if_addrs_keys_v28(samples: int = 1):
    import psutil
    val = list(psutil.net_if_addrs().keys())
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "value": val}

@progress_tool(name="system_net_if_stats_keys_v28")
async def system_net_if_stats_keys_v28(samples: int = 1):
    import psutil
    val = list(psutil.net_if_stats().keys())
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "value": val}

@progress_tool(name="system_disk_partitions_device_v28")
async def system_disk_partitions_device_v28(samples: int = 1):
    import psutil
    val = [p.device for p in psutil.disk_partitions()]
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "value": val}

@progress_tool(name="system_disk_partitions_mountpoint_v28")
async def system_disk_partitions_mountpoint_v28(samples: int = 1):
    import psutil
    val = [p.mountpoint for p in psutil.disk_partitions()]
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "value": val}

@progress_tool(name="system_cpu_times_percent_iowait_v28")
async def system_cpu_times_percent_iowait_v28(interval: float = 0.1):
    import psutil
    val = psutil.cpu_times_percent(interval=interval)
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "value": getattr(val, 'iowait', 0)}

@progress_tool(name="system_cpu_times_percent_irq_v28")
async def system_cpu_times_percent_irq_v28(interval: float = 0.1):
    import psutil
    val = psutil.cpu_times_percent(interval=interval)
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "value": getattr(val, 'irq', 0)}

@progress_tool(name="system_cpu_times_percent_softirq_v28")
async def system_cpu_times_percent_softirq_v28(interval: float = 0.1):
    import psutil
    val = psutil.cpu_times_percent(interval=interval)
    yield ProgressPayload(step="Measuring", pct=50)
    yield {"status": "audit_complete", "value": getattr(val, 'softirq', 0)}
"""
    with open(tools_file, "a") as f:
        f.write(new_tools)
    print(f"Appended 40 tools to {tools_file}")

if __name__ == "__main__":
    append_tools()
