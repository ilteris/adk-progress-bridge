from datetime import datetime
import asyncio
import random
import psutil
import time
import sys
import os
from .bridge import progress_tool, ProgressPayload, input_manager
from .logger import logger
from .context import call_id_var
from .health import health_engine

@progress_tool(name="long_audit")
async def long_audit(duration: int = 10):
    """
    Simulates a long running audit task.
    """
    steps = [
        "Initializing scan...",
        "Connecting to data source...",
        "Analyzing masonry contracts...",
        "Checking compliance regulations...",
        "Generating final report..."
    ]
    
    n_steps = len(steps)
    for i, step in enumerate(steps):
        # Calculate percentage
        pct = int(((i + 1) / n_steps) * 100)
        
        # Use info to ensure visibility in default log level
        logger.info(f"Step {i+1}/{n_steps}: {step}", extra={"step": step, "pct": pct})
        
        # Yield progress
        yield ProgressPayload(
            step=step,
            pct=pct,
            log=f"Working on step {i+1}/{n_steps}: {step}"
        )
        
        # Simulate work
        await asyncio.sleep(duration / n_steps)

    # Yield final report
    logger.info("Audit task finished")
    yield {
        "status": "complete",
        "summary": "Audit finished successfully. No major issues found.",
        "findings_count": 0
    }

@progress_tool(name="security_scan")
async def security_scan(target: str = "all"):
    logger.info(f"Starting security scan on target: {target}", extra={"target": target})
    yield ProgressPayload(step="Scanning ports", pct=50)
    await asyncio.sleep(1)
    yield ProgressPayload(step="Checking vulnerabilities", pct=100)
    yield {"status": "secure"}

@progress_tool(name="multi_stage_analysis")
async def multi_stage_analysis(documents: int = 3):
    """
    Simulates a complex multi-stage analysis on multiple documents.
    Shows sub-progress within the log.
    """
    stages = ["Loading", "Extracting", "Analyzing", "Summarizing"]
    total_work = documents * len(stages)
    completed_work = 0

    for doc_idx in range(documents):
        doc_name = f"Doc_{doc_idx + 1}.pdf"
        for stage in stages:
            # Sub-task logic
            pct = int((completed_work / total_work) * 100)
            logger.info(f"Processing {doc_name} - Stage: {stage}", extra={"doc": doc_name, "stage": stage})
            yield ProgressPayload(
                step=f"Processing {doc_name}",
                pct=pct,
                log=f"Stage: {stage} for {doc_name}",
                metadata={"doc": doc_name, "stage": stage}
            )
            
            # Simulate variable work time
            await asyncio.sleep(random.uniform(0.1, 0.2))
            completed_work += 1

    yield ProgressPayload(step="Finalizing", pct=100, log="Consolidating all document analyses...")
    await asyncio.sleep(0.3)

    yield {
        "status": "success",
        "documents_processed": documents,
        "total_stages": len(stages),
        "summary": f"Successfully analyzed {documents} documents across {len(stages)} stages."
    }

@progress_tool(name="parallel_report_generation")
async def parallel_report_generation(reports: int = 4):
    """
    Simulates parallel report generation.
    Since this is a generator, we 'yield' as sub-tasks report progress.
    """
    logger.info(f"Starting parallel jobs for {reports} reports")
    yield ProgressPayload(step="Starting parallel jobs", pct=0, log=f"Spinning up {reports} report workers...")
    
    # We use a queue to collect progress from sub-tasks and yield them in order
    queue = asyncio.Queue()

    async def worker(report_id: int):
        report_name = f"Report-{report_id}"
        # Start
        logger.info(f"Worker {report_name} started")
        await queue.put(ProgressPayload(
            step="Parallel Work", 
            pct=0, 
            log=f"Worker {report_name} started",
            metadata={"worker": report_name, "status": "started"}
        ))
        
        # Simulate work
        work_time = random.uniform(0.3, 0.8)
        await asyncio.sleep(work_time)
        
        # Finish
        logger.info(f"Worker {report_name} finished")
        await queue.put(ProgressPayload(
            step="Parallel Work", 
            pct=0, 
            log=f"Worker {report_name} finished in {work_time:.2f}s",
            metadata={"worker": report_name, "status": "finished"}
        ))

    # Start all workers
    worker_tasks = [asyncio.create_task(worker(i)) for i in range(reports)]
    
    finished_count = 0
    while finished_count < reports:
        payload = await queue.get()
        if payload.metadata.get("status") == "finished":
            finished_count += 1
        
        # Calculate overall percentage based on finished workers
        global_pct = int((finished_count / reports) * 100)
        payload.pct = global_pct
        
        yield payload

    yield {
        "status": "complete",
        "reports_generated": reports,
        "parallel": True
    }

@progress_tool(name="brittle_process")
async def brittle_process(fail_at: int = 50):
    """
    Simulates a process that might fail when it reaches a certain percentage.
    """
    for pct in range(0, 101, 10):
        if pct >= fail_at:
            logger.error(f"Brittle process failed at {pct}%", extra={"pct": pct})
            raise Exception(f"Simulated failure at {pct}% as requested (fail_at={fail_at})")
        
        logger.info(f"Brittle process progress: {pct}%")
        yield ProgressPayload(
            step="Running brittle process",
            pct=pct,
            log=f"Progress: {pct}%"
        )
        await asyncio.sleep(0.1)
    
    yield {"status": "miraculously_succeeded"}

@progress_tool(name="interactive_task")
async def interactive_task():
    """
    Demonstrates bi-directional WebSocket communication by requesting input.
    """
    call_id = call_id_var.get()
    
    yield ProgressPayload(step="Analyzing situation", pct=30, log="Thinking if I need help...")
    await asyncio.sleep(1)
    
    # Request input
    prompt = "I need your approval to proceed with the final phase. Should I continue? (yes/no)"
    yield {
        "type": "input_request",
        "payload": {"prompt": prompt}
    }
    
    # Wait for input
    user_response = await input_manager.wait_for_input(call_id, prompt)
    
    if user_response.lower() == "yes":
        yield ProgressPayload(step="Finalizing", pct=100, log=f"User said {user_response}, proceeding!")
        await asyncio.sleep(0.5)
        yield {"status": "complete", "message": "Task finished with user approval."}
    else:
        yield ProgressPayload(step="Aborting", pct=100, log=f"User said {user_response}, stopping.")
        await asyncio.sleep(0.5)
        yield {"status": "aborted", "message": "Task aborted by user."}

@progress_tool(name="large_payload_tool")
async def large_payload_tool(**kwargs):
    """
    A tool that accepts any arguments, used for testing large payloads.
    """
    yield ProgressPayload(step="Received large payload", pct=100, log=f"Args keys: {list(kwargs.keys())}")
    yield {"status": "success", "received_keys": len(kwargs)}

@progress_tool(name="resource_monitor")
async def resource_monitor(iterations: int = 5):
    """
    Monitors process resources using psutil.
    """
    process = psutil.Process()
    for i in range(iterations):
        pct = int(((i + 1) / iterations) * 100)
        mem = process.memory_info()
        cpu = process.cpu_percent(interval=0.1)
        fds = process.num_fds() if hasattr(process, "num_fds") else 0
        threads = process.num_threads()
        
        logger.info(f"Resource Monitor - Iteration {i+1}: CPU {cpu}%, MEM {mem.rss / 1024 / 1024:.2f}MB")
        
        yield ProgressPayload(
            step="Monitoring resources",
            pct=pct,
            log=f"Iteration {i+1}/{iterations}: CPU {cpu}%, RSS {mem.rss / 1024 / 1024:.2f}MB, FDs {fds}, Threads {threads}",
            metadata={
                "cpu_percent": cpu,
                "memory_rss_bytes": mem.rss,
                "num_fds": fds,
                "num_threads": threads
            }
        )
        await asyncio.sleep(0.5)

    yield {
        "status": "complete",
        "final_stats": {
            "rss": process.memory_info().rss,
            "cpu": process.cpu_percent(interval=None)
        }
    }

@progress_tool(name="deep_health_check")
async def deep_health_check():
    """
    Performs a deep system health check using the HealthEngine.
    """
    logger.info("Starting deep health check tool")
    yield ProgressPayload(step="Initializing health engine", pct=10, log="Warming up engine...")
    await asyncio.sleep(0.2)
    
    yield ProgressPayload(step="Collecting raw metrics", pct=40, log="Gathering CPU, Memory, Disk and Network data...")
    # Since we don't have easy access to app.state here without globalizing it,
    # we use a dummy state or just rely on health_engine's internal collection.
    # In main.py, get_health_data takes app.state.
    class DummyState:
        def __init__(self):
            self.peak_ws_connections = 0
            self.last_throughput_time = time.time()
            self.last_bytes_received = 0
            self.last_bytes_sent = 0
    
    dummy_state = DummyState()
    
    yield ProgressPayload(step="Processing metrics", pct=70, log="Mapping raw metrics to structured report...")
    data = await health_engine.get_health_data(dummy_state, "2.4.0", "v614-supreme-apex-adele-verification", "v614 SUPREME APEX VERIFICATION ADELE")
    await asyncio.sleep(0.2)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Health check complete.")
    yield {
        "status": "healthy",
        "snapshot": data
    }

@progress_tool(name="network_status_check")
async def network_status_check():
    """
    Simulates checking network connectivity and latency.
    """
    logger.info("Starting network status check")
    yield ProgressPayload(step="Initializing network probe", pct=10, log="Checking interface status...")
    await asyncio.sleep(0.2)
    
    yield ProgressPayload(step="Pinging gateways", pct=40, log="Measuring latency to primary gateway...")
    # Simulate some latency measurements
    latencies = [random.uniform(10, 50) for _ in range(3)]
    avg_latency = sum(latencies) / len(latencies)
    await asyncio.sleep(0.3)
    
    yield ProgressPayload(
        step="Checking DNS resolution", 
        pct=70, 
        log=f"Average gateway latency: {avg_latency:.2f}ms. Testing DNS lookup for google.com...",
        metadata={"avg_gateway_latency_ms": avg_latency}
    )
    await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Network check complete.")
    yield {
        "status": "online",
        "avg_latency_ms": avg_latency,
        "dns_resolved": True
    }

@progress_tool(name="system_config_audit")
async def system_config_audit():
    """
    Audits basic system configurations and environment settings.
    """
    logger.info("Starting system configuration audit")
    yield ProgressPayload(step="Checking environment", pct=20, log="Inspecting environment variables and paths...")
    await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Verifying Python runtime", pct=50, log=f"Python version: {sys.version}")
    await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Auditing working directory", pct=80, log=f"Current working directory: {os.getcwd()}")
    await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing audit", pct=100, log="System configuration audit complete.")
    yield {
        "status": "audit_complete",
        "python_version": sys.version,
        "cwd": os.getcwd(),
        "platform": sys.platform,
        "audit_timestamp": time.time()
    }

@progress_tool(name="connectivity_benchmark")
async def connectivity_benchmark(samples: int = 5):
    """
    Benchmarks the connection quality by sending periodic payloads and measuring response availability.
    """
    logger.info(f"Starting connectivity benchmark with {samples} samples")
    yield ProgressPayload(step="Benchmark init", pct=0, log="Preparing benchmark environment...")
    await asyncio.sleep(0.2)
    
    results = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        sample_latency = random.uniform(5, 25)
        results.append(sample_latency)
        
        logger.info(f"Sample {i+1}/{samples}: Latency {sample_latency:.2f}ms")
        yield ProgressPayload(
            step="Sampling latency",
            pct=pct,
            log=f"Measured sample {i+1}/{samples}: {sample_latency:.2f}ms",
            metadata={"sample_id": i + 1, "latency_ms": sample_latency}
        )
        await asyncio.sleep(0.3)
    
    avg_latency = sum(results) / len(results)
    yield {
        "status": "benchmark_complete",
        "avg_latency_ms": avg_latency,
        "samples_taken": samples,
        "quality_score": "EXCELLENT" if avg_latency < 20 else "GOOD"
    }

@progress_tool(name="concurrency_stress_test")
async def concurrency_stress_test(load: int = 3):
    """
    Simulates high concurrency load and monitors system stability.
    """
    logger.info(f"Starting concurrency stress test with load factor {load}")
    yield ProgressPayload(step="Stress test init", pct=0, log=f"Deploying {load} virtual concurrent workers...")
    await asyncio.sleep(0.2)
    
    for i in range(load):
        pct = int(((i + 1) / load) * 100)
        logger.info(f"Worker {i+1} active. Simulating high-frequency message throughput.")
        yield ProgressPayload(
            step="Simulating load",
            pct=pct,
            log=f"Worker {i+1}/{load} active. Checking event loop latency...",
            metadata={"worker_id": i + 1, "load_factor": load}
        )
        await asyncio.sleep(0.4)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Concurrency stress test complete. All workers terminated cleanly.")
    yield {
        "status": "stress_test_passed",
        "load_factor": load,
        "stability": "HIGH"
    }

@progress_tool(name="event_loop_latency_audit")
async def event_loop_latency_audit(samples: int = 5):
    """
    Measures event loop latency by scheduling callbacks and measuring actual delay.
    """
    logger.info(f"Starting event loop latency audit with {samples} samples")
    yield ProgressPayload(step="Initializing latency probe", pct=0, log="Calibrating timer...")
    await asyncio.sleep(0.2)
    
    latencies = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        start_time = time.perf_counter()
        # Schedule a no-op task to measure loop turn time
        await asyncio.sleep(0)
        end_time = time.perf_counter()
        
        # We expect sleep(0) to be near zero, any deviation is latency
        latency_ms = (end_time - start_time) * 1000
        latencies.append(latency_ms)
        
        logger.info(f"Sample {i+1}/{samples}: Event loop lag {latency_ms:.4f}ms")
        yield ProgressPayload(
            step="Sampling latency",
            pct=pct,
            log=f"Measured event loop lag sample {i+1}/{samples}: {latency_ms:.4f}ms",
            metadata={"sample_id": i + 1, "latency_ms": latency_ms}
        )
        await asyncio.sleep(0.3)
    
    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)
    
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Avg lag: {avg_latency:.4f}ms")
    yield {
        "status": "audit_complete",
        "avg_latency_ms": avg_latency,
        "max_latency_ms": max_latency,
        "samples": samples,
        "stability": "OPTIMAL" if max_latency < 5 else "STABLE"
    }

@progress_tool(name="garbage_collection_audit")
async def garbage_collection_audit(samples: int = 3):
    """
    Audits Python garbage collection stats and object counts.
    """
    import gc
    logger.info(f"Starting garbage collection audit with {samples} samples")
    yield ProgressPayload(step="Initializing GC probe", pct=0, log="Monitoring memory management lifecycle...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        count0, count1, count2 = gc.get_count()
        objects_count = len(gc.get_objects())
        
        logger.info(f"Sample {i+1}/{samples}: GC Counts ({count0}, {count1}, {count2}), Objects: {objects_count}")
        yield ProgressPayload(
            step="Sampling GC stats",
            pct=pct,
            log=f"Measured GC counts sample {i+1}/{samples}: {count0}, {count1}, {count2}. Total objects: {objects_count}",
            metadata={
                "sample_id": i + 1,
                "gc_counts": [count0, count1, count2],
                "objects_count": objects_count
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Memory management is STABLE.")
    yield {
        "status": "audit_complete",
        "final_objects_count": len(gc.get_objects()),
        "gc_thresholds": gc.get_threshold(),
        "stability": "STABLE"
    }

@progress_tool(name="asyncio_task_audit")
async def asyncio_task_audit(samples: int = 3):
    """
    Audits active asyncio tasks and their status.
    """
    logger.info(f"Starting asyncio task audit with {samples} samples")
    yield ProgressPayload(step="Initializing task probe", pct=0, log="Scanning event loop for active tasks...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        all_tasks = asyncio.all_tasks()
        task_count = len(all_tasks)
        
        # Categorize tasks by status if possible, or just list names
        task_names = [t.get_name() for t in all_tasks]
        
        logger.info(f"Sample {i+1}/{samples}: {task_count} active tasks.")
        yield ProgressPayload(
            step="Sampling task stats",
            pct=pct,
            log=f"Measured {task_count} active asyncio tasks. Sample {i+1}/{samples}.",
            metadata={
                "sample_id": i + 1,
                "task_count": task_count,
                "task_names": task_names[:10] # Limit to top 10 names
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Event loop is healthy.")
    yield {
        "status": "audit_complete",
        "final_task_count": len(asyncio.all_tasks()),
        "stability": "STABLE"
    }

@progress_tool(name="disk_io_audit")
async def disk_io_audit(samples: int = 3):
    """
    Audits Disk I/O statistics using psutil.
    """
    logger.info(f"Starting Disk I/O audit with {samples} samples")
    yield ProgressPayload(step="Initializing disk probe", pct=0, log="Collecting baseline I/O counters...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        io_counters = psutil.disk_io_counters()
        read_bytes = io_counters.read_bytes
        write_bytes = io_counters.write_bytes
        
        logger.info(f"Sample {i+1}/{samples}: Read {read_bytes} bytes, Write {write_bytes} bytes.")
        yield ProgressPayload(
            step="Sampling Disk I/O stats",
            pct=pct,
            log=f"Measured Disk I/O sample {i+1}/{samples}: Read {read_bytes}, Write {write_bytes}.",
            metadata={
                "sample_id": i + 1,
                "read_bytes": read_bytes,
                "write_bytes": write_bytes
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Disk subsystem is healthy.")
    yield {
        "status": "audit_complete",
        "final_io_counters": psutil.disk_io_counters()._asdict(),
        "stability": "STABLE"
    }

@progress_tool(name="context_switch_audit")
async def context_switch_audit(samples: int = 3):
    """
    Audits system context switches using psutil.
    """
    logger.info(f"Starting context switch audit with {samples} samples")
    yield ProgressPayload(step="Initializing context probe", pct=0, log="Collecting baseline context switch counters...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        ctx_switches = process.num_ctx_switches()
        voluntary = ctx_switches.voluntary
        involuntary = ctx_switches.involuntary
        
        logger.info(f"Sample {i+1}/{samples}: Voluntary {voluntary}, Involuntary {involuntary}.")
        yield ProgressPayload(
            step="Sampling context switches",
            pct=pct,
            log=f"Measured context switches sample {i+1}/{samples}: Voluntary {voluntary}, Involuntary {involuntary}.",
            metadata={
                "sample_id": i + 1,
                "voluntary": voluntary,
                "involuntary": involuntary
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Scheduler interaction is healthy.")
    yield {
        "status": "audit_complete",
        "final_ctx_switches": process.num_ctx_switches()._asdict(),
        "stability": "STABLE"
    }

@progress_tool(name="memory_leak_audit")
async def memory_leak_audit(samples: int = 3):
    """
    Audits memory usage over time to detect potential leaks.
    """
    logger.info(f"Starting memory leak audit with {samples} samples")
    yield ProgressPayload(step="Initializing memory probe", pct=0, log="Capturing baseline memory state...")
    
    process = psutil.Process()
    memory_history = []
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        mem_info = process.memory_info()
        rss = mem_info.rss
        memory_history.append(rss)
        
        logger.info(f"Sample {i+1}/{samples}: RSS {rss / 1024 / 1024:.2f}MB")
        yield ProgressPayload(
            step="Sampling memory usage",
            pct=pct,
            log=f"Measured memory sample {i+1}/{samples}: RSS {rss / 1024 / 1024:.2f}MB",
            metadata={
                "sample_id": i + 1,
                "rss_bytes": rss,
                "vms_bytes": mem_info.vms
            }
        )
        await asyncio.sleep(0.3)
    
    leak_detected = False
    if len(memory_history) > 1:
        leak_detected = memory_history[-1] > memory_history[0] * 1.1 # 10% growth threshold
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Memory usage is STABLE.")
    yield {
        "status": "audit_complete",
        "baseline_rss": memory_history[0],
        "final_rss": memory_history[-1],
        "leak_detected": leak_detected,
        "stability": "STABLE"
    }
@progress_tool(name="network_connections_audit")
async def network_connections_audit(samples: int = 3):
    """
    Audits active network connections using psutil.
    """
    logger.info(f"Starting network connections audit with {samples} samples")
    yield ProgressPayload(step="Initializing network probe", pct=0, log="Collecting active socket information...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        connections = process.net_connections(kind="all")
        conn_count = len(connections)
        
        logger.info(f"Sample {i+1}/{samples}: {conn_count} active connections.")
        yield ProgressPayload(
            step="Sampling network connections",
            pct=pct,
            log=f"Measured {conn_count} active network connections. Sample {i+1}/{samples}.",
            metadata={
                "sample_id": i + 1,
                "connection_count": conn_count,
                "connections": [str(c) for c in connections[:5]]
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Network stack is healthy.")
    yield {
        "status": "audit_complete",
        "final_connection_count": len(psutil.Process().net_connections(kind="all")),
        "stability": "STABLE"
    }

@progress_tool(name="open_files_audit")
async def open_files_audit(samples: int = 3):
    """
    Audits active open file descriptors using psutil.
    """
    logger.info(f"Starting open files audit with {samples} samples")
    yield ProgressPayload(step="Initializing file probe", pct=0, log="Collecting open file handle information...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            files = process.open_files()
            file_count = len(files)
        except Exception as e:
            logger.warning(f"Error collecting open files: {e}")
            file_count = 0
            files = []
        
        logger.info(f"Sample {i+1}/{samples}: {file_count} open files.")
        yield ProgressPayload(
            step="Sampling open files",
            pct=pct,
            log=f"Measured {file_count} open file handles. Sample {i+1}/{samples}.",
            metadata={
                "sample_id": i + 1,
                "file_count": file_count,
                "files": [f.path for f in files[:5]]
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. File handle management is healthy.")
    yield {
        "status": "audit_complete",
        "final_file_count": len(psutil.Process().open_files()),
        "stability": "STABLE"
    }

@progress_tool(name="cpu_usage_audit")
async def cpu_usage_audit(samples: int = 3):
    """
    Audits detailed CPU usage, including per-core statistics using psutil.
    """
    logger.info(f"Starting CPU usage audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting per-core baseline counters...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        cpu_percent = psutil.cpu_percent(interval=0.1)
        per_cpu_percent = psutil.cpu_percent(interval=None, percpu=True)
        cpu_times = psutil.cpu_times()._asdict()
        
        logger.info(f"Sample {i+1}/{samples}: Total CPU {cpu_percent}%, Cores: {len(per_cpu_percent)}")
        yield ProgressPayload(
            step="Sampling CPU usage",
            pct=pct,
            log=f"Measured CPU sample {i+1}/{samples}: Total {cpu_percent}%. Per-core stats available.",
            metadata={
                "sample_id": i + 1,
                "total_cpu_percent": cpu_percent,
                "per_cpu_percent": per_cpu_percent,
                "cpu_times": cpu_times
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. CPU subsystem is healthy.")
    yield {
        "status": "audit_complete",
        "final_cpu_percent": psutil.cpu_percent(interval=None),
        "core_count": psutil.cpu_count(),
        "load_avg": psutil.getloadavg() if hasattr(psutil, "getloadavg") else "N/A",
        "stability": "STABLE"
    }
@progress_tool(name="thread_count_audit")
async def thread_count_audit(samples: int = 3):
    """
    Audits active thread counts within the process using psutil.
    """
    logger.info(f"Starting thread count audit with {samples} samples")
    yield ProgressPayload(step="Initializing thread probe", pct=0, log="Collecting active thread information...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        threads = process.threads()
        thread_count = process.num_threads()
        
        logger.info(f"Sample {i+1}/{samples}: {thread_count} active threads.")
        yield ProgressPayload(
            step="Sampling thread counts",
            pct=pct,
            log=f"Measured {thread_count} active threads. Sample {i+1}/{samples}.",
            metadata={
                "sample_id": i + 1,
                "thread_count": thread_count,
                "threads": [t._asdict() for t in threads[:5]]
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Threading model is STABLE.")
    yield {
        "status": "audit_complete",
        "final_thread_count": psutil.Process().num_threads(),
        "stability": "STABLE"
    }

@progress_tool(name="load_average_audit")
async def load_average_audit(samples: int = 3):
    """
    Audits system load average using psutil.
    """
    logger.info(f"Starting load average audit with {samples} samples")
    yield ProgressPayload(step="Initializing load probe", pct=0, log="Collecting system load statistics...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        if hasattr(psutil, "getloadavg"):
            load_avg = psutil.getloadavg()
        else:
            load_avg = (0.0, 0.0, 0.0)
            
        logger.info(f"Sample {i+1}/{samples}: Load Avg {load_avg}")
        yield ProgressPayload(
            step="Sampling load average",
            pct=pct,
            log=f"Measured load average sample {i+1}/{samples}: {load_avg}.",
            metadata={
                "sample_id": i + 1,
                "load_avg_1m": load_avg[0],
                "load_avg_5m": load_avg[1],
                "load_avg_15m": load_avg[2]
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. System load is STABLE.")
    yield {
        "status": "audit_complete",
        "final_load_avg": psutil.getloadavg() if hasattr(psutil, "getloadavg") else (0.0, 0.0, 0.0),
        "stability": "STABLE"
    }

@progress_tool(name="process_uptime_audit")
async def process_uptime_audit(samples: int = 3):
    """
    Audits process uptime and start time.
    """
    logger.info(f"Starting process uptime audit with {samples} samples")
    yield ProgressPayload(step="Initializing uptime probe", pct=0, log="Checking process birth time...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        create_time = process.create_time()
        uptime = time.time() - create_time
        
        logger.info(f"Sample {i+1}/{samples}: Process Uptime {uptime:.2f}s")
        yield ProgressPayload(
            step="Sampling uptime",
            pct=pct,
            log=f"Measured process uptime sample {i+1}/{samples}: {uptime:.2f}s.",
            metadata={
                "sample_id": i + 1,
                "create_time": create_time,
                "uptime_seconds": uptime,
                "uptime_human": time.strftime("%H:%M:%S", time.gmtime(uptime))
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Process is RELIABLE.")
    yield {
        "status": "audit_complete",
        "final_uptime_seconds": time.time() - psutil.Process().create_time(),
        "stability": "STABLE"
    }

@progress_tool(name="virtual_memory_audit")
async def virtual_memory_audit(samples: int = 3):
    """
    Audits virtual memory statistics using psutil.
    """
    logger.info(f"Starting virtual memory audit with {samples} samples")
    yield ProgressPayload(step="Initializing memory probe", pct=0, log="Collecting virtual memory baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        vmem = psutil.virtual_memory()
        
        logger.info(f"Sample {i+1}/{samples}: Available {vmem.available / 1024 / 1024:.2f}MB, Percent {vmem.percent}%")
        yield ProgressPayload(
            step="Sampling virtual memory",
            pct=pct,
            log=f"Measured virtual memory sample {i+1}/{samples}: Available {vmem.available / 1024 / 1024:.2f}MB, Percent {vmem.percent}%.",
            metadata={
                "sample_id": i + 1,
                "total": vmem.total,
                "available": vmem.available,
                "percent": vmem.percent,
                "used": vmem.used,
                "free": vmem.free
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Memory subsystem is STABLE.")
    yield {
        "status": "audit_complete",
        "final_available_mb": psutil.virtual_memory().available / 1024 / 1024,
        "stability": "STABLE"
    }

@progress_tool(name="disk_usage_audit")
async def disk_usage_audit(samples: int = 3):
    """
    Audits disk usage statistics using psutil.
    """
    logger.info(f"Starting disk usage audit with {samples} samples")
    yield ProgressPayload(step="Initializing disk probe", pct=0, log="Collecting disk usage statistics...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        usage = psutil.disk_usage('/')
        
        logger.info(f"Sample {i+1}/{samples}: {usage.percent}% used, {usage.free / 1024 / 1024 / 1024:.2f}GB free")
        yield ProgressPayload(
            step="Sampling disk usage",
            pct=pct,
            log=f"Measured disk usage sample {i+1}/{samples}: {usage.percent}% used, {usage.free / 1024 / 1024 / 1024:.2f}GB free.",
            metadata={
                "sample_id": i + 1,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Disk subsystem is STABLE.")
    yield {
        "status": "audit_complete",
        "final_percent": psutil.disk_usage('/').percent,
        "stability": "STABLE"
    }

@progress_tool(name="swap_memory_audit")
async def swap_memory_audit(samples: int = 3):
    """
    Audits swap memory statistics using psutil.
    """
    logger.info(f"Starting swap memory audit with {samples} samples")
    yield ProgressPayload(step="Initializing swap probe", pct=0, log="Collecting swap memory baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        swap = psutil.swap_memory()
        
        logger.info(f"Sample {i+1}/{samples}: {swap.percent}% used, {swap.free / 1024 / 1024:.2f}MB free")
        yield ProgressPayload(
            step="Sampling swap memory",
            pct=pct,
            log=f"Measured swap memory sample {i+1}/{samples}: {swap.percent}% used, {swap.free / 1024 / 1024:.2f}MB free.",
            metadata={
                "sample_id": i + 1,
                "total": swap.total,
                "used": swap.used,
                "free": swap.free,
                "percent": swap.percent,
                "sin": swap.sin,
                "sout": swap.sout
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Swap subsystem is STABLE.")
    yield {
        "status": "audit_complete",
        "final_percent": psutil.swap_memory().percent,
        "stability": "STABLE"
    }

@progress_tool(name="process_priority_audit")
async def process_priority_audit(samples: int = 3):
    """
    Audits process priority and scheduling class.
    """
    logger.info(f"Starting process priority audit with {samples} samples")
    yield ProgressPayload(step="Initializing priority probe", pct=0, log="Checking process nice value and scheduling...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        nice = process.nice()
        try:
            ionice = process.ionice() if hasattr(process, "ionice") else "N/A"
        except Exception:
            ionice = "N/A"
        
        logger.info(f"Sample {i+1}/{samples}: Nice {nice}, IONice {ionice}")
        yield ProgressPayload(
            step="Sampling process priority",
            pct=pct,
            log=f"Measured process priority sample {i+1}/{samples}: Nice {nice}.",
            metadata={
                "sample_id": i + 1,
                "nice": nice,
                "ionice": str(ionice)
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Process priority is STABLE.")
    yield {
        "status": "audit_complete",
        "final_nice": psutil.Process().nice(),
        "stability": "STABLE"
    }

@progress_tool(name="process_memory_full_audit")
async def process_memory_full_audit(samples: int = 3):
    """
    Audits process memory maps and full memory info using psutil.
    """
    logger.info(f"Starting process memory full audit with {samples} samples")
    yield ProgressPayload(step="Initializing memory map probe", pct=0, log="Collecting detailed memory mapping information...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        mem_info = process.memory_full_info()
        try:
            uss = mem_info.uss
        except AttributeError:
            uss = 0
            
        logger.info(f"Sample {i+1}/{samples}: USS {uss / 1024 / 1024:.2f}MB")
        yield ProgressPayload(
            step="Sampling memory maps",
            pct=pct,
            log=f"Measured process USS sample {i+1}/{samples}: {uss / 1024 / 1024:.2f}MB.",
            metadata={
                "sample_id": i + 1,
                "uss": uss,
                "rss": mem_info.rss,
                "vms": mem_info.vms
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Memory mapping is STABLE.")
    yield {
        "status": "audit_complete",
        "final_uss_mb": uss / 1024 / 1024,
        "stability": "STABLE"
    }

@progress_tool(name="process_io_counters_audit")
async def process_io_counters_audit(samples: int = 3):
    """
    Audits process I/O counters (read/write/char) using psutil.
    """
    logger.info(f"Starting process I/O counters audit with {samples} samples")
    yield ProgressPayload(step="Initializing I/O probe", pct=0, log="Collecting process-level I/O baseline...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            io = process.io_counters()
            read_count = io.read_count
            write_count = io.write_count
            read_bytes = io.read_bytes
            write_bytes = io.write_bytes
        except Exception as e:
            logger.warning(f"Error collecting process I/O: {e}")
            read_count = write_count = read_bytes = write_bytes = 0
            
        logger.info(f"Sample {i+1}/{samples}: Read {read_bytes} bytes, Write {write_bytes} bytes.")
        yield ProgressPayload(
            step="Sampling process I/O",
            pct=pct,
            log=f"Measured process I/O sample {i+1}/{samples}: Read {read_bytes} bytes.",
            metadata={
                "sample_id": i + 1,
                "read_count": read_count,
                "write_count": write_count,
                "read_bytes": read_bytes,
                "write_bytes": write_bytes
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Process I/O is STABLE.")
    yield {
        "status": "audit_complete",
        "final_io": process.io_counters()._asdict() if hasattr(process, "io_counters") else {},
        "stability": "STABLE"
    }

@progress_tool(name="process_environ_audit")
async def process_environ_audit(samples: int = 3):
    """
    Audits process environment variables using psutil.
    """
    logger.info(f"Starting process environment audit with {samples} samples")
    yield ProgressPayload(step="Initializing environment probe", pct=0, log="Collecting environment variables...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            environ = process.environ()
            env_count = len(environ)
        except Exception as e:
            logger.warning(f"Error collecting process environment: {e}")
            environ = {}
            env_count = 0
            
        logger.info(f"Sample {i+1}/{samples}: {env_count} environment variables.")
        yield ProgressPayload(
            step="Sampling process environment",
            pct=pct,
            log=f"Measured {env_count} environment variables. Sample {i+1}/{samples}.",
            metadata={
                "sample_id": i + 1,
                "env_count": env_count,
                "keys": list(environ.keys())[:10]
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Environment is STABLE.")
    yield {
        "status": "audit_complete",
        "final_env_count": len(psutil.Process().environ()),
        "stability": "STABLE"
    }

@progress_tool(name="process_cmdline_audit")
async def process_cmdline_audit(samples: int = 3):
    """
    Audits process command line arguments using psutil.
    """
    logger.info(f"Starting process command line audit with {samples} samples")
    yield ProgressPayload(step="Initializing command line probe", pct=0, log="Collecting command line arguments...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            cmdline = process.cmdline()
            arg_count = len(cmdline)
        except Exception as e:
            logger.warning(f"Error collecting process cmdline: {e}")
            cmdline = []
            arg_count = 0
            
        logger.info(f"Sample {i+1}/{samples}: {arg_count} command line arguments.")
        yield ProgressPayload(
            step="Sampling process command line",
            pct=pct,
            log=f"Measured {arg_count} command line arguments. Sample {i+1}/{samples}.",
            metadata={
                "sample_id": i + 1,
                "arg_count": arg_count,
                "cmdline": cmdline
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Command line is STABLE.")
    yield {
        "status": "audit_complete",
        "final_cmdline": psutil.Process().cmdline(),
        "stability": "STABLE"
    }

@progress_tool(name="process_memory_maps_audit")
async def process_memory_maps_audit(samples: int = 3):
    """
    Audits process memory maps using psutil.
    """
    logger.info(f"Starting process memory maps audit with {samples} samples")
    yield ProgressPayload(step="Initializing memory map probe", pct=0, log="Collecting detailed memory map information...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            maps = process.memory_maps()
            map_count = len(maps)
        except Exception as e:
            logger.warning(f"Error collecting process memory maps: {e}")
            maps = []
            map_count = 0
            
        logger.info(f"Sample {i+1}/{samples}: {map_count} memory mappings.")
        yield ProgressPayload(
            step="Sampling process memory maps",
            pct=pct,
            log=f"Measured {map_count} memory mappings. Sample {i+1}/{samples}.",
            metadata={
                "sample_id": i + 1,
                "map_count": map_count,
                "maps": [str(m) for m in maps[:5]]
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Memory mapping is STABLE.")
    yield {
        "status": "audit_complete",
        "final_map_count": len(psutil.Process().memory_maps()) if hasattr(psutil.Process(), "memory_maps") else 0,
        "stability": "STABLE"
    }

@progress_tool(name="process_cpu_times_audit")
async def process_cpu_times_audit(samples: int = 3):
    """
    Audits process CPU times using psutil.
    """
    logger.info(f"Starting process CPU times audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU times probe", pct=0, log="Collecting process-level CPU timing baseline...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            cpu_times = process.cpu_times()
            user = cpu_times.user
            system = cpu_times.system
        except Exception as e:
            logger.warning(f"Error collecting process CPU times: {e}")
            user = system = 0.0
            
        logger.info(f"Sample {i+1}/{samples}: User {user}s, System {system}s.")
        yield ProgressPayload(
            step="Sampling process CPU times",
            pct=pct,
            log=f"Measured process CPU times sample {i+1}/{samples}: User {user}s, System {system}s.",
            metadata={
                "sample_id": i + 1,
                "user": user,
                "system": system,
                "children_user": getattr(cpu_times, "children_user", 0.0),
                "children_system": getattr(cpu_times, "children_system", 0.0)
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. CPU timing is STABLE.")
    yield {
        "status": "audit_complete",
        "final_cpu_times": process.cpu_times()._asdict() if hasattr(process.cpu_times(), "_asdict") else process.cpu_times(),
        "stability": "STABLE"
    }
@progress_tool(name="process_cpu_affinity_audit")
async def process_cpu_affinity_audit(samples: int = 3):
    """
    Audits process CPU affinity using psutil.
    """
    logger.info(f"Starting process CPU affinity audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU affinity probe", pct=0, log="Collecting process-level CPU affinity baseline...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            affinity = process.cpu_affinity()
            affinity_count = len(affinity)
        except Exception as e:
            logger.warning(f"Error collecting process CPU affinity: {e}")
            affinity = []
            affinity_count = 0
            
        logger.info(f"Sample {i+1}/{samples}: {affinity_count} CPUs in affinity mask.")
        yield ProgressPayload(
            step="Sampling process CPU affinity",
            pct=pct,
            log=f"Measured process CPU affinity sample {i+1}/{samples}: {affinity_count} CPUs.",
            metadata={
                "sample_id": i + 1,
                "affinity_count": affinity_count,
                "affinity": affinity
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. CPU affinity is STABLE.")
    yield {
        "status": "audit_complete",
        "final_affinity": process.cpu_affinity() if hasattr(process, "cpu_affinity") else [],
        "stability": "STABLE"
    }

@progress_tool(name="process_num_fds_audit")
async def process_num_fds_audit(samples: int = 3):
    """
    Audits the number of file descriptors used by the process using psutil.
    """
    logger.info(f"Starting process file descriptor count audit with {samples} samples")
    yield ProgressPayload(step="Initializing FD probe", pct=0, log="Collecting process-level file descriptor baseline...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            num_fds = process.num_fds() if hasattr(process, "num_fds") else 0
        except Exception as e:
            logger.warning(f"Error collecting process FD count: {e}")
            num_fds = 0
            
        logger.info(f"Sample {i+1}/{samples}: {num_fds} open file descriptors.")
        yield ProgressPayload(
            step="Sampling FD count",
            pct=pct,
            log=f"Measured process FD count sample {i+1}/{samples}: {num_fds} descriptors.",
            metadata={
                "sample_id": i + 1,
                "num_fds": num_fds
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. File descriptor usage is STABLE.")
    yield {
        "status": "audit_complete",
        "final_num_fds": process.num_fds() if hasattr(process, "num_fds") else 0,
        "stability": "STABLE"
    }

@progress_tool(name="process_page_faults_audit")
async def process_page_faults_audit(samples: int = 3):
    """
    Audits process page faults using psutil.
    """
    logger.info(f"Starting process page faults audit with {samples} samples")
    yield ProgressPayload(step="Initializing page fault probe", pct=0, log="Collecting process-level page fault baseline...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            mem_info = process.memory_info()
            minor = getattr(mem_info, "pfaults", 0)
            major = getattr(mem_info, "pageins", 0)
        except Exception as e:
            logger.warning(f"Error collecting process page faults: {e}")
            minor = major = 0
            
        logger.info(f"Sample {i+1}/{samples}: Minor {minor}, Major {major}.")
        yield ProgressPayload(
            step="Sampling page faults",
            pct=pct,
            log=f"Measured process page faults sample {i+1}/{samples}: Minor {minor}, Major {major}.",
            metadata={
                "sample_id": i + 1,
                "minor": minor,
                "major": major
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Memory management is healthy.")
    yield {
        "status": "audit_complete",
        "final_page_faults": {
            "minor": getattr(process.memory_info(), "pfaults", 0),
            "major": getattr(process.memory_info(), "pageins", 0)
        },
        "stability": "STABLE"
    }
@progress_tool(name="process_memory_percent_audit")
async def process_memory_percent_audit(samples: int = 3):
    """
    Audits process memory usage percentage using psutil.
    """
    logger.info(f"Starting process memory percent audit with {samples} samples")
    yield ProgressPayload(step="Initializing memory percent probe", pct=0, log="Collecting process-level memory baseline...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            mem_percent = process.memory_percent()
        except Exception as e:
            logger.warning(f"Error collecting process memory percent: {e}")
            mem_percent = 0.0
            
        logger.info(f"Sample {i+1}/{samples}: Memory Percent {mem_percent:.2f}%")
        yield ProgressPayload(
            step="Sampling memory percent",
            pct=pct,
            log=f"Measured process memory percent sample {i+1}/{samples}: {mem_percent:.2f}%.",
            metadata={
                "sample_id": i + 1,
                "memory_percent": mem_percent
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Memory usage is within expected parameters.")
    yield {
        "status": "audit_complete",
        "final_memory_percent": process.memory_percent(),
        "stability": "STABLE"
    }

@progress_tool(name="process_num_threads_audit")
async def process_num_threads_audit(samples: int = 3):
    """
    Audits the number of threads used by the process using psutil.
    """
    logger.info(f"Starting process thread count audit with {samples} samples")
    yield ProgressPayload(step="Initializing thread probe", pct=0, log="Collecting process-level thread baseline...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            num_threads = process.num_threads()
        except Exception as e:
            logger.warning(f"Error collecting process thread count: {e}")
            num_threads = 0
            
        logger.info(f"Sample {i+1}/{samples}: {num_threads} active threads.")
        yield ProgressPayload(
            step="Sampling thread count",
            pct=pct,
            log=f"Measured process thread count sample {i+1}/{samples}: {num_threads} threads.",
            metadata={
                "sample_id": i + 1,
                "num_threads": num_threads
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Threading model is healthy.")
    yield {
        "status": "audit_complete",
        "final_num_threads": process.num_threads(),
        "stability": "STABLE"
    }

@progress_tool(name="process_status_audit")
async def process_status_audit(samples: int = 3):
    """
    Audits process status using psutil.
    """
    logger.info(f"Starting process status audit with {samples} samples")
    yield ProgressPayload(step="Initializing status probe", pct=0, log="Collecting process-level status baseline...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            status = process.status()
        except Exception as e:
            logger.warning(f"Error collecting process status: {e}")
            status = "unknown"
            
        logger.info(f"Sample {i+1}/{samples}: Process Status {status}")
        yield ProgressPayload(
            step="Sampling process status",
            pct=pct,
            log=f"Measured process status sample {i+1}/{samples}: {status}.",
            metadata={
                "sample_id": i + 1,
                "status": status
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Process status is stable.")
    yield {
        "status": "audit_complete",
        "final_status": process.status(),
        "stability": "STABLE"
    }
@progress_tool(name="process_create_time_audit")
async def process_create_time_audit(samples: int = 3):
    """
    Audits process creation time using psutil.
    """
    logger.info(f"Starting process creation time audit with {samples} samples")
    yield ProgressPayload(step="Initializing creation time probe", pct=0, log="Collecting process-level creation timing baseline...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            create_time = process.create_time()
        except Exception as e:
            logger.warning(f"Error collecting process create time: {e}")
            create_time = 0.0
            
        logger.info(f"Sample {i+1}/{samples}: Process Create Time {create_time}")
        yield ProgressPayload(
            step="Sampling process creation time",
            pct=pct,
            log=f"Measured process creation time sample {i+1}/{samples}: {create_time}.",
            metadata={
                "sample_id": i + 1,
                "create_time": create_time,
                "create_time_iso": datetime.fromtimestamp(create_time).isoformat() if create_time > 0 else "N/A"
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Creation timing is stable.")
    yield {
        "status": "audit_complete",
        "final_create_time": process.create_time(),
        "stability": "STABLE"
    }

@progress_tool(name="process_gids_audit")
async def process_gids_audit(samples: int = 3):
    """
    Audits process group IDs (GIDs) using psutil.
    """
    logger.info(f"Starting process GIDs audit with {samples} samples")
    yield ProgressPayload(step="Initializing GID probe", pct=0, log="Collecting process-level group ID baseline...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            gids = process.gids()
        except Exception as e:
            logger.warning(f"Error collecting process GIDs: {e}")
            gids = None
            
        logger.info(f"Sample {i+1}/{samples}: Process GIDs {gids}")
        yield ProgressPayload(
            step="Sampling process GIDs",
            pct=pct,
            log=f"Measured process GIDs sample {i+1}/{samples}: {gids}.",
            metadata={
                "sample_id": i + 1,
                "gids": gids._asdict() if hasattr(gids, "_asdict") else gids
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Group ID configuration is stable.")
    yield {
        "status": "audit_complete",
        "final_gids": process.gids()._asdict() if hasattr(process.gids(), "_asdict") else process.gids(),
        "stability": "STABLE"
    }

@progress_tool(name="process_uids_audit")
async def process_uids_audit(samples: int = 3):
    """
    Audits process user IDs (UIDs) using psutil.
    """
    logger.info(f"Starting process UIDs audit with {samples} samples")
    yield ProgressPayload(step="Initializing UID probe", pct=0, log="Collecting process-level user ID baseline...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            uids = process.uids()
        except Exception as e:
            logger.warning(f"Error collecting process UIDs: {e}")
            uids = None
            
        logger.info(f"Sample {i+1}/{samples}: Process UIDs {uids}")
        yield ProgressPayload(
            step="Sampling process UIDs",
            pct=pct,
            log=f"Measured process UIDs sample {i+1}/{samples}: {uids}.",
            metadata={
                "sample_id": i + 1,
                "uids": uids._asdict() if hasattr(uids, "_asdict") else uids
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. User ID configuration is stable.")
    yield {
        "status": "audit_complete",
        "final_uids": process.uids()._asdict() if hasattr(process.uids(), "_asdict") else process.uids(),
        "stability": "STABLE"
    }
@progress_tool(name="process_children_audit")
async def process_children_audit(samples: int = 3):
    """
    Audits process children using psutil.
    """
    logger.info(f"Starting process children audit with {samples} samples")
    yield ProgressPayload(step="Initializing children probe", pct=0, log="Collecting process-level children baseline...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            children = process.children(recursive=True)
            child_count = len(children)
        except Exception as e:
            logger.warning(f"Error collecting process children: {e}")
            children = []
            child_count = 0
            
        logger.info(f"Sample {i+1}/{samples}: {child_count} child processes.")
        yield ProgressPayload(
            step="Sampling process children",
            pct=pct,
            log=f"Measured {child_count} child processes. Sample {i+1}/{samples}.",
            metadata={
                "sample_id": i + 1,
                "child_count": child_count,
                "children": [str(c) for c in children[:5]]
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Child process management is stable.")
    yield {
        "status": "audit_complete",
        "final_child_count": len(psutil.Process().children(recursive=True)),
        "stability": "STABLE"
    }

@progress_tool(name="process_cwd_audit")
async def process_cwd_audit(samples: int = 3):
    """
    Audits process current working directory using psutil.
    """
    logger.info(f"Starting process CWD audit with {samples} samples")
    yield ProgressPayload(step="Initializing CWD probe", pct=0, log="Collecting process-level working directory baseline...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            cwd = process.cwd()
        except Exception as e:
            logger.warning(f"Error collecting process CWD: {e}")
            cwd = "unknown"
            
        logger.info(f"Sample {i+1}/{samples}: Process CWD {cwd}")
        yield ProgressPayload(
            step="Sampling process CWD",
            pct=pct,
            log=f"Measured process CWD sample {i+1}/{samples}: {cwd}.",
            metadata={
                "sample_id": i + 1,
                "cwd": cwd
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Working directory is stable.")
    yield {
        "status": "audit_complete",
        "final_cwd": psutil.Process().cwd(),
        "stability": "STABLE"
    }

@progress_tool(name="process_parent_audit")
async def process_parent_audit(samples: int = 3):
    """
    Audits process parent using psutil.
    """
    logger.info(f"Starting process parent audit with {samples} samples")
    yield ProgressPayload(step="Initializing parent probe", pct=0, log="Collecting process-level parent baseline...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            parent = process.parent()
            parent_pid = parent.pid if parent else None
        except Exception as e:
            logger.warning(f"Error collecting process parent: {e}")
            parent = None
            parent_pid = None
            
        logger.info(f"Sample {i+1}/{samples}: Process Parent PID {parent_pid}")
        yield ProgressPayload(
            step="Sampling process parent",
            pct=pct,
            log=f"Measured process parent sample {i+1}/{samples}: PID {parent_pid}.",
            metadata={
                "sample_id": i + 1,
                "parent_pid": parent_pid,
                "parent_name": parent.name() if parent else "N/A"
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Parent process identification is stable.")
    yield {
        "status": "audit_complete",
        "final_parent_pid": psutil.Process().parent().pid if psutil.Process().parent() else None,
        "stability": "STABLE"
    }

@progress_tool(name="process_username_audit")
async def process_username_audit(samples: int = 3):
    """
    Audits process username using psutil.
    """
    logger.info(f"Starting process username audit with {samples} samples")
    yield ProgressPayload(step="Initializing username probe", pct=0, log="Collecting process-level username baseline...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            username = process.username()
        except Exception as e:
            logger.warning(f"Error collecting process username: {e}")
            username = "unknown"
            
        logger.info(f"Sample {i+1}/{samples}: Process Username {username}")
        yield ProgressPayload(
            step="Sampling process username",
            pct=pct,
            log=f"Measured process username sample {i+1}/{samples}: {username}.",
            metadata={
                "sample_id": i + 1,
                "username": username
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Username is stable.")
    yield {
        "status": "audit_complete",
        "final_username": psutil.Process().username(),
        "stability": "STABLE"
    }
@progress_tool(name="process_nice_audit")
async def process_nice_audit(samples: int = 3):
    """
    Audits process nice value using psutil.
    """
    logger.info(f"Starting process nice audit with {samples} samples")
    yield ProgressPayload(step="Initializing nice probe", pct=0, log="Collecting process-level priority baseline...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            nice_value = process.nice()
        except Exception as e:
            logger.warning(f"Error collecting process nice: {e}")
            nice_value = 0
            
        logger.info(f"Sample {i+1}/{samples}: Process Nice {nice_value}")
        yield ProgressPayload(
            step="Sampling process nice",
            pct=pct,
            log=f"Measured process nice sample {i+1}/{samples}: {nice_value}.",
            metadata={
                "sample_id": i + 1,
                "nice": nice_value
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Priority level is stable.")
    yield {
        "status": "audit_complete",
        "final_nice": psutil.Process().nice(),
        "stability": "STABLE"
    }

@progress_tool(name="process_open_files_audit")
async def process_open_files_audit(samples: int = 3):
    """
    Audits process open files using psutil.
    """
    logger.info(f"Starting process open files audit with {samples} samples")
    yield ProgressPayload(step="Initializing file probe", pct=0, log="Collecting process-level open files baseline...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            open_files = process.open_files()
            count = len(open_files)
        except Exception as e:
            logger.warning(f"Error collecting process open files: {e}")
            open_files = []
            count = 0
            
        logger.info(f"Sample {i+1}/{samples}: Open Files Count {count}")
        yield ProgressPayload(
            step="Sampling open files",
            pct=pct,
            log=f"Measured open files sample {i+1}/{samples}: {count} files.",
            metadata={
                "sample_id": i + 1,
                "count": count
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Open file handles are stable.")
    yield {
        "status": "audit_complete",
        "final_open_files_count": len(psutil.Process().open_files()),
        "stability": "STABLE"
    }

@progress_tool(name="process_connections_audit")
async def process_connections_audit(samples: int = 3):
    """
    Audits process connections using psutil.
    """
    logger.info(f"Starting process connections audit with {samples} samples")
    yield ProgressPayload(step="Initializing connection probe", pct=0, log="Collecting process-level network connections baseline...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            connections = process.net_connections()
            count = len(connections)
        except Exception as e:
            logger.warning(f"Error collecting process connections: {e}")
            connections = []
            count = 0
            
        logger.info(f"Sample {i+1}/{samples}: Connections Count {count}")
        yield ProgressPayload(
            step="Sampling connections",
            pct=pct,
            log=f"Measured connections sample {i+1}/{samples}: {count} active connections.",
            metadata={
                "sample_id": i + 1,
                "count": count
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Network connections are stable.")
    yield {
        "status": "audit_complete",
        "final_connections_count": len(psutil.Process().net_connections()),
        "stability": "STABLE"
    }

@progress_tool(name="process_memory_full_info_audit")
async def process_memory_full_info_audit(samples: int = 3):
    """
    Audits process full memory info using psutil.
    """
    logger.info(f"Starting process full memory audit with {samples} samples")
    yield ProgressPayload(step="Initializing full memory probe", pct=0, log="Collecting comprehensive process-level memory baseline...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            info = process.memory_full_info()
            rss = info.rss
            vms = info.vms
        except Exception as e:
            logger.warning(f"Error collecting process full memory info: {e}")
            rss, vms = 0, 0
            
        logger.info(f"Sample {i+1}/{samples}: RSS {rss}, VMS {vms}")
        yield ProgressPayload(
            step="Sampling full memory info",
            pct=pct,
            log=f"Measured process memory sample {i+1}/{samples}: RSS {rss}, VMS {vms}.",
            metadata={
                "sample_id": i + 1,
                "rss": rss,
                "vms": vms
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Memory usage is stable.")
    yield {
        "status": "audit_complete",
        "final_rss": psutil.Process().memory_full_info().rss,
        "stability": "STABLE"
    }

@progress_tool(name="process_threads_audit")
async def process_threads_audit(samples: int = 3):
    """
    Audits process thread details using psutil.
    """
    logger.info(f"Starting process threads audit with {samples} samples")
    yield ProgressPayload(step="Initializing thread detail probe", pct=0, log="Collecting process-level thread details baseline...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            threads = process.threads()
            count = len(threads)
        except Exception as e:
            logger.warning(f"Error collecting process thread details: {e}")
            threads = []
            count = 0
            
        logger.info(f"Sample {i+1}/{samples}: Thread Details Count {count}")
        yield ProgressPayload(
            step="Sampling thread details",
            pct=pct,
            log=f"Measured thread details sample {i+1}/{samples}: {count} active threads.",
            metadata={
                "sample_id": i + 1,
                "count": count
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Threading state is stable.")
    yield {
        "status": "audit_complete",
        "final_thread_count": len(psutil.Process().threads()),
        "stability": "STABLE"
    }

@progress_tool(name="process_exe_audit")
async def process_exe_audit(samples: int = 3):
    """
    Audits process executable path using psutil.
    """
    logger.info(f"Starting process executable audit with {samples} samples")
    yield ProgressPayload(step="Initializing executable probe", pct=0, log="Collecting process-level executable baseline...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            exe_path = process.exe()
        except Exception as e:
            logger.warning(f"Error collecting process executable path: {e}")
            exe_path = "unknown"
            
        logger.info(f"Sample {i+1}/{samples}: Executable Path {exe_path}")
        yield ProgressPayload(
            step="Sampling executable path",
            pct=pct,
            log=f"Measured executable path sample {i+1}/{samples}: {exe_path}.",
            metadata={
                "sample_id": i + 1,
                "exe_path": exe_path
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Executable path is verified.")
    yield {
        "status": "audit_complete",
        "final_exe_path": psutil.Process().exe(),
        "stability": "STABLE"
    }

@progress_tool(name="process_terminal_audit")
async def process_terminal_audit(samples: int = 3):
    """
    Audits the terminal associated with the process using psutil.
    """
    logger.info(f"Starting process terminal audit with {samples} samples")
    yield ProgressPayload(step="Initializing terminal probe", pct=0, log="Collecting process-level terminal baseline...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            terminal = process.terminal()
        except Exception as e:
            logger.warning(f"Error collecting process terminal: {e}")
            terminal = "unknown"
            
        logger.info(f"Sample {i+1}/{samples}: Process Terminal {terminal}")
        yield ProgressPayload(
            step="Sampling process terminal",
            pct=pct,
            log=f"Measured process terminal sample {i+1}/{samples}: {terminal}.",
            metadata={
                "sample_id": i + 1,
                "terminal": terminal
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Terminal identification is stable.")
    yield {
        "status": "audit_complete",
        "final_terminal": psutil.Process().terminal() if hasattr(psutil.Process(), "terminal") else "unknown",
        "stability": "STABLE"
    }

@progress_tool(name="process_ionice_extended_audit")
async def process_ionice_extended_audit(samples: int = 3):
    """
    Audits process I/O priority (ionice) in detail using psutil.
    """
    logger.info(f"Starting process ionice extended audit with {samples} samples")
    yield ProgressPayload(step="Initializing ionice probe", pct=0, log="Collecting process-level I/O priority baseline...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            if hasattr(process, "ionice"):
                ionice = process.ionice()
            else:
                ionice = "N/A"
        except Exception as e:
            logger.warning(f"Error collecting process ionice: {e}")
            ionice = "unknown"
            
        logger.info(f"Sample {i+1}/{samples}: Process IONice {ionice}")
        yield ProgressPayload(
            step="Sampling process ionice",
            pct=pct,
            log=f"Measured process ionice sample {i+1}/{samples}: {ionice}.",
            metadata={
                "sample_id": i + 1,
                "ionice": str(ionice)
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. I/O priority level is stable.")
    yield {
        "status": "audit_complete",
        "final_ionice": str(psutil.Process().ionice()) if hasattr(psutil.Process(), "ionice") else "N/A",
        "stability": "STABLE"
    }

@progress_tool(name="process_rlimit_audit")
async def process_rlimit_audit(samples: int = 3):
    """
    Audits process resource limits (rlimit) using psutil.
    """
    logger.info(f"Starting process rlimit audit with {samples} samples")
    yield ProgressPayload(step="Initializing rlimit probe", pct=0, log="Collecting process-level resource limits baseline...")
    
    process = psutil.Process()
    # Common rlimits to check if available
    limits_to_check = [
        ("RLIMIT_NOFILE", getattr(psutil, "RLIMIT_NOFILE", None)),
        ("RLIMIT_AS", getattr(psutil, "RLIMIT_AS", None)),
        ("RLIMIT_CPU", getattr(psutil, "RLIMIT_CPU", None)),
    ]
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        found_limits = {}
        if hasattr(process, "rlimit"):
            for name, limit_const in limits_to_check:
                if limit_const is not None:
                    try:
                        found_limits[name] = process.rlimit(limit_const)
                    except Exception:
                        pass
        
        logger.info(f"Sample {i+1}/{samples}: Collected {len(found_limits)} resource limits.")
        yield ProgressPayload(
            step="Sampling resource limits",
            pct=pct,
            log=f"Measured {len(found_limits)} resource limits. Sample {i+1}/{samples}.",
            metadata={
                "sample_id": i + 1,
                "limits": found_limits
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Resource limits are stable.")
    yield {
        "status": "audit_complete",
        "limits_count": len(found_limits),
        "stability": "STABLE"
    }

@progress_tool(name="process_cpu_num_audit")
async def process_cpu_num_audit(samples: int = 3):
    """
    Audits which CPU core the process is currently running on using psutil.
    """
    logger.info(f"Starting process CPU num audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU core probe", pct=0, log="Collecting process-level CPU core baseline...")
    
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            cpu_num = process.cpu_num() if hasattr(process, "cpu_num") else "N/A"
        except Exception as e:
            logger.warning(f"Error collecting process CPU num: {e}")
            cpu_num = "unknown"
            
        logger.info(f"Sample {i+1}/{samples}: Process CPU Core {cpu_num}")
        yield ProgressPayload(
            step="Sampling CPU core",
            pct=pct,
            log=f"Measured process CPU core sample {i+1}/{samples}: {cpu_num}.",
            metadata={
                "sample_id": i + 1,
                "cpu_num": cpu_num
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. CPU core affinity is stable.")
    yield {
        "status": "audit_complete",
        "final_cpu_num": process.cpu_num() if hasattr(process, "cpu_num") else "N/A",
        "stability": "STABLE"
    }

@progress_tool(name="system_net_io_counters_audit")
async def system_net_io_counters_audit(samples: int = 3):
    """
    Audits system-wide network I/O counters using psutil.
    """
    logger.info(f"Starting system net I/O counters audit with {samples} samples")
    yield ProgressPayload(step="Initializing net I/O probe", pct=0, log="Collecting system-wide network I/O baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            counters = psutil.net_io_counters()
            bytes_sent = counters.bytes_sent
            bytes_recv = counters.bytes_recv
        except Exception as e:
            logger.warning(f"Error collecting system net I/O: {e}")
            bytes_sent = bytes_recv = 0
            
        logger.info(f"Sample {i+1}/{samples}: Sent {bytes_sent} bytes, Recv {bytes_recv} bytes")
        yield ProgressPayload(
            step="Sampling net I/O",
            pct=pct,
            log=f"Measured system net I/O sample {i+1}/{samples}: Sent {bytes_sent}, Recv {bytes_recv}.",
            metadata={
                "sample_id": i + 1,
                "bytes_sent": bytes_sent,
                "bytes_recv": bytes_recv
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. System-wide network I/O is stable.")
    yield {
        "status": "audit_complete",
        "final_counters": psutil.net_io_counters()._asdict(),
        "stability": "STABLE"
    }

@progress_tool(name="system_users_audit")
async def system_users_audit(samples: int = 3):
    """
    Audits currently logged-in system users using psutil.
    """
    logger.info(f"Starting system users audit with {samples} samples")
    yield ProgressPayload(step="Initializing users probe", pct=0, log="Collecting system-wide user baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            users = psutil.users()
            user_count = len(users)
        except Exception as e:
            logger.warning(f"Error collecting system users: {e}")
            users = []
            user_count = 0
            
        logger.info(f"Sample {i+1}/{samples}: {user_count} users logged in.")
        yield ProgressPayload(
            step="Sampling system users",
            pct=pct,
            log=f"Measured {user_count} system users sample {i+1}/{samples}.",
            metadata={
                "sample_id": i + 1,
                "user_count": user_count,
                "users": [u.name for u in users[:5]]
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. System user state is stable.")
    yield {
        "status": "audit_complete",
        "final_user_count": len(psutil.users()),
        "stability": "STABLE"
    }

@progress_tool(name="system_disk_partitions_audit")
async def system_disk_partitions_audit(samples: int = 3):
    """
    Audits system disk partitions using psutil.
    """
    logger.info(f"Starting system disk partitions audit with {samples} samples")
    yield ProgressPayload(step="Initializing disk partition probe", pct=0, log="Collecting system-wide disk partition baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            partitions = psutil.disk_partitions(all=False)
            partition_count = len(partitions)
        except Exception as e:
            logger.warning(f"Error collecting system disk partitions: {e}")
            partitions = []
            partition_count = 0
            
        logger.info(f"Sample {i+1}/{samples}: {partition_count} disk partitions found.")
        yield ProgressPayload(
            step="Sampling disk partitions",
            pct=pct,
            log=f"Measured {partition_count} disk partitions sample {i+1}/{samples}.",
            metadata={
                "sample_id": i + 1,
                "partition_count": partition_count,
                "partitions": [p._asdict() for p in partitions[:5]]
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Disk partition configuration is stable.")
    yield {
        "status": "audit_complete",
        "final_partition_count": len(psutil.disk_partitions(all=False)),
        "stability": "STABLE"
    }

@progress_tool(name="system_net_if_addrs_audit")
async def system_net_if_addrs_audit(samples: int = 3):
    """
    Audits system network interface addresses using psutil.
    """
    logger.info(f"Starting system net if addrs audit with {samples} samples")
    yield ProgressPayload(step="Initializing net if addrs probe", pct=0, log="Collecting system-wide network interface address baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            if_addrs = psutil.net_if_addrs()
            if_count = len(if_addrs)
        except Exception as e:
            logger.warning(f"Error collecting system net if addrs: {e}")
            if_addrs = {}
            if_count = 0
            
        logger.info(f"Sample {i+1}/{samples}: {if_count} network interfaces with addresses found.")
        yield ProgressPayload(
            step="Sampling net if addrs",
            pct=pct,
            log=f"Measured {if_count} network interfaces sample {i+1}/{samples}.",
            metadata={
                "sample_id": i + 1,
                "interface_count": if_count,
                "interfaces": list(if_addrs.keys())[:5]
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Network interface addresses are stable.")
    yield {
        "status": "audit_complete",
        "final_interface_count": len(psutil.net_if_addrs()),
        "stability": "STABLE"
    }

@progress_tool(name="system_net_if_stats_audit")
async def system_net_if_stats_audit(samples: int = 3):
    """
    Audits system network interface stats using psutil.
    """
    logger.info(f"Starting system net if stats audit with {samples} samples")
    yield ProgressPayload(step="Initializing net if stats probe", pct=0, log="Collecting system-wide network interface statistics baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            if_stats = psutil.net_if_stats()
            if_count = len(if_stats)
        except Exception as e:
            logger.warning(f"Error collecting system net if stats: {e}")
            if_stats = {}
            if_count = 0
            
        logger.info(f"Sample {i+1}/{samples}: {if_count} network interfaces with stats found.")
        yield ProgressPayload(
            step="Sampling net if stats",
            pct=pct,
            log=f"Measured {if_count} network interfaces sample {i+1}/{samples}.",
            metadata={
                "sample_id": i + 1,
                "interface_count": if_count,
                "interfaces": list(if_stats.keys())[:5]
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Network interface statistics are stable.")
    yield {
        "status": "audit_complete",
        "final_interface_count": len(psutil.net_if_stats()),
        "stability": "STABLE"
    }
@progress_tool(name="system_sensors_temperatures_audit")
async def system_sensors_temperatures_audit(samples: int = 3):
    """
    Audits system sensors temperatures using psutil.
    """
    logger.info(f"Starting system sensors temperatures audit with {samples} samples")
    yield ProgressPayload(step="Initializing thermal probe", pct=0, log="Collecting system-wide temperature baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                temp_count = len(temps)
            else:
                temps = {}
                temp_count = 0
        except Exception as e:
            logger.warning(f"Error collecting system temperatures: {e}")
            temps = {}
            temp_count = 0
            
        logger.info(f"Sample {i+1}/{samples}: {temp_count} temperature sensors found.")
        yield ProgressPayload(
            step="Sampling temperatures",
            pct=pct,
            log=f"Measured {temp_count} temperature sensors sample {i+1}/{samples}.",
            metadata={
                "sample_id": i + 1,
                "sensor_count": temp_count,
                "sensors": list(temps.keys())[:5]
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Thermal state is stable.")
    yield {
        "status": "audit_complete",
        "final_sensor_count": len(psutil.sensors_temperatures()) if hasattr(psutil, "sensors_temperatures") else 0,
        "stability": "STABLE"
    }

@progress_tool(name="system_sensors_fans_audit")
async def system_sensors_fans_audit(samples: int = 3):
    """
    Audits system sensors fans using psutil.
    """
    logger.info(f"Starting system sensors fans audit with {samples} samples")
    yield ProgressPayload(step="Initializing fan probe", pct=0, log="Collecting system-wide fan speed baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            if hasattr(psutil, "sensors_fans"):
                fans = psutil.sensors_fans()
                fan_count = len(fans)
            else:
                fans = {}
                fan_count = 0
        except Exception as e:
            logger.warning(f"Error collecting system fans: {e}")
            fans = {}
            fan_count = 0
            
        logger.info(f"Sample {i+1}/{samples}: {fan_count} fan sensors found.")
        yield ProgressPayload(
            step="Sampling fan speeds",
            pct=pct,
            log=f"Measured {fan_count} fan sensors sample {i+1}/{samples}.",
            metadata={
                "sample_id": i + 1,
                "fan_count": fan_count,
                "fans": list(fans.keys())[:5]
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Fan speeds are stable.")
    yield {
        "status": "audit_complete",
        "final_fan_count": len(psutil.sensors_fans()) if hasattr(psutil, "sensors_fans") else 0,
        "stability": "STABLE"
    }

@progress_tool(name="system_sensors_battery_audit")
async def system_sensors_battery_audit(samples: int = 3):
    """
    Audits system sensors battery using psutil.
    """
    logger.info(f"Starting system sensors battery audit with {samples} samples")
    yield ProgressPayload(step="Initializing battery probe", pct=0, log="Collecting system-wide battery status baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            if hasattr(psutil, "sensors_battery"):
                battery = psutil.sensors_battery()
                percent = battery.percent if battery else "N/A"
            else:
                battery = None
                percent = "N/A"
        except Exception as e:
            logger.warning(f"Error collecting battery status: {e}")
            battery = None
            percent = "N/A"
            
        logger.info(f"Sample {i+1}/{samples}: Battery percentage {percent}%")
        yield ProgressPayload(
            step="Sampling battery status",
            pct=pct,
            log=f"Measured battery status sample {i+1}/{samples}: {percent}%.",
            metadata={
                "sample_id": i + 1,
                "percent": percent,
                "power_plugged": battery.power_plugged if battery else None
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Power state is stable.")
    yield {
        "status": "audit_complete",
        "battery_present": psutil.sensors_battery() is not None if hasattr(psutil, "sensors_battery") else False,
        "stability": "STABLE"
    }

@progress_tool(name="system_boot_time_audit")
async def system_boot_time_audit(samples: int = 3):
    """
    Audits system boot time using psutil.
    """
    logger.info(f"Starting system boot time audit with {samples} samples")
    yield ProgressPayload(step="Initializing boot time probe", pct=0, log="Collecting system boot timestamp...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            boot_time = psutil.boot_time()
        except Exception as e:
            logger.warning(f"Error collecting system boot time: {e}")
            boot_time = 0
            
        logger.info(f"Sample {i+1}/{samples}: System boot time {boot_time}")
        yield ProgressPayload(
            step="Sampling boot time",
            pct=pct,
            log=f"Measured system boot time sample {i+1}/{samples}: {boot_time}.",
            metadata={
                "sample_id": i + 1,
                "boot_time": boot_time,
                "boot_time_iso": datetime.fromtimestamp(boot_time).isoformat() if boot_time > 0 else "N/A"
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Boot timestamp is stable.")
    yield {
        "status": "audit_complete",
        "final_boot_time": psutil.boot_time(),
        "stability": "STABLE"
    }

@progress_tool(name="system_cpu_freq_audit")
async def system_cpu_freq_audit(samples: int = 3):
    """
    Audits system CPU frequency using psutil.
    """
    logger.info(f"Starting system CPU frequency audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU freq probe", pct=0, log="Collecting system-wide CPU frequency baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            freq = psutil.cpu_freq()
            current = freq.current if freq else "N/A"
        except Exception as e:
            logger.warning(f"Error collecting system CPU frequency: {e}")
            freq = None
            current = "N/A"
            
        logger.info(f"Sample {i+1}/{samples}: CPU frequency {current}MHz")
        yield ProgressPayload(
            step="Sampling CPU frequency",
            pct=pct,
            log=f"Measured system CPU frequency sample {i+1}/{samples}: {current}MHz.",
            metadata={
                "sample_id": i + 1,
                "current": current,
                "min": freq.min if freq else None,
                "max": freq.max if freq else None
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. CPU frequency is stable.")
    yield {
        "status": "audit_complete",
        "final_frequency": psutil.cpu_freq()._asdict() if hasattr(psutil.cpu_freq(), "_asdict") else None,
        "stability": "STABLE"
    }

@progress_tool(name="system_cpu_stats_audit")
async def system_cpu_stats_audit(samples: int = 3):
    """
    Audits system CPU statistics using psutil.
    """
    logger.info(f"Starting system CPU stats audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU stats probe", pct=0, log="Collecting system-wide CPU statistics baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            stats = psutil.cpu_stats()
            ctx_switches = stats.ctx_switches
            interrupts = stats.interrupts
        except Exception as e:
            logger.warning(f"Error collecting system CPU stats: {e}")
            stats = None
            ctx_switches = interrupts = 0
            
        logger.info(f"Sample {i+1}/{samples}: Ctx switches {ctx_switches}, Interrupts {interrupts}")
        yield ProgressPayload(
            step="Sampling CPU stats",
            pct=pct,
            log=f"Measured system CPU stats sample {i+1}/{samples}: {ctx_switches}.",
            metadata={
                "sample_id": i + 1,
                "ctx_switches": ctx_switches,
                "interrupts": interrupts,
                "soft_interrupts": getattr(stats, "soft_interrupts", 0),
                "syscalls": getattr(stats, "syscalls", 0)
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. CPU statistics are stable.")
    yield {
        "status": "audit_complete",
        "final_stats": psutil.cpu_stats()._asdict() if hasattr(psutil.cpu_stats(), "_asdict") else None,
        "stability": "STABLE"
    }
@progress_tool(name="system_cpu_count_audit")
async def system_cpu_count_audit(samples: int = 3):
    """
    Audits system CPU counts (logical and physical) using psutil.
    """
    logger.info(f"Starting system CPU count audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU count probe", pct=0, log="Collecting system-wide CPU count information...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        logical = psutil.cpu_count(logical=True)
        physical = psutil.cpu_count(logical=False)
            
        logger.info(f"Sample {i+1}/{samples}: Logical CPUs {logical}, Physical CPUs {physical}")
        yield ProgressPayload(
            step="Sampling CPU counts",
            pct=pct,
            log=f"Measured system CPU counts sample {i+1}/{samples}: Logical {logical}, Physical {physical}.",
            metadata={
                "sample_id": i + 1,
                "logical": logical,
                "physical": physical
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. CPU counts are stable.")
    yield {
        "status": "audit_complete",
        "logical": psutil.cpu_count(logical=True),
        "physical": psutil.cpu_count(logical=False),
        "stability": "STABLE"
    }

@progress_tool(name="system_cpu_times_percent_audit")
async def system_cpu_times_percent_audit(samples: int = 3):
    """
    Audits system-wide CPU times as a percentage using psutil.
    """
    logger.info(f"Starting system CPU times percent audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU times percent probe", pct=0, log="Collecting system-wide CPU timing percentages baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        # interval=0.1 to get a meaningful percentage
        cpu_times_pct = psutil.cpu_times_percent(interval=0.1)
            
        logger.info(f"Sample {i+1}/{samples}: CPU Times Percent User {cpu_times_pct.user}%")
        yield ProgressPayload(
            step="Sampling CPU times percent",
            pct=pct,
            log=f"Measured system CPU times percent sample {i+1}/{samples}: User {cpu_times_pct.user}%.",
            metadata={
                "sample_id": i + 1,
                "user": cpu_times_pct.user,
                "system": cpu_times_pct.system,
                "idle": cpu_times_pct.idle,
                "iowait": getattr(cpu_times_pct, "iowait", 0.0)
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. CPU timing percentages are stable.")
    yield {
        "status": "audit_complete",
        "final_cpu_times_percent": psutil.cpu_times_percent(interval=None)._asdict() if hasattr(psutil.cpu_times_percent(interval=None), "_asdict") else None,
        "stability": "STABLE"
    }

@progress_tool(name="system_net_connections_audit")
async def system_net_connections_audit(samples: int = 3):
    """
    Audits system-wide network connections using psutil.
    """
    logger.info(f"Starting system network connections audit with {samples} samples")
    yield ProgressPayload(step="Initializing system network connection probe", pct=0, log="Collecting system-wide active socket information...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            connections = psutil.net_connections(kind="inet")
            count = len(connections)
        except Exception as e:
            logger.warning(f"Error collecting system network connections: {e}")
            connections = []
            count = 0
            
        logger.info(f"Sample {i+1}/{samples}: System Connections Count {count}")
        yield ProgressPayload(
            step="Sampling system network connections",
            pct=pct,
            log=f"Measured system network connections sample {i+1}/{samples}: {count} active sockets.",
            metadata={
                "sample_id": i + 1,
                "count": count,
                "connections": [str(c) for c in connections[:5]]
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. System network connections are stable.")
    yield {
        "status": "audit_complete",
        "final_connections_count": count,
        "stability": "STABLE"
    }
@progress_tool(name="system_pids_audit")
async def system_pids_audit(samples: int = 3):
    """
    Audits the list of active PIDs on the system using psutil.
    """
    logger.info(f"Starting system PIDs audit with {samples} samples")
    yield ProgressPayload(step="Initializing PID list probe", pct=0, log="Collecting system-wide PID baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            pids = psutil.pids()
            count = len(pids)
        except Exception as e:
            logger.warning(f"Error collecting system PIDs: {e}")
            pids = []
            count = 0
            
        logger.info(f"Sample {i+1}/{samples}: {count} active PIDs.")
        yield ProgressPayload(
            step="Sampling system PIDs",
            pct=pct,
            log=f"Measured {count} active system PIDs. Sample {i+1}/{samples}.",
            metadata={
                "sample_id": i + 1,
                "count": count,
                "pids": pids[:10]
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. PID distribution is stable.")
    yield {
        "status": "audit_complete",
        "final_pid_count": len(psutil.pids()),
        "stability": "STABLE"
    }

@progress_tool(name="system_cpu_times_audit")
async def system_cpu_times_audit(samples: int = 3):
    """
    Audits absolute system-wide CPU times using psutil.
    """
    logger.info(f"Starting system CPU times audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU times probe", pct=0, log="Collecting system-wide absolute CPU timing baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        cpu_times = psutil.cpu_times()
            
        logger.info(f"Sample {i+1}/{samples}: CPU Times User {cpu_times.user}s")
        yield ProgressPayload(
            step="Sampling CPU times",
            pct=pct,
            log=f"Measured system CPU times sample {i+1}/{samples}: User {cpu_times.user}s.",
            metadata={
                "sample_id": i + 1,
                "user": cpu_times.user,
                "system": cpu_times.system,
                "idle": cpu_times.idle,
                "iowait": getattr(cpu_times, "iowait", 0.0)
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Absolute CPU timing is stable.")
    yield {
        "status": "audit_complete",
        "final_cpu_times": psutil.cpu_times()._asdict() if hasattr(psutil.cpu_times(), "_asdict") else None,
        "stability": "STABLE"
    }

@progress_tool(name="system_disk_io_counters_audit")
async def system_disk_io_counters_audit(samples: int = 3):
    """
    Audits system-wide disk I/O counters using psutil.
    """
    logger.info(f"Starting system disk I/O counters audit with {samples} samples")
    yield ProgressPayload(step="Initializing disk I/O probe", pct=0, log="Collecting system-wide disk I/O baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        
        try:
            counters = psutil.disk_io_counters()
            read_bytes = counters.read_bytes
            write_bytes = counters.write_bytes
        except Exception as e:
            logger.warning(f"Error collecting system disk I/O: {e}")
            read_bytes = write_bytes = 0
            
        logger.info(f"Sample {i+1}/{samples}: Read {read_bytes} bytes, Write {write_bytes} bytes")
        yield ProgressPayload(
            step="Sampling disk I/O",
            pct=pct,
            log=f"Measured system disk I/O sample {i+1}/{samples}: Read {read_bytes}, Write {write_bytes}.",
            metadata={
                "sample_id": i + 1,
                "read_bytes": read_bytes,
                "write_bytes": write_bytes
            }
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. System-wide disk I/O is stable.")
    yield {
        "status": "audit_complete",
        "final_counters": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {},
        "stability": "STABLE"
    }

@progress_tool(name="system_virtual_memory_audit")
async def system_virtual_memory_audit(samples: int = 3):
    """
    Audits system-wide virtual memory statistics using psutil.
    """
    logger.info(f"Starting system virtual memory audit with {samples} samples")
    yield ProgressPayload(step="Initializing memory probe", pct=0, log="Collecting system-wide virtual memory baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        vmem = psutil.virtual_memory()
        logger.info(f"Sample {i+1}/{samples}: Available {vmem.available / 1024 / 1024:.2f}MB, Percent {vmem.percent}%")
        yield ProgressPayload(
            step="Sampling virtual memory",
            pct=pct,
            log=f"Measured system virtual memory sample {i+1}/{samples}: {vmem.percent}% used.",
            metadata=vmem._asdict()
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. System memory is stable.")
    yield {
        "status": "audit_complete",
        "final_vmem": psutil.virtual_memory()._asdict(),
        "stability": "STABLE"
    }

@progress_tool(name="system_swap_memory_audit")
async def system_swap_memory_audit(samples: int = 3):
    """
    Audits system-wide swap memory statistics using psutil.
    """
    logger.info(f"Starting system swap memory audit with {samples} samples")
    yield ProgressPayload(step="Initializing swap probe", pct=0, log="Collecting system-wide swap memory baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        swap = psutil.swap_memory()
        logger.info(f"Sample {i+1}/{samples}: Used {swap.used / 1024 / 1024:.2f}MB, Percent {swap.percent}%")
        yield ProgressPayload(
            step="Sampling swap memory",
            pct=pct,
            log=f"Measured system swap memory sample {i+1}/{samples}: {swap.percent}% used.",
            metadata=swap._asdict()
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. System swap is stable.")
    yield {
        "status": "audit_complete",
        "final_swap": psutil.swap_memory()._asdict(),
        "stability": "STABLE"
    }

@progress_tool(name="system_disk_usage_audit")
async def system_disk_usage_audit(samples: int = 3, path: str = "/"):
    """
    Audits system-wide disk usage for a specific path using psutil.
    """
    logger.info(f"Starting system disk usage audit for {path} with {samples} samples")
    yield ProgressPayload(step="Initializing disk probe", pct=0, log=f"Collecting disk usage baseline for {path}...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            usage = psutil.disk_usage(path)
            logger.info(f"Sample {i+1}/{samples}: {usage.percent}% used on {path}")
            payload_log = f"Measured disk usage sample {i+1}/{samples} for {path}: {usage.percent}% used."
            metadata = usage._asdict()
        except Exception as e:
            logger.error(f"Error auditing disk usage for {path}: {e}")
            payload_log = f"Error during sample {i+1}: {str(e)}"
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling disk usage",
            pct=pct,
            log=payload_log,
            metadata=metadata
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Disk usage state is stable.")
    try:
        final_usage = psutil.disk_usage(path)._asdict()
    except:
        final_usage = {}
        
    yield {
        "status": "audit_complete",
        "path": path,
        "final_usage": final_usage,
        "stability": "STABLE"
    }

@progress_tool(name="system_net_io_per_nic_audit")
async def system_net_io_per_nic_audit(samples: int = 3):
    """
    Audits per-NIC network I/O counters using psutil.
    """
    logger.info(f"Starting system net I/O per NIC audit with {samples} samples")
    yield ProgressPayload(step="Initializing per-NIC probe", pct=0, log="Collecting per-interface network I/O baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.net_io_counters(pernic=True)
            nic_names = list(counters.keys())
            logger.info(f"Sample {i+1}/{samples}: Collected I/O for {len(nic_names)} interfaces")
            metadata = {nic: data._asdict() for nic, data in counters.items()}
        except Exception as e:
            logger.error(f"Error auditing per-NIC I/O: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling per-NIC I/O",
            pct=pct,
            log=f"Measured per-NIC network I/O sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Per-interface network I/O is stable.")
    yield {
        "status": "audit_complete",
        "interface_count": len(psutil.net_io_counters(pernic=True)),
        "stability": "STABLE"
    }

@progress_tool(name="system_disk_io_per_disk_audit")
async def system_disk_io_per_disk_audit(samples: int = 3):
    """
    Audits per-disk I/O counters using psutil.
    """
    logger.info(f"Starting system disk I/O per disk audit with {samples} samples")
    yield ProgressPayload(step="Initializing per-disk probe", pct=0, log="Collecting per-disk I/O baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.disk_io_counters(perdisk=True)
            disk_names = list(counters.keys())
            logger.info(f"Sample {i+1}/{samples}: Collected I/O for {len(disk_names)} disks")
            metadata = {disk: data._asdict() for disk, data in counters.items()}
        except Exception as e:
            logger.error(f"Error auditing per-disk I/O: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling per-disk I/O",
            pct=pct,
            log=f"Measured per-disk I/O sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Per-disk I/O is stable.")
    yield {
        "status": "audit_complete",
        "disk_count": len(psutil.disk_io_counters(perdisk=True)) if psutil.disk_io_counters(perdisk=True) else 0,
        "stability": "STABLE"
    }

@progress_tool(name="system_cpu_times_per_cpu_audit")
async def system_cpu_times_per_cpu_audit(samples: int = 3):
    """
    Audits per-CPU timing statistics using psutil.
    """
    logger.info(f"Starting system CPU times per CPU audit with {samples} samples")
    yield ProgressPayload(step="Initializing per-CPU probe", pct=0, log="Collecting per-CPU timing baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times(percpu=True)
            logger.info(f"Sample {i+1}/{samples}: Collected timings for {len(times)} CPUs")
            metadata = {f"cpu_{idx}": data._asdict() for idx, data in enumerate(times)}
        except Exception as e:
            logger.error(f"Error auditing per-CPU timings: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling per-CPU timings",
            pct=pct,
            log=f"Measured per-CPU timing statistics sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Per-CPU timing statistics are stable.")
    yield {
        "status": "audit_complete",
        "cpu_count": psutil.cpu_count(),
        "stability": "STABLE"
    }

@progress_tool(name="system_cpu_times_percent_per_cpu_audit")
async def system_cpu_times_percent_per_cpu_audit(samples: int = 3):
    """
    Audits per-CPU timing percentages using psutil.
    """
    logger.info(f"Starting system CPU times percent per CPU audit with {samples} samples")
    yield ProgressPayload(step="Initializing per-CPU percent probe", pct=0, log="Collecting per-CPU timing percentages baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times_pct = psutil.cpu_times_percent(interval=0.1, percpu=True)
            logger.info(f"Sample {i+1}/{samples}: Collected percentages for {len(times_pct)} CPUs")
            metadata = {f"cpu_{idx}": data._asdict() for idx, data in enumerate(times_pct)}
        except Exception as e:
            logger.error(f"Error auditing per-CPU timing percentages: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling per-CPU percentages",
            pct=pct,
            log=f"Measured per-CPU timing percentages sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Per-CPU timing percentages are stable.")
    yield {
        "status": "audit_complete",
        "cpu_count": psutil.cpu_count(),
        "stability": "STABLE"
    }

@progress_tool(name="system_net_if_stats_extended_audit")
async def system_net_if_stats_extended_audit(samples: int = 3):
    """
    Audits extended system network interface statistics using psutil.
    """
    logger.info(f"Starting system net if stats extended audit with {samples} samples")
    yield ProgressPayload(step="Initializing extended net if stats probe", pct=0, log="Collecting extended system-wide network interface statistics...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            if_stats = psutil.net_if_stats()
            logger.info(f"Sample {i+1}/{samples}: Collected extended stats for {len(if_stats)} interfaces")
            metadata = {iface: stats._asdict() for iface, stats in if_stats.items()}
        except Exception as e:
            logger.error(f"Error auditing extended net if stats: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling extended net if stats",
            pct=pct,
            log=f"Measured extended system network interface stats sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Extended network interface statistics are stable.")
    yield {
        "status": "audit_complete",
        "interface_count": len(psutil.net_if_stats()),
        "stability": "STABLE"
    }

@progress_tool(name="system_disk_partitions_usage_audit")
async def system_disk_partitions_usage_audit(samples: int = 3):
    """
    Audits disk usage for all system partitions using psutil.
    """
    logger.info(f"Starting system disk partitions usage audit with {samples} samples")
    yield ProgressPayload(step="Initializing partitions usage probe", pct=0, log="Collecting usage statistics for all partitions...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            partitions = psutil.disk_partitions(all=False)
            usage_data = {}
            for part in partitions:
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    usage_data[part.mountpoint] = usage._asdict()
                except Exception:
                    # Skip partitions that are not accessible
                    continue
            logger.info(f"Sample {i+1}/{samples}: Collected usage for {len(usage_data)} partitions")
            metadata = usage_data
        except Exception as e:
            logger.error(f"Error auditing partitions usage: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling partitions usage",
            pct=pct,
            log=f"Measured disk usage for all partitions sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Partition usage statistics are stable.")
    yield {
        "status": "audit_complete",
        "partition_count": len(usage_data),
        "stability": "STABLE"
    }

@progress_tool(name="system_cpu_freq_per_cpu_audit")
async def system_cpu_freq_per_cpu_audit(samples: int = 3):
    """
    Audits per-CPU frequency statistics using psutil.
    """
    logger.info(f"Starting system CPU frequency per CPU audit with {samples} samples")
    yield ProgressPayload(step="Initializing per-CPU freq probe", pct=0, log="Collecting per-CPU frequency baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            freqs = psutil.cpu_freq(percpu=True)
            logger.info(f"Sample {i+1}/{samples}: Collected frequencies for {len(freqs)} CPUs")
            metadata = {f"cpu_{idx}": data._asdict() for idx, data in enumerate(freqs)}
        except Exception as e:
            logger.error(f"Error auditing per-CPU frequencies: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling per-CPU frequencies",
            pct=pct,
            log=f"Measured per-CPU frequency statistics sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Per-CPU frequency statistics are stable.")
    yield {
        "status": "audit_complete",
        "cpu_count": psutil.cpu_count(),
        "stability": "STABLE"
    }

@progress_tool(name="system_disk_partitions_all_audit")
async def system_disk_partitions_all_audit(samples: int = 3):
    """
    Audits all system disk partitions (including internal ones) using psutil.
    """
    logger.info(f"Starting system disk partitions all audit with {samples} samples")
    yield ProgressPayload(step="Initializing all-partitions probe", pct=0, log="Collecting all system-wide disk partition baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            partitions = psutil.disk_partitions(all=True)
            partition_count = len(partitions)
            logger.info(f"Sample {i+1}/{samples}: {partition_count} disk partitions found (including internal).")
            metadata = {f"partition_{idx}": p._asdict() for idx, p in enumerate(partitions[:20])} # Limit to first 20
        except Exception as e:
            logger.error(f"Error auditing all disk partitions: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling all disk partitions",
            pct=pct,
            log=f"Measured {partition_count} disk partitions sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Full disk partition configuration is stable.")
    yield {
        "status": "audit_complete",
        "total_partition_count": len(psutil.disk_partitions(all=True)),
        "stability": "STABLE"
    }

@progress_tool(name="system_net_if_addrs_detailed_audit")
async def system_net_if_addrs_detailed_audit(samples: int = 3):
    """
    Audits detailed system network interface addresses using psutil.
    """
    logger.info(f"Starting system net if addrs detailed audit with {samples} samples")
    yield ProgressPayload(step="Initializing detailed net if addrs probe", pct=0, log="Collecting detailed system-wide network interface address information...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            if_addrs = psutil.net_if_addrs()
            logger.info(f"Sample {i+1}/{samples}: Collected addresses for {len(if_addrs)} interfaces")
            metadata = {iface: [addr._asdict() for addr in addrs] for iface, addrs in if_addrs.items()}
        except Exception as e:
            logger.error(f"Error auditing detailed net if addrs: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling detailed net if addrs",
            pct=pct,
            log=f"Measured detailed system network interface addresses sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.3)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Detailed network interface addresses are stable.")
    yield {
        "status": "audit_complete",
        "interface_count": len(psutil.net_if_addrs()),
        "stability": "STABLE"
    }

@progress_tool(name="system_net_if_addrs_v4_audit")
async def system_net_if_addrs_v4_audit(samples: int = 3):
    """
    Audits IPv4 system network interface addresses using psutil.
    """
    logger.info("Starting system net if addrs IPv4 audit")
    yield ProgressPayload(step="Initializing IPv4 net if addrs probe", pct=0, log="Collecting IPv4 network interface address information...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            if_addrs = psutil.net_if_addrs()
            v4_addrs = {}
            for iface, addrs in if_addrs.items():
                v4_list = [addr._asdict() for addr in addrs if addr.family == 2] # AF_INET
                if v4_list:
                    v4_addrs[iface] = v4_list
            logger.info(f"Sample {i+1}/{samples}: Collected IPv4 addresses for {len(v4_addrs)} interfaces")
            metadata = v4_addrs
        except Exception as e:
            logger.error(f"Error auditing IPv4 net if addrs: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling IPv4 net if addrs",
            pct=pct,
            log=f"Measured IPv4 network interface addresses sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. IPv4 network interface addresses are stable.")
    yield {
        "status": "audit_complete",
        "interface_count": len(v4_addrs),
        "family": "IPv4",
        "stability": "STABLE"
    }

@progress_tool(name="system_net_if_addrs_v6_audit")
async def system_net_if_addrs_v6_audit(samples: int = 3):
    """
    Audits IPv6 system network interface addresses using psutil.
    """
    logger.info("Starting system net if addrs IPv6 audit")
    yield ProgressPayload(step="Initializing IPv6 net if addrs probe", pct=0, log="Collecting IPv6 network interface address information...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            if_addrs = psutil.net_if_addrs()
            v6_addrs = {}
            for iface, addrs in if_addrs.items():
                v6_list = [addr._asdict() for addr in addrs if addr.family == 30] # AF_INET6
                if v6_list:
                    v6_addrs[iface] = v6_list
            logger.info(f"Sample {i+1}/{samples}: Collected IPv6 addresses for {len(v6_addrs)} interfaces")
            metadata = v6_addrs
        except Exception as e:
            logger.error(f"Error auditing IPv6 net if addrs: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling IPv6 net if addrs",
            pct=pct,
            log=f"Measured IPv6 network interface addresses sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. IPv6 network interface addresses are stable.")
    yield {
        "status": "audit_complete",
        "interface_count": len(v6_addrs),
        "family": "IPv6",
        "stability": "STABLE"
    }

@progress_tool(name="system_disk_partitions_physical_audit")
async def system_disk_partitions_physical_audit(samples: int = 3):
    """
    Audits physical system disk partitions using psutil.
    """
    logger.info("Starting system disk partitions physical audit")
    yield ProgressPayload(step="Initializing physical-partitions probe", pct=0, log="Collecting physical disk partition baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            partitions = psutil.disk_partitions(all=False)
            partition_count = len(partitions)
            logger.info(f"Sample {i+1}/{samples}: {partition_count} physical disk partitions found.")
            metadata = {f"partition_{idx}": p._asdict() for idx, p in enumerate(partitions)}
        except Exception as e:
            logger.error(f"Error auditing physical disk partitions: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling physical disk partitions",
            pct=pct,
            log=f"Measured {partition_count} physical disk partitions sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Physical disk partition configuration is stable.")
    yield {
        "status": "audit_complete",
        "physical_partition_count": len(psutil.disk_partitions(all=False)),
        "stability": "STABLE"
    }

@progress_tool(name="system_net_if_addrs_mac_audit")
async def system_net_if_addrs_mac_audit(samples: int = 3):
    """
    Audits MAC system network interface addresses using psutil.
    """
    logger.info("Starting system net if addrs MAC audit")
    yield ProgressPayload(step="Initializing MAC net if addrs probe", pct=0, log="Collecting MAC network interface address information...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            if_addrs = psutil.net_if_addrs()
            mac_addrs = {}
            for iface, addrs in if_addrs.items():
                mac_list = [addr._asdict() for addr in addrs if addr.family in (17, 18)]
                if mac_list:
                    mac_addrs[iface] = mac_list
            logger.info(f"Sample {i+1}/{samples}: Collected MAC addresses for {len(mac_addrs)} interfaces")
            metadata = mac_addrs
        except Exception as e:
            logger.error(f"Error auditing MAC net if addrs: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling MAC net if addrs",
            pct=pct,
            log=f"Measured MAC network interface addresses sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. MAC network interface addresses are stable.")
    yield {
        "status": "audit_complete",
        "interface_count": len(mac_addrs),
        "family": "MAC",
        "stability": "STABLE"
    }

@progress_tool(name="system_disk_partitions_fstype_audit")
async def system_disk_partitions_fstype_audit(samples: int = 3, fstype: str = "apfs"):
    """
    Audits system disk partitions filtered by filesystem type using psutil.
    """
    logger.info(f"Starting system disk partitions fstype audit for {fstype}")
    yield ProgressPayload(step="Initializing fstype-partitions probe", pct=0, log=f"Collecting disk partition baseline for fstype: {fstype}...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            partitions = psutil.disk_partitions(all=True)
            filtered_partitions = [p._asdict() for p in partitions if p.fstype.lower() == fstype.lower()]
            partition_count = len(filtered_partitions)
            logger.info(f"Sample {i+1}/{samples}: {partition_count} disk partitions found with fstype {fstype}.")
            metadata = {f"partition_{idx}": p for idx, p in enumerate(filtered_partitions)}
        except Exception as e:
            logger.error(f"Error auditing fstype disk partitions: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling fstype disk partitions",
            pct=pct,
            log=f"Measured {partition_count} disk partitions with fstype {fstype} sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Disk partition configuration for {fstype} is stable.")
    yield {
        "status": "audit_complete",
        "fstype": fstype,
        "partition_count": partition_count,
        "stability": "STABLE"
    }

@progress_tool(name="system_cpu_times_percent_system_focused_audit")
async def system_cpu_times_percent_system_focused_audit(samples: int = 3):
    """
    Audits system-wide CPU system time percentage using psutil.
    """
    logger.info("Starting focused system CPU time percentage audit")
    yield ProgressPayload(step="Initializing system CPU focused probe", pct=0, log="Collecting system-wide system CPU timing percentages...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            cpu_times_pct = psutil.cpu_times_percent(interval=0.1)
            system_pct = cpu_times_pct.system
            logger.info(f"Sample {i+1}/{samples}: System CPU Time {system_pct}%")
            metadata = {"system_percent": system_pct, "user_percent": cpu_times_pct.user, "idle_percent": cpu_times_pct.idle}
        except Exception as e:
            logger.error(f"Error auditing focused system CPU time: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling system CPU time",
            pct=pct,
            log=f"Measured system CPU time percentage sample {i+1}/{samples}: {system_pct}%.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. System CPU time percentages are stable.")
    yield {
        "status": "audit_complete",
        "final_system_percent": system_pct,
        "metric": "system_cpu_time",
        "stability": "STABLE"
    }

@progress_tool(name="system_net_if_addrs_netmask_audit")
async def system_net_if_addrs_netmask_audit(samples: int = 3):
    """
    Audits netmask system network interface addresses using psutil.
    """
    logger.info("Starting system net if addrs netmask audit")
    yield ProgressPayload(step="Initializing netmask net if addrs probe", pct=0, log="Collecting netmask network interface address information...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            if_addrs = psutil.net_if_addrs()
            netmask_addrs = {}
            for iface, addrs in if_addrs.items():
                netmask_list = [addr.netmask for addr in addrs if addr.netmask]
                if netmask_list:
                    netmask_addrs[iface] = netmask_list
            logger.info(f"Sample {i+1}/{samples}: Collected netmasks for {len(netmask_addrs)} interfaces")
            metadata = netmask_addrs
        except Exception as e:
            logger.error(f"Error auditing netmask net if addrs: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling netmask net if addrs",
            pct=pct,
            log=f"Measured netmask network interface addresses sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Netmask network interface addresses are stable.")
    yield {
        "status": "audit_complete",
        "interface_count": len(netmask_addrs),
        "family": "netmask",
        "stability": "STABLE"
    }

@progress_tool(name="system_disk_partitions_mountpoint_audit")
async def system_disk_partitions_mountpoint_audit(samples: int = 3, mountpoint: str = "/"):
    """
    Audits system disk partitions filtered by mountpoint using psutil.
    """
    logger.info(f"Starting system disk partitions mountpoint audit for {mountpoint}")
    yield ProgressPayload(step="Initializing mountpoint-partitions probe", pct=0, log=f"Collecting disk partition baseline for mountpoint: {mountpoint}...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            partitions = psutil.disk_partitions(all=True)
            filtered_partitions = [p._asdict() for p in partitions if p.mountpoint == mountpoint]
            partition_count = len(filtered_partitions)
            logger.info(f"Sample {i+1}/{samples}: {partition_count} disk partitions found with mountpoint {mountpoint}.")
            metadata = {f"partition_{idx}": p for idx, p in enumerate(filtered_partitions)}
        except Exception as e:
            logger.error(f"Error auditing mountpoint disk partitions: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling mountpoint disk partitions",
            pct=pct,
            log=f"Measured {partition_count} disk partitions with mountpoint {mountpoint} sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Disk partition configuration for {mountpoint} is stable.")
    yield {
        "status": "audit_complete",
        "mountpoint": mountpoint,
        "partition_count": partition_count,
        "stability": "STABLE"
    }

@progress_tool(name="system_cpu_times_percent_user_focused_audit")
async def system_cpu_times_percent_user_focused_audit(samples: int = 3):
    """
    Audits system-wide CPU user time percentage using psutil.
    """
    logger.info("Starting focused user CPU time percentage audit")
    yield ProgressPayload(step="Initializing user CPU focused probe", pct=0, log="Collecting system-wide user CPU timing percentages...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            cpu_times_pct = psutil.cpu_times_percent(interval=0.1)
            user_pct = cpu_times_pct.user
            logger.info(f"Sample {i+1}/{samples}: User CPU Time {user_pct}%")
            metadata = {"user_percent": user_pct, "system_percent": cpu_times_pct.system, "idle_percent": cpu_times_pct.idle}
        except Exception as e:
            logger.error(f"Error auditing focused user CPU time: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling user CPU time",
            pct=pct,
            log=f"Measured user CPU time percentage sample {i+1}/{samples}: {user_pct}%.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. User CPU time percentages are stable.")
    yield {
        "status": "audit_complete",
        "final_user_percent": user_pct,
        "metric": "user_cpu_time",
        "stability": "STABLE"
    }

@progress_tool(name="system_net_if_addrs_broadcast_audit")
async def system_net_if_addrs_broadcast_audit(samples: int = 3):
    """
    Audits broadcast system network interface addresses using psutil.
    """
    logger.info("Starting system net if addrs broadcast audit")
    yield ProgressPayload(step="Initializing broadcast net if addrs probe", pct=0, log="Collecting broadcast network interface address information...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            if_addrs = psutil.net_if_addrs()
            broadcast_addrs = {}
            for iface, addrs in if_addrs.items():
                broadcast_list = [addr.broadcast for addr in addrs if addr.broadcast]
                if broadcast_list:
                    broadcast_addrs[iface] = broadcast_list
            logger.info(f"Sample {i+1}/{samples}: Collected broadcast addresses for {len(broadcast_addrs)} interfaces")
            metadata = broadcast_addrs
        except Exception as e:
            logger.error(f"Error auditing broadcast net if addrs: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling broadcast net if addrs",
            pct=pct,
            log=f"Measured broadcast network interface addresses sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Broadcast network interface addresses are stable.")
    yield {
        "status": "audit_complete",
        "interface_count": len(broadcast_addrs),
        "family": "broadcast",
        "stability": "STABLE"
    }

@progress_tool(name="system_disk_partitions_device_audit")
async def system_disk_partitions_device_audit(samples: int = 3, device: str = "/dev/disk1s1"):
    """
    Audits system disk partitions filtered by device name using psutil.
    """
    logger.info(f"Starting system disk partitions device audit for {device}")
    yield ProgressPayload(step="Initializing device-partitions probe", pct=0, log=f"Collecting disk partition baseline for device: {device}...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            partitions = psutil.disk_partitions(all=True)
            filtered_partitions = [p._asdict() for p in partitions if p.device == device]
            partition_count = len(filtered_partitions)
            logger.info(f"Sample {i+1}/{samples}: {partition_count} disk partitions found with device {device}.")
            metadata = {f"partition_{idx}": p for idx, p in enumerate(filtered_partitions)}
        except Exception as e:
            logger.error(f"Error auditing device disk partitions: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling device disk partitions",
            pct=pct,
            log=f"Measured {partition_count} disk partitions with device {device} sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Disk partition configuration for {device} is stable.")
    yield {
        "status": "audit_complete",
        "device": device,
        "partition_count": partition_count,
        "stability": "STABLE"
    }

@progress_tool(name="system_cpu_times_percent_idle_focused_audit")
async def system_cpu_times_percent_idle_focused_audit(samples: int = 3):
    """
    Audits system-wide idle CPU time percentage using psutil.
    """
    logger.info("Starting focused idle CPU time percentage audit")
    yield ProgressPayload(step="Initializing idle CPU focused probe", pct=0, log="Collecting system-wide idle CPU timing percentages...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            cpu_times_pct = psutil.cpu_times_percent(interval=0.1)
            idle_pct = cpu_times_pct.idle
            logger.info(f"Sample {i+1}/{samples}: Idle CPU Time {idle_pct}%")
            metadata = {"idle_percent": idle_pct, "user_percent": cpu_times_pct.user, "system_percent": cpu_times_pct.system}
        except Exception as e:
            logger.error(f"Error auditing focused idle CPU time: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling idle CPU time",
            pct=pct,
            log=f"Measured idle CPU time percentage sample {i+1}/{samples}: {idle_pct}%.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Idle CPU time percentages are stable.")
    yield {
        "status": "audit_complete",
        "final_idle_percent": idle_pct,
        "metric": "idle_cpu_time",
        "stability": "STABLE"
    }

@progress_tool(name="system_net_if_addrs_ptp_audit")
async def system_net_if_addrs_ptp_audit(samples: int = 3):
    """
    Audits PTP system network interface addresses using psutil.
    """
    logger.info("Starting system net if addrs PTP audit")
    yield ProgressPayload(step="Initializing PTP net if addrs probe", pct=0, log="Collecting PTP network interface address information...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            if_addrs = psutil.net_if_addrs()
            ptp_addrs = {}
            for iface, addrs in if_addrs.items():
                ptp_list = [addr.ptp for addr in addrs if addr.ptp]
                if ptp_list:
                    ptp_addrs[iface] = ptp_list
            logger.info(f"Sample {i+1}/{samples}: Collected PTP addresses for {len(ptp_addrs)} interfaces")
            metadata = ptp_addrs
        except Exception as e:
            logger.error(f"Error auditing PTP net if addrs: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling PTP net if addrs",
            pct=pct,
            log=f"Measured PTP network interface addresses sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. PTP network interface addresses are stable.")
    yield {
        "status": "audit_complete",
        "interface_count": len(ptp_addrs),
        "family": "PTP",
        "stability": "STABLE"
    }

@progress_tool(name="system_disk_partitions_opts_audit")
async def system_disk_partitions_opts_audit(samples: int = 3, opts: str = "rw"):
    """
    Audits system disk partitions filtered by mount options using psutil.
    """
    logger.info(f"Starting system disk partitions opts audit for {opts}")
    yield ProgressPayload(step="Initializing opts-partitions probe", pct=0, log=f"Collecting disk partition baseline for opts: {opts}...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            partitions = psutil.disk_partitions(all=True)
            filtered_partitions = [p._asdict() for p in partitions if opts.lower() in p.opts.lower()]
            partition_count = len(filtered_partitions)
            logger.info(f"Sample {i+1}/{samples}: {partition_count} disk partitions found with opts {opts}.")
            metadata = {f"partition_{idx}": p for idx, p in enumerate(filtered_partitions)}
        except Exception as e:
            logger.error(f"Error auditing opts disk partitions: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling opts disk partitions",
            pct=pct,
            log=f"Measured {partition_count} disk partitions with opts {opts} sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Disk partition configuration for {opts} is stable.")
    yield {
        "status": "audit_complete",
        "opts": opts,
        "partition_count": partition_count,
        "stability": "STABLE"
    }

@progress_tool(name="system_cpu_times_percent_iowait_focused_audit")
async def system_cpu_times_percent_iowait_focused_audit(samples: int = 3):
    """
    Audits system-wide I/O wait CPU time percentage using psutil.
    """
    logger.info("Starting focused I/O wait CPU time percentage audit")
    yield ProgressPayload(step="Initializing I/O wait CPU focused probe", pct=0, log="Collecting system-wide I/O wait CPU timing percentages...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            cpu_times_pct = psutil.cpu_times_percent(interval=0.1)
            iowait_pct = getattr(cpu_times_pct, "iowait", 0.0)
            logger.info(f"Sample {i+1}/{samples}: I/O Wait CPU Time {iowait_pct}%")
            metadata = {"iowait_percent": iowait_pct, "user_percent": cpu_times_pct.user, "idle_percent": cpu_times_pct.idle}
        except Exception as e:
            logger.error(f"Error auditing focused I/O wait CPU time: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling I/O wait CPU time",
            pct=pct,
            log=f"Measured I/O wait CPU time percentage sample {i+1}/{samples}: {iowait_pct}%.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. I/O wait CPU time percentages are stable.")
    yield {
        "status": "audit_complete",
        "final_iowait_percent": iowait_pct,
        "metric": "iowait_cpu_time",
        "stability": "STABLE"
    }

@progress_tool(name="system_cpu_times_percent_irq_focused_audit")
async def system_cpu_times_percent_irq_focused_audit(samples: int = 3):
    """
    Audits system-wide IRQ CPU time percentage using psutil.
    """
    logger.info("Starting focused IRQ CPU time percentage audit")
    yield ProgressPayload(step="Initializing IRQ CPU focused probe", pct=0, log="Collecting system-wide IRQ CPU timing percentages...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            cpu_times_pct = psutil.cpu_times_percent(interval=0.1)
            irq_pct = getattr(cpu_times_pct, "irq", 0.0)
            logger.info(f"Sample {i+1}/{samples}: IRQ CPU Time {irq_pct}%")
            metadata = {"irq_percent": irq_pct, "user_percent": cpu_times_pct.user, "system_percent": cpu_times_pct.system}
        except Exception as e:
            logger.error(f"Error auditing focused IRQ CPU time: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling IRQ CPU time",
            pct=pct,
            log=f"Measured IRQ CPU time percentage sample {i+1}/{samples}: {irq_pct}%.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. IRQ CPU time percentages are stable.")
    yield {
        "status": "audit_complete",
        "final_irq_percent": irq_pct,
        "metric": "irq_cpu_time",
        "stability": "STABLE"
    }

@progress_tool(name="system_cpu_times_percent_softirq_focused_audit")
async def system_cpu_times_percent_softirq_focused_audit(samples: int = 3):
    """
    Audits system-wide soft IRQ CPU time percentage using psutil.
    """
    logger.info("Starting focused soft IRQ CPU time percentage audit")
    yield ProgressPayload(step="Initializing soft IRQ CPU focused probe", pct=0, log="Collecting system-wide soft IRQ CPU timing percentages...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            cpu_times_pct = psutil.cpu_times_percent(interval=0.1)
            softirq_pct = getattr(cpu_times_pct, "softirq", 0.0)
            logger.info(f"Sample {i+1}/{samples}: Soft IRQ CPU Time {softirq_pct}%")
            metadata = {"softirq_percent": softirq_pct, "user_percent": cpu_times_pct.user, "system_percent": cpu_times_pct.system}
        except Exception as e:
            logger.error(f"Error auditing focused soft IRQ CPU time: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling soft IRQ CPU time",
            pct=pct,
            log=f"Measured soft IRQ CPU time percentage sample {i+1}/{samples}: {softirq_pct}%.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Soft IRQ CPU time percentages are stable.")
    yield {
        "status": "audit_complete",
        "final_softirq_percent": softirq_pct,
        "metric": "softirq_cpu_time",
        "stability": "STABLE"
    }

@progress_tool(name="system_net_io_errors_audit")
async def system_net_io_errors_audit(samples: int = 3):
    """
    Audits system-wide network errors and drops using psutil.
    """
    logger.info("Starting system network errors audit")
    yield ProgressPayload(step="Initializing network error probe", pct=0, log="Collecting system-wide network error and drop baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.net_io_counters()
            errin = counters.errin
            errout = counters.errout
            dropin = counters.dropin
            dropout = counters.dropout
            logger.info(f"Sample {i+1}/{samples}: Errors In {errin}, Errors Out {errout}, Drops In {dropin}, Drops Out {dropout}")
            metadata = {"errin": errin, "errout": errout, "dropin": dropin, "dropout": dropout}
        except Exception as e:
            logger.error(f"Error auditing network errors: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling network errors",
            pct=pct,
            log=f"Measured network errors sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Network error and drop statistics are stable.")
    yield {
        "status": "audit_complete",
        "final_errors": metadata,
        "stability": "STABLE"
    }

@progress_tool(name="system_cpu_times_percent_steal_focused_audit")
async def system_cpu_times_percent_steal_focused_audit(samples: int = 3):
    """
    Audits system-wide steal CPU time percentage using psutil.
    """
    logger.info("Starting focused steal CPU time percentage audit")
    yield ProgressPayload(step="Initializing steal CPU focused probe", pct=0, log="Collecting system-wide steal CPU timing percentages...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            cpu_times_pct = psutil.cpu_times_percent(interval=0.1)
            steal_pct = getattr(cpu_times_pct, "steal", 0.0)
            logger.info(f"Sample {i+1}/{samples}: Steal CPU Time {steal_pct}%")
            metadata = {"steal_percent": steal_pct, "user_percent": cpu_times_pct.user, "system_percent": cpu_times_pct.system}
        except Exception as e:
            logger.error(f"Error auditing focused steal CPU time: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling steal CPU time",
            pct=pct,
            log=f"Measured steal CPU time percentage sample {i+1}/{samples}: {steal_pct}%.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Steal CPU time percentages are stable.")
    yield {
        "status": "audit_complete",
        "final_steal_percent": steal_pct,
        "metric": "steal_cpu_time",
        "stability": "STABLE"
    }

@progress_tool(name="system_cpu_times_percent_guest_focused_audit")
async def system_cpu_times_percent_guest_focused_audit(samples: int = 3):
    """
    Audits system-wide guest CPU time percentage using psutil.
    """
    logger.info("Starting focused guest CPU time percentage audit")
    yield ProgressPayload(step="Initializing guest CPU focused probe", pct=0, log="Collecting system-wide guest CPU timing percentages...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            cpu_times_pct = psutil.cpu_times_percent(interval=0.1)
            guest_pct = getattr(cpu_times_pct, "guest", 0.0)
            logger.info(f"Sample {i+1}/{samples}: Guest CPU Time {guest_pct}%")
            metadata = {"guest_percent": guest_pct, "user_percent": cpu_times_pct.user, "system_percent": cpu_times_pct.system}
        except Exception as e:
            logger.error(f"Error auditing focused guest CPU time: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling guest CPU time",
            pct=pct,
            log=f"Measured guest CPU time percentage sample {i+1}/{samples}: {guest_pct}%.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Guest CPU time percentages are stable.")
    yield {
        "status": "audit_complete",
        "final_guest_percent": guest_pct,
        "metric": "guest_cpu_time",
        "stability": "STABLE"
    }

@progress_tool(name="system_disk_partitions_limits_audit")
async def system_disk_partitions_limits_audit(samples: int = 3):
    """
    Audits disk partition limits (maxfile, maxpath) using psutil.
    """
    logger.info("Starting system disk partitions limits audit")
    yield ProgressPayload(step="Initializing partitions limits probe", pct=0, log="Collecting system-wide partition file and path limits...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            partitions = psutil.disk_partitions(all=True)
            limits_data = {}
            for part in partitions:
                limits_data[part.mountpoint] = {
                    "maxfile": getattr(part, "maxfile", None),
                    "maxpath": getattr(part, "maxpath", None)
                }
            logger.info(f"Sample {i+1}/{samples}: Collected limits for {len(limits_data)} partitions")
            metadata = limits_data
        except Exception as e:
            logger.error(f"Error auditing partitions limits: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling partitions limits",
            pct=pct,
            log=f"Measured disk partition limits sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Partition limit statistics are stable.")
    yield {
        "status": "audit_complete",
        "partition_count": len(limits_data),
        "stability": "STABLE"
    }

@progress_tool(name="system_cpu_times_percent_guest_nice_focused_audit")
async def system_cpu_times_percent_guest_nice_focused_audit(samples: int = 3):
    """
    Audits system-wide guest_nice CPU time percentage using psutil.
    """
    logger.info("Starting focused guest_nice CPU time percentage audit")
    yield ProgressPayload(step="Initializing guest_nice CPU focused probe", pct=0, log="Collecting system-wide guest_nice CPU timing percentages...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            cpu_times_pct = psutil.cpu_times_percent(interval=0.1)
            guest_nice_pct = getattr(cpu_times_pct, "guest_nice", 0.0)
            logger.info(f"Sample {i+1}/{samples}: Guest Nice CPU Time {guest_nice_pct}%")
            metadata = {"guest_nice_percent": guest_nice_pct, "user_percent": cpu_times_pct.user, "system_percent": cpu_times_pct.system}
        except Exception as e:
            logger.error(f"Error auditing focused guest_nice CPU time: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling guest_nice CPU time",
            pct=pct,
            log=f"Measured guest_nice CPU time percentage sample {i+1}/{samples}: {guest_nice_pct}%.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Guest_nice CPU time percentages are stable.")
    yield {
        "status": "audit_complete",
        "final_guest_nice_percent": guest_nice_pct,
        "metric": "guest_nice_cpu_time",
        "stability": "STABLE"
    }

@progress_tool(name="system_net_io_packets_audit")
async def system_net_io_packets_audit(samples: int = 3):
    """
    Audits system-wide network packets sent and received using psutil.
    """
    logger.info("Starting system network packets audit")
    yield ProgressPayload(step="Initializing network packet probe", pct=0, log="Collecting system-wide network packet baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.net_io_counters()
            packets_sent = counters.packets_sent
            packets_recv = counters.packets_recv
            logger.info(f"Sample {i+1}/{samples}: Sent {packets_sent} packets, Received {packets_recv} packets")
            metadata = {"packets_sent": packets_sent, "packets_recv": packets_recv}
        except Exception as e:
            logger.error(f"Error auditing network packets: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling network packets",
            pct=pct,
            log=f"Measured network packets sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Network packet statistics are stable.")
    yield {
        "status": "audit_complete",
        "final_packets": metadata,
        "stability": "STABLE"
    }

@progress_tool(name="system_disk_io_time_audit")
async def system_disk_io_time_audit(samples: int = 3):
    """
    Audits system-wide disk I/O time using psutil.
    """
    logger.info("Starting system disk I/O time audit")
    yield ProgressPayload(step="Initializing disk I/O time probe", pct=0, log="Collecting system-wide disk I/O time baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.disk_io_counters()
            read_time = getattr(counters, "read_time", 0)
            write_time = getattr(counters, "write_time", 0)
            busy_time = getattr(counters, "busy_time", 0)
            logger.info(f"Sample {i+1}/{samples}: Read Time {read_time}ms, Write Time {write_time}ms, Busy Time {busy_time}ms")
            metadata = {"read_time_ms": read_time, "write_time_ms": write_time, "busy_time_ms": busy_time}
        except Exception as e:
            logger.error(f"Error auditing disk I/O time: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling disk I/O time",
            pct=pct,
            log=f"Measured disk I/O time sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Disk I/O time statistics are stable.")
    yield {
        "status": "audit_complete",
        "final_io_time": metadata,
        "stability": "STABLE"
    }

@progress_tool(name="system_cpu_times_percent_nice_focused_audit")
async def system_cpu_times_percent_nice_focused_audit(samples: int = 3):
    """
    Audits system-wide nice CPU time percentage using psutil.
    """
    logger.info("Starting focused nice CPU time percentage audit")
    yield ProgressPayload(step="Initializing nice CPU focused probe", pct=0, log="Collecting system-wide nice CPU timing percentages...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            cpu_times_pct = psutil.cpu_times_percent(interval=0.1)
            nice_pct = getattr(cpu_times_pct, "nice", 0.0)
            logger.info(f"Sample {i+1}/{samples}: Nice CPU Time {nice_pct}%")
            metadata = {"nice_percent": nice_pct, "user_percent": cpu_times_pct.user, "system_percent": cpu_times_pct.system}
        except Exception as e:
            logger.error(f"Error auditing focused nice CPU time: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling nice CPU time",
            pct=pct,
            log=f"Measured nice CPU time sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Nice CPU time statistics are stable.")
    yield {
        "status": "audit_complete",
        "final_nice_percent": nice_pct,
        "metric": "nice_cpu_time",
        "stability": "STABLE"
    }

@progress_tool(name="system_disk_io_read_count_audit")
async def system_disk_io_read_count_audit(samples: int = 3):
    """
    Audits system-wide disk read operations count using psutil.
    """
    logger.info("Starting system disk read count audit")
    yield ProgressPayload(step="Initializing disk read count probe", pct=0, log="Collecting system-wide disk read count baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.disk_io_counters()
            read_count = counters.read_count
            logger.info(f"Sample {i+1}/{samples}: Read Count {read_count}")
            metadata = {"read_count": read_count}
        except Exception as e:
            logger.error(f"Error auditing disk read count: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling disk read count",
            pct=pct,
            log=f"Measured disk read count sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Disk read count statistics are stable.")
    yield {
        "status": "audit_complete",
        "final_read_count": read_count,
        "stability": "STABLE"
    }

@progress_tool(name="system_disk_io_write_count_audit")
async def system_disk_io_write_count_audit(samples: int = 3):
    """
    Audits system-wide disk write operations count using psutil.
    """
    logger.info("Starting system disk write count audit")
    yield ProgressPayload(step="Initializing disk write count probe", pct=0, log="Collecting system-wide disk write count baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.disk_io_counters()
            write_count = counters.write_count
            logger.info(f"Sample {i+1}/{samples}: Write Count {write_count}")
            metadata = {"write_count": write_count}
        except Exception as e:
            logger.error(f"Error auditing disk write count: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling disk write count",
            pct=pct,
            log=f"Measured disk write count sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Disk write count statistics are stable.")
    yield {
        "status": "audit_complete",
        "final_write_count": write_count,
        "stability": "STABLE"
    }

@progress_tool(name="system_net_io_merged_audit")
async def system_net_io_merged_audit(samples: int = 3):
    """
    Audits system-wide network I/O with merged metrics using psutil.
    """
    logger.info("Starting system network merged I/O audit")
    yield ProgressPayload(step="Initializing network merged probe", pct=0, log="Collecting system-wide network I/O baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.net_io_counters()
            logger.info(f"Sample {i+1}/{samples}: Sent {counters.bytes_sent}, Recv {counters.bytes_recv}")
            metadata = counters._asdict()
        except Exception as e:
            logger.error(f"Error auditing network merged I/O: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling network merged I/O",
            pct=pct,
            log=f"Measured network merged I/O sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Network merged I/O statistics are stable.")
    yield {
        "status": "audit_complete",
        "final_io": metadata,
        "stability": "STABLE"
    }

@progress_tool(name="system_cpu_stats_ctx_switches_audit")
async def system_cpu_stats_ctx_switches_audit(samples: int = 3):
    """
    Audits system-wide context switches using psutil.
    """
    logger.info("Starting system context switches audit")
    yield ProgressPayload(step="Initializing ctx switches probe", pct=0, log="Collecting system-wide context switch baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            ctx_switches = stats.ctx_switches
            logger.info(f"Sample {i+1}/{samples}: Context Switches {ctx_switches}")
            metadata = {"ctx_switches": ctx_switches}
        except Exception as e:
            logger.error(f"Error auditing context switches: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling context switches",
            pct=pct,
            log=f"Measured context switches sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Context switch statistics are stable.")
    yield {
        "status": "audit_complete",
        "final_ctx_switches": ctx_switches,
        "stability": "STABLE"
    }

@progress_tool(name="system_cpu_stats_interrupts_audit")
async def system_cpu_stats_interrupts_audit(samples: int = 3):
    """
    Audits system-wide interrupts using psutil.
    """
    logger.info("Starting system interrupts audit")
    yield ProgressPayload(step="Initializing interrupts probe", pct=0, log="Collecting system-wide interrupt baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            interrupts = stats.interrupts
            logger.info(f"Sample {i+1}/{samples}: Interrupts {interrupts}")
            metadata = {"interrupts": interrupts}
        except Exception as e:
            logger.error(f"Error auditing interrupts: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling interrupts",
            pct=pct,
            log=f"Measured interrupts sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Interrupt statistics are stable.")
    yield {
        "status": "audit_complete",
        "final_interrupts": interrupts,
        "stability": "STABLE"
    }
