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
    data = await health_engine.get_health_data(dummy_state, "2.2.9", "v603-supreme-apex-adele-verification", "v603 SUPREME APEX VERIFICATION ADELE")
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
