
new_tools = """
@progress_tool(name="system_disk_io_counters_read_bytes_avg_v16")
async def system_disk_io_counters_read_bytes_avg_v16(samples: int = 1):
    vals = []
    for i in range(samples):
        import psutil
        vals.append(getattr(psutil.disk_io_counters(), "read_bytes", 0))
        yield ProgressPayload(step="Sampling", pct=int(((i+1)/samples)*100))
        await asyncio.sleep(0.01)
    yield {"status": "audit_complete", "avg": sum(vals)/len(vals) if vals else 0}

@progress_tool(name="system_disk_io_counters_read_bytes_max_v16")
async def system_disk_io_counters_read_bytes_max_v16(samples: int = 1):
    vals = []
    for i in range(samples):
        import psutil
        vals.append(getattr(psutil.disk_io_counters(), "read_bytes", 0))
        yield ProgressPayload(step="Sampling", pct=int(((i+1)/samples)*100))
        await asyncio.sleep(0.01)
    yield {"status": "audit_complete", "max": max(vals) if vals else 0}

@progress_tool(name="system_disk_io_counters_read_bytes_min_v16")
async def system_disk_io_counters_read_bytes_min_v16(samples: int = 1):
    vals = []
    for i in range(samples):
        import psutil
        vals.append(getattr(psutil.disk_io_counters(), "read_bytes", 0))
        yield ProgressPayload(step="Sampling", pct=int(((i+1)/samples)*100))
        await asyncio.sleep(0.01)
    yield {"status": "audit_complete", "min": min(vals) if vals else 0}

@progress_tool(name="system_disk_io_counters_read_bytes_sum_v16")
async def system_disk_io_counters_read_bytes_sum_v16(samples: int = 1):
    vals = []
    for i in range(samples):
        import psutil
        vals.append(getattr(psutil.disk_io_counters(), "read_bytes", 0))
        yield ProgressPayload(step="Sampling", pct=int(((i+1)/samples)*100))
        await asyncio.sleep(0.01)
    yield {"status": "audit_complete", "sum": sum(vals)}

@progress_tool(name="system_disk_io_counters_write_bytes_avg_v16")
async def system_disk_io_counters_write_bytes_avg_v16(samples: int = 1):
    vals = []
    for i in range(samples):
        import psutil
        vals.append(getattr(psutil.disk_io_counters(), "write_bytes", 0))
        yield ProgressPayload(step="Sampling", pct=int(((i+1)/samples)*100))
        await asyncio.sleep(0.01)
    yield {"status": "audit_complete", "avg": sum(vals)/len(vals) if vals else 0}

@progress_tool(name="system_disk_io_counters_write_bytes_max_v16")
async def system_disk_io_counters_write_bytes_max_v16(samples: int = 1):
    vals = []
    for i in range(samples):
        import psutil
        vals.append(getattr(psutil.disk_io_counters(), "write_bytes", 0))
        yield ProgressPayload(step="Sampling", pct=int(((i+1)/samples)*100))
        await asyncio.sleep(0.01)
    yield {"status": "audit_complete", "max": max(vals) if vals else 0}

@progress_tool(name="system_disk_io_counters_write_bytes_min_v16")
async def system_disk_io_counters_write_bytes_min_v16(samples: int = 1):
    vals = []
    for i in range(samples):
        import psutil
        vals.append(getattr(psutil.disk_io_counters(), "write_bytes", 0))
        yield ProgressPayload(step="Sampling", pct=int(((i+1)/samples)*100))
        await asyncio.sleep(0.01)
    yield {"status": "audit_complete", "min": min(vals) if vals else 0}

@progress_tool(name="system_disk_io_counters_write_bytes_sum_v16")
async def system_disk_io_counters_write_bytes_sum_v16(samples: int = 1):
    vals = []
    for i in range(samples):
        import psutil
        vals.append(getattr(psutil.disk_io_counters(), "write_bytes", 0))
        yield ProgressPayload(step="Sampling", pct=int(((i+1)/samples)*100))
        await asyncio.sleep(0.01)
    yield {"status": "audit_complete", "sum": sum(vals)}

@progress_tool(name="system_net_io_counters_errin_avg_v16")
async def system_net_io_counters_errin_avg_v16(samples: int = 1):
    vals = []
    for i in range(samples):
        import psutil
        vals.append(getattr(psutil.net_io_counters(), "errin", 0))
        yield ProgressPayload(step="Sampling", pct=int(((i+1)/samples)*100))
        await asyncio.sleep(0.01)
    yield {"status": "audit_complete", "avg": sum(vals)/len(vals) if vals else 0}

@progress_tool(name="system_net_io_counters_errin_max_v16")
async def system_net_io_counters_errin_max_v16(samples: int = 1):
    vals = []
    for i in range(samples):
        import psutil
        vals.append(getattr(psutil.net_io_counters(), "errin", 0))
        yield ProgressPayload(step="Sampling", pct=int(((i+1)/samples)*100))
        await asyncio.sleep(0.01)
    yield {"status": "audit_complete", "max": max(vals) if vals else 0}

@progress_tool(name="system_net_io_counters_errin_min_v16")
async def system_net_io_counters_errin_min_v16(samples: int = 1):
    vals = []
    for i in range(samples):
        import psutil
        vals.append(getattr(psutil.net_io_counters(), "errin", 0))
        yield ProgressPayload(step="Sampling", pct=int(((i+1)/samples)*100))
        await asyncio.sleep(0.01)
    yield {"status": "audit_complete", "min": min(vals) if vals else 0}

@progress_tool(name="system_net_io_counters_errin_sum_v16")
async def system_net_io_counters_errin_sum_v16(samples: int = 1):
    vals = []
    for i in range(samples):
        import psutil
        vals.append(getattr(psutil.net_io_counters(), "errin", 0))
        yield ProgressPayload(step="Sampling", pct=int(((i+1)/samples)*100))
        await asyncio.sleep(0.01)
    yield {"status": "audit_complete", "sum": sum(vals)}
"""
import os
dummy_tool_path = "backend/app/dummy_tool.py"
if os.path.exists(dummy_tool_path):
    with open(dummy_tool_path, "a") as f:
        f.write(new_tools)
    print("Tools part 2 appended successfully to " + dummy_tool_path)
else:
    print("Error: " + dummy_tool_path + " not found.")
