
import os

def append_tools():
    tools_file = "backend/app/dummy_tool.py"
    
    new_tools = """
@progress_tool(name="system_cpu_stats_ctx_switches_v23")
async def system_cpu_stats_ctx_switches_v23(samples: int = 1):
    vals = []
    for i in range(samples):
        import psutil
        vals.append(psutil.cpu_stats().ctx_switches)
        yield ProgressPayload(step="Sampling", pct=int(((i+1)/samples)*100))
        await asyncio.sleep(0.01)
    yield {"status": "audit_complete", "ctx_switches": sum(vals)/len(vals) if vals else 0}

@progress_tool(name="system_cpu_stats_interrupts_v23")
async def system_cpu_stats_interrupts_v23(samples: int = 1):
    vals = []
    for i in range(samples):
        import psutil
        vals.append(psutil.cpu_stats().interrupts)
        yield ProgressPayload(step="Sampling", pct=int(((i+1)/samples)*100))
        await asyncio.sleep(0.01)
    yield {"status": "audit_complete", "interrupts": sum(vals)/len(vals) if vals else 0}

@progress_tool(name="system_cpu_stats_soft_interrupts_v23")
async def system_cpu_stats_soft_interrupts_v23(samples: int = 1):
    vals = []
    for i in range(samples):
        import psutil
        vals.append(psutil.cpu_stats().soft_interrupts)
        yield ProgressPayload(step="Sampling", pct=int(((i+1)/samples)*100))
        await asyncio.sleep(0.01)
    yield {"status": "audit_complete", "soft_interrupts": sum(vals)/len(vals) if vals else 0}

@progress_tool(name="system_cpu_stats_syscalls_v23")
async def system_cpu_stats_syscalls_v23(samples: int = 1):
    vals = []
    for i in range(samples):
        import psutil
        vals.append(psutil.cpu_stats().syscalls)
        yield ProgressPayload(step="Sampling", pct=int(((i+1)/samples)*100))
        await asyncio.sleep(0.01)
    yield {"status": "audit_complete", "syscalls": sum(vals)/len(vals) if vals else 0}

@progress_tool(name="system_virtual_memory_total_v23")
async def system_virtual_memory_total_v23(samples: int = 1):
    import psutil
    val = psutil.virtual_memory().total
    yield ProgressPayload(step="Measuring", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "total": val}

@progress_tool(name="system_virtual_memory_available_v23")
async def system_virtual_memory_available_v23(samples: int = 1):
    import psutil
    val = psutil.virtual_memory().available
    yield ProgressPayload(step="Measuring", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "available": val}

@progress_tool(name="system_virtual_memory_used_v23")
async def system_virtual_memory_used_v23(samples: int = 1):
    import psutil
    val = psutil.virtual_memory().used
    yield ProgressPayload(step="Measuring", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "used": val}

@progress_tool(name="system_virtual_memory_free_v23")
async def system_virtual_memory_free_v23(samples: int = 1):
    import psutil
    val = psutil.virtual_memory().free
    yield ProgressPayload(step="Measuring", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "free": val}

@progress_tool(name="system_virtual_memory_active_v23")
async def system_virtual_memory_active_v23(samples: int = 1):
    import psutil
    val = getattr(psutil.virtual_memory(), 'active', 0)
    yield ProgressPayload(step="Measuring", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "active": val}

@progress_tool(name="system_virtual_memory_inactive_v23")
async def system_virtual_memory_inactive_v23(samples: int = 1):
    import psutil
    val = getattr(psutil.virtual_memory(), 'inactive', 0)
    yield ProgressPayload(step="Measuring", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "inactive": val}

@progress_tool(name="system_virtual_memory_buffers_v23")
async def system_virtual_memory_buffers_v23(samples: int = 1):
    import psutil
    val = getattr(psutil.virtual_memory(), 'buffers', 0)
    yield ProgressPayload(step="Measuring", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "buffers": val}

@progress_tool(name="system_virtual_memory_cached_v23")
async def system_virtual_memory_cached_v23(samples: int = 1):
    import psutil
    val = getattr(psutil.virtual_memory(), 'cached', 0)
    yield ProgressPayload(step="Measuring", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "cached": val}

@progress_tool(name="system_virtual_memory_shared_v23")
async def system_virtual_memory_shared_v23(samples: int = 1):
    import psutil
    val = getattr(psutil.virtual_memory(), 'shared', 0)
    yield ProgressPayload(step="Measuring", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "shared": val}

@progress_tool(name="system_virtual_memory_slab_v23")
async def system_virtual_memory_slab_v23(samples: int = 1):
    import psutil
    val = getattr(psutil.virtual_memory(), 'slab', 0)
    yield ProgressPayload(step="Measuring", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "slab": val}

@progress_tool(name="system_disk_usage_total_v23")
async def system_disk_usage_total_v23(path: str = "/"):
    import psutil
    val = psutil.disk_usage(path).total
    yield ProgressPayload(step="Querying", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "total": val}

@progress_tool(name="system_disk_usage_used_v23")
async def system_disk_usage_used_v23(path: str = "/"):
    import psutil
    val = psutil.disk_usage(path).used
    yield ProgressPayload(step="Querying", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "used": val}

@progress_tool(name="system_disk_usage_free_v23")
async def system_disk_usage_free_v23(path: str = "/"):
    import psutil
    val = psutil.disk_usage(path).free
    yield ProgressPayload(step="Querying", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "free": val}

@progress_tool(name="system_disk_usage_percent_v23")
async def system_disk_usage_percent_v23(path: str = "/"):
    import psutil
    val = psutil.disk_usage(path).percent
    yield ProgressPayload(step="Querying", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "percent": val}

@progress_tool(name="system_net_io_bytes_sent_v23")
async def system_net_io_bytes_sent_v23(samples: int = 1):
    import psutil
    val = psutil.net_io_counters().bytes_sent
    yield ProgressPayload(step="Querying", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "bytes_sent": val}

@progress_tool(name="system_net_io_bytes_recv_v23")
async def system_net_io_bytes_recv_v23(samples: int = 1):
    import psutil
    val = psutil.net_io_counters().bytes_recv
    yield ProgressPayload(step="Querying", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "bytes_recv": val}

@progress_tool(name="system_net_io_packets_sent_v23")
async def system_net_io_packets_sent_v23(samples: int = 1):
    import psutil
    val = psutil.net_io_counters().packets_sent
    yield ProgressPayload(step="Querying", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "packets_sent": val}

@progress_tool(name="system_net_io_packets_recv_v23")
async def system_net_io_packets_recv_v23(samples: int = 1):
    import psutil
    val = psutil.net_io_counters().packets_recv
    yield ProgressPayload(step="Querying", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "packets_recv": val}

@progress_tool(name="system_net_io_errin_v23")
async def system_net_io_errin_v23(samples: int = 1):
    import psutil
    val = psutil.net_io_counters().errin
    yield ProgressPayload(step="Querying", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "errin": val}

@progress_tool(name="system_net_io_errout_v23")
async def system_net_io_errout_v23(samples: int = 1):
    import psutil
    val = psutil.net_io_counters().errout
    yield ProgressPayload(step="Querying", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "errout": val}

@progress_tool(name="system_net_io_dropin_v23")
async def system_net_io_dropin_v23(samples: int = 1):
    import psutil
    val = psutil.net_io_counters().dropin
    yield ProgressPayload(step="Querying", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "dropin": val}

@progress_tool(name="system_net_io_dropout_v23")
async def system_net_io_dropout_v23(samples: int = 1):
    import psutil
    val = psutil.net_io_counters().dropout
    yield ProgressPayload(step="Querying", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "dropout": val}

@progress_tool(name="system_sensors_battery_percent_v23")
async def system_sensors_battery_percent_v23(samples: int = 1):
    import psutil
    battery = psutil.sensors_battery()
    val = battery.percent if battery else 100
    yield ProgressPayload(step="Sensing", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "percent": val}

@progress_tool(name="system_sensors_battery_secsleft_v23")
async def system_sensors_battery_secsleft_v23(samples: int = 1):
    import psutil
    battery = psutil.sensors_battery()
    val = battery.secsleft if battery else -1
    yield ProgressPayload(step="Sensing", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "secsleft": val}

@progress_tool(name="system_sensors_battery_power_plugged_v23")
async def system_sensors_battery_power_plugged_v23(samples: int = 1):
    import psutil
    battery = psutil.sensors_battery()
    val = battery.power_plugged if battery else True
    yield ProgressPayload(step="Sensing", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "power_plugged": val}

@progress_tool(name="system_users_count_v23")
async def system_users_count_v23(samples: int = 1):
    import psutil
    val = len(psutil.users())
    yield ProgressPayload(step="Counting", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "count": val}

@progress_tool(name="system_boot_time_v23")
async def system_boot_time_v23(samples: int = 1):
    import psutil
    val = psutil.boot_time()
    yield ProgressPayload(step="Retrieving", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "boot_time": val}

@progress_tool(name="system_cpu_count_logical_v23")
async def system_cpu_count_logical_v23(samples: int = 1):
    import psutil
    val = psutil.cpu_count(logical=True)
    yield ProgressPayload(step="Counting", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "count": val}

@progress_tool(name="system_cpu_count_physical_v23")
async def system_cpu_count_physical_v23(samples: int = 1):
    import psutil
    val = psutil.cpu_count(logical=False)
    yield ProgressPayload(step="Counting", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "count": val}

@progress_tool(name="system_cpu_freq_current_v23")
async def system_cpu_freq_current_v23(samples: int = 1):
    import psutil
    freq = psutil.cpu_freq()
    val = freq.current if freq else 0
    yield ProgressPayload(step="Measuring", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "current": val}

@progress_tool(name="system_cpu_freq_min_v23")
async def system_cpu_freq_min_v23(samples: int = 1):
    import psutil
    freq = psutil.cpu_freq()
    val = freq.min if freq else 0
    yield ProgressPayload(step="Measuring", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "min": val}

@progress_tool(name="system_cpu_freq_max_v23")
async def system_cpu_freq_max_v23(samples: int = 1):
    import psutil
    freq = psutil.cpu_freq()
    val = freq.max if freq else 0
    yield ProgressPayload(step="Measuring", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "max": val}

@progress_tool(name="system_loadavg_1m_v23")
async def system_loadavg_1m_v23(samples: int = 1):
    import psutil
    val = psutil.getloadavg()[0]
    yield ProgressPayload(step="Measuring", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "load": val}

@progress_tool(name="system_loadavg_5m_v23")
async def system_loadavg_5m_v23(samples: int = 1):
    import psutil
    val = psutil.getloadavg()[1]
    yield ProgressPayload(step="Measuring", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "load": val}

@progress_tool(name="system_loadavg_15m_v23")
async def system_loadavg_15m_v23(samples: int = 1):
    import psutil
    val = psutil.getloadavg()[2]
    yield ProgressPayload(step="Measuring", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "load": val}

@progress_tool(name="system_pid_count_v23")
async def system_pid_count_v23(samples: int = 1):
    import psutil
    val = len(psutil.pids())
    yield ProgressPayload(step="Counting", pct=50)
    await asyncio.sleep(0.05)
    yield {"status": "audit_complete", "count": val}
"""
    with open(tools_file, "a") as f:
        f.write(new_tools)
    print(f"Appended 40 tools to {tools_file}")

if __name__ == "__main__":
    append_tools()
