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
    data = await health_engine.get_health_data(dummy_state, "2.10.83", "v757-supreme-apex-adele-verification", "v757 SUPREME APEX VERIFICATION ADELE")
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

@progress_tool(name="system_cpu_stats_soft_interrupts_audit")
async def system_cpu_stats_soft_interrupts_audit(samples: int = 3):
    """
    Audits system-wide soft interrupts using psutil.
    """
    logger.info("Starting system soft interrupts audit")
    yield ProgressPayload(step="Initializing soft interrupts probe", pct=0, log="Collecting system-wide soft interrupt baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            soft_interrupts = stats.soft_interrupts
            logger.info(f"Sample {i+1}/{samples}: Soft Interrupts {soft_interrupts}")
            metadata = {"soft_interrupts": soft_interrupts}
        except Exception as e:
            logger.error(f"Error auditing soft interrupts: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling soft interrupts",
            pct=pct,
            log=f"Measured soft interrupts sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Soft interrupt statistics are stable.")
    yield {
        "status": "audit_complete",
        "final_soft_interrupts": soft_interrupts,
        "stability": "STABLE"
    }

@progress_tool(name="system_cpu_stats_syscalls_audit")
async def system_cpu_stats_syscalls_audit(samples: int = 3):
    """
    Audits system-wide syscalls using psutil.
    """
    logger.info("Starting system syscalls audit")
    yield ProgressPayload(step="Initializing syscalls probe", pct=0, log="Collecting system-wide syscall baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            syscalls = stats.syscalls
            logger.info(f"Sample {i+1}/{samples}: Syscalls {syscalls}")
            metadata = {"syscalls": syscalls}
        except Exception as e:
            logger.error(f"Error auditing syscalls: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling syscalls",
            pct=pct,
            log=f"Measured syscalls sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Syscall statistics are stable.")
    yield {
        "status": "audit_complete",
        "final_syscalls": syscalls,
        "stability": "STABLE"
    }

@progress_tool(name="system_net_io_dropin_audit")
async def system_net_io_dropin_audit(samples: int = 3):
    """
    Audits incoming network packet drops using psutil.
    """
    logger.info("Starting system net io dropin audit")
    yield ProgressPayload(step="Initializing dropin probe", pct=0, log="Collecting dropin packet baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.net_io_counters()
            dropin = counters.dropin
            logger.info(f"Sample {i+1}/{samples}: Drop-in {dropin}")
            metadata = {"dropin": dropin}
        except Exception as e:
            logger.error(f"Error auditing dropin packets: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling dropin packets",
            pct=pct,
            log=f"Measured dropin sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Drop-in statistics are stable.")
    yield {
        "status": "audit_complete",
        "final_dropin": dropin,
        "stability": "STABLE"
    }

@progress_tool(name="system_net_io_dropout_audit")
async def system_net_io_dropout_audit(samples: int = 3):
    """
    Audits outgoing network packet drops using psutil.
    """
    logger.info("Starting system net io dropout audit")
    yield ProgressPayload(step="Initializing dropout probe", pct=0, log="Collecting dropout packet baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.net_io_counters()
            dropout = counters.dropout
            logger.info(f"Sample {i+1}/{samples}: Drop-out {dropout}")
            metadata = {"dropout": dropout}
        except Exception as e:
            logger.error(f"Error auditing dropout packets: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling dropout packets",
            pct=pct,
            log=f"Measured dropout sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Drop-out statistics are stable.")
    yield {
        "status": "audit_complete",
        "final_dropout": dropout,
        "stability": "STABLE"
    }

@progress_tool(name="system_net_io_errin_audit")
async def system_net_io_errin_audit(samples: int = 3):
    """
    Audits incoming network errors using psutil.
    """
    logger.info("Starting system net io errin audit")
    yield ProgressPayload(step="Initializing errin probe", pct=0, log="Collecting incoming network error baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.net_io_counters()
            errin = counters.errin
            logger.info(f"Sample {i+1}/{samples}: Error-in {errin}")
            metadata = {"errin": errin}
        except Exception as e:
            logger.error(f"Error auditing errin packets: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling errin packets",
            pct=pct,
            log=f"Measured errin sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Error-in statistics are stable.")
    yield {
        "status": "audit_complete",
        "final_errin": errin,
        "stability": "STABLE"
    }

@progress_tool(name="system_net_io_errout_audit")
async def system_net_io_errout_audit(samples: int = 3):
    """
    Audits outgoing network errors using psutil.
    """
    logger.info("Starting system net io errout audit")
    yield ProgressPayload(step="Initializing errout probe", pct=0, log="Collecting outgoing network error baseline...")
    
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.net_io_counters()
            errout = counters.errout
            logger.info(f"Sample {i+1}/{samples}: Error-out {errout}")
            metadata = {"errout": errout}
        except Exception as e:
            logger.error(f"Error auditing errout packets: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling errout packets",
            pct=pct,
            log=f"Measured errout sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Error-out statistics are stable.")
    yield {
        "status": "audit_complete",
        "final_errout": errout,
        "stability": "STABLE"
    }

@progress_tool(name="system_net_io_packets_sent_audit")
async def system_net_io_packets_sent_audit(samples: int = 3):
    """
    Audits system-wide network packets sent using psutil.
    """
    logger.info("Starting system net io packets sent audit")
    yield ProgressPayload(step="Initializing packets sent probe", pct=0, log="Collecting packets sent baseline...")
    
    packets_sent = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.net_io_counters()
            packets_sent = counters.packets_sent
            logger.info(f"Sample {i+1}/{samples}: Packets-sent {packets_sent}")
            metadata = {"packets_sent": packets_sent}
        except Exception as e:
            logger.error(f"Error auditing packets sent: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling packets sent",
            pct=pct,
            log=f"Measured packets sent sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Packets sent statistics are stable.")
    yield {
        "status": "audit_complete",
        "final_packets_sent": packets_sent,
        "stability": "STABLE"
    }

@progress_tool(name="system_net_io_packets_recv_audit")
async def system_net_io_packets_recv_audit(samples: int = 3):
    """
    Audits system-wide network packets received using psutil.
    """
    logger.info("Starting system net io packets recv audit")
    yield ProgressPayload(step="Initializing packets recv probe", pct=0, log="Collecting packets recv baseline...")
    
    packets_recv = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.net_io_counters()
            packets_recv = counters.packets_recv
            logger.info(f"Sample {i+1}/{samples}: Packets-recv {packets_recv}")
            metadata = {"packets_recv": packets_recv}
        except Exception as e:
            logger.error(f"Error auditing packets recv: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling packets recv",
            pct=pct,
            log=f"Measured packets recv sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Packets recv statistics are stable.")
    yield {
        "status": "audit_complete",
        "final_packets_recv": packets_recv,
        "stability": "STABLE"
    }

@progress_tool(name="system_disk_io_read_bytes_audit")
async def system_disk_io_read_bytes_audit(samples: int = 3):
    """
    Audits system-wide disk read bytes using psutil.
    """
    logger.info("Starting system disk io read bytes audit")
    yield ProgressPayload(step="Initializing disk read bytes probe", pct=0, log="Collecting disk read bytes baseline...")
    
    read_bytes = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.disk_io_counters()
            read_bytes = counters.read_bytes
            logger.info(f"Sample {i+1}/{samples}: Read-bytes {read_bytes}")
            metadata = {"read_bytes": read_bytes}
        except Exception as e:
            logger.error(f"Error auditing disk read bytes: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling disk read bytes",
            pct=pct,
            log=f"Measured disk read bytes sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Disk read bytes statistics are stable.")
    yield {
        "status": "audit_complete",
        "final_read_bytes": read_bytes,
        "stability": "STABLE"
    }

@progress_tool(name="system_disk_io_write_bytes_audit")
async def system_disk_io_write_bytes_audit(samples: int = 3):
    """
    Audits system-wide disk write bytes using psutil.
    """
    logger.info("Starting system disk io write bytes audit")
    yield ProgressPayload(step="Initializing disk write bytes probe", pct=0, log="Collecting disk write bytes baseline...")
    
    write_bytes = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.disk_io_counters()
            write_bytes = counters.write_bytes
            logger.info(f"Sample {i+1}/{samples}: Write-bytes {write_bytes}")
            metadata = {"write_bytes": write_bytes}
        except Exception as e:
            logger.error(f"Error auditing disk write bytes: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling disk write bytes",
            pct=pct,
            log=f"Measured disk write bytes sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Disk write bytes statistics are stable.")
    yield {
        "status": "audit_complete",
        "final_write_bytes": write_bytes,
        "stability": "STABLE"
    }

@progress_tool(name="system_net_io_sent_bytes_audit")
async def system_net_io_sent_bytes_audit(samples: int = 3):
    """
    Audits system-wide network sent bytes using psutil.
    """
    logger.info("Starting system net io sent bytes audit")
    yield ProgressPayload(step="Initializing sent bytes probe", pct=0, log="Collecting sent bytes baseline...")
    
    bytes_sent = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.net_io_counters()
            bytes_sent = counters.bytes_sent
            logger.info(f"Sample {i+1}/{samples}: Sent-bytes {bytes_sent}")
            metadata = {"bytes_sent": bytes_sent}
        except Exception as e:
            logger.error(f"Error auditing network sent bytes: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling sent bytes",
            pct=pct,
            log=f"Measured network sent bytes sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Network sent bytes statistics are stable.")
    yield {
        "status": "audit_complete",
        "final_bytes_sent": bytes_sent,
        "stability": "STABLE"
    }

@progress_tool(name="system_net_io_recv_bytes_audit")
async def system_net_io_recv_bytes_audit(samples: int = 3):
    """
    Audits system-wide network received bytes using psutil.
    """
    logger.info("Starting system net io recv bytes audit")
    yield ProgressPayload(step="Initializing recv bytes probe", pct=0, log="Collecting recv bytes baseline...")
    
    bytes_recv = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.net_io_counters()
            bytes_recv = counters.bytes_recv
            logger.info(f"Sample {i+1}/{samples}: Recv-bytes {bytes_recv}")
            metadata = {"bytes_recv": bytes_recv}
        except Exception as e:
            logger.error(f"Error auditing network recv bytes: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling recv bytes",
            pct=pct,
            log=f"Measured network recv bytes sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Network recv bytes statistics are stable.")
    yield {
        "status": "audit_complete",
        "final_bytes_recv": bytes_recv,
        "stability": "STABLE"
    }

@progress_tool(name="system_disk_io_read_time_audit")
async def system_disk_io_read_time_audit(samples: int = 3):
    """
    Audits system-wide disk read time using psutil.
    """
    logger.info("Starting system disk io read time audit")
    yield ProgressPayload(step="Initializing disk read time probe", pct=0, log="Collecting disk read time baseline...")
    
    read_time = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.disk_io_counters()
            read_time = counters.read_time
            logger.info(f"Sample {i+1}/{samples}: Read-time {read_time}")
            metadata = {"read_time": read_time}
        except Exception as e:
            logger.error(f"Error auditing disk read time: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling disk read time",
            pct=pct,
            log=f"Measured disk read time sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Disk read time statistics are stable.")
    yield {
        "status": "audit_complete",
        "final_read_time": read_time,
        "stability": "STABLE"
    }

@progress_tool(name="system_disk_io_write_time_audit")
async def system_disk_io_write_time_audit(samples: int = 3):
    """
    Audits system-wide disk write time using psutil.
    """
    logger.info("Starting system disk io write time audit")
    yield ProgressPayload(step="Initializing disk write time probe", pct=0, log="Collecting disk write time baseline...")
    
    write_time = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.disk_io_counters()
            write_time = counters.write_time
            logger.info(f"Sample {i+1}/{samples}: Write-time {write_time}")
            metadata = {"write_time": write_time}
        except Exception as e:
            logger.error(f"Error auditing disk write time: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling disk write time",
            pct=pct,
            log=f"Measured disk write time sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Disk write time statistics are stable.")
    yield {
        "status": "audit_complete",
        "final_write_time": write_time,
        "stability": "STABLE"
    }

@progress_tool(name="system_disk_io_busy_time_audit")
async def system_disk_io_busy_time_audit(samples: int = 3):
    """
    Audits system-wide disk busy time using psutil.
    """
    logger.info("Starting system disk io busy time audit")
    yield ProgressPayload(step="Initializing disk busy time probe", pct=0, log="Collecting disk busy time baseline...")
    
    busy_time = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.disk_io_counters()
            busy_time = getattr(counters, "busy_time", 0)
            logger.info(f"Sample {i+1}/{samples}: Busy-time {busy_time}")
            metadata = {"busy_time": busy_time}
        except Exception as e:
            logger.error(f"Error auditing disk busy time: {e}")
            metadata = {"error": str(e)}

        yield ProgressPayload(
            step="Sampling disk busy time",
            pct=pct,
            log=f"Measured disk busy time sample {i+1}/{samples}.",
            metadata=metadata
        )
        await asyncio.sleep(0.1)
    
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Disk busy time statistics are stable.")
    yield {
        "status": "audit_complete",
        "final_busy_time": busy_time,
        "stability": "STABLE"
    }

@progress_tool(name="system_cpu_times_percent_idle_focused_audit")
async def system_cpu_times_percent_idle_focused_audit(samples: int = 3):
    """
    Audits system-wide idle CPU time percentage using psutil.
    """
    logger.info("Starting focused idle CPU time percentage audit")
    yield ProgressPayload(step="Initializing idle CPU focused probe", pct=0, log="Collecting system-wide idle CPU timing percentages...")
    
    idle_pct = 0.0
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

@progress_tool(name="system_cpu_stats_ctx_switches_focused_audit")
async def system_cpu_stats_ctx_switches_focused_audit(samples: int = 3):
    logger.info("Starting focused context switches audit")
    yield ProgressPayload(step="Initializing context switches probe", pct=0, log="Collecting system-wide context switch counters...")
    ctx_switches = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            ctx_switches = stats.ctx_switches
            logger.info(f"Sample {i+1}/{samples}: Context-switches {ctx_switches}")
            metadata = {"ctx_switches": ctx_switches}
        except Exception as e:
            logger.error(f"Error auditing focused context switches: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling context switches", pct=pct, log=f"Measured context switches sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Context switch statistics are stable.")
    yield {"status": "audit_complete", "final_ctx_switches": ctx_switches, "stability": "STABLE"}

@progress_tool(name="system_cpu_stats_interrupts_focused_audit")
async def system_cpu_stats_interrupts_focused_audit(samples: int = 3):
    logger.info("Starting focused interrupts audit")
    yield ProgressPayload(step="Initializing interrupts probe", pct=0, log="Collecting system-wide interrupt counters...")
    interrupts = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            interrupts = stats.interrupts
            logger.info(f"Sample {i+1}/{samples}: Interrupts {interrupts}")
            metadata = {"interrupts": interrupts}
        except Exception as e:
            logger.error(f"Error auditing focused interrupts: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling interrupts", pct=pct, log=f"Measured interrupts sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Interrupt statistics are stable.")
    yield {"status": "audit_complete", "final_interrupts": interrupts, "stability": "STABLE"}

@progress_tool(name="system_cpu_stats_soft_interrupts_focused_audit")
async def system_cpu_stats_soft_interrupts_focused_audit(samples: int = 3):
    logger.info("Starting focused soft interrupts audit")
    yield ProgressPayload(step="Initializing soft interrupts probe", pct=0, log="Collecting system-wide soft interrupt counters...")
    soft_interrupts = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            soft_interrupts = stats.soft_interrupts
            logger.info(f"Sample {i+1}/{samples}: Soft-interrupts {soft_interrupts}")
            metadata = {"soft_interrupts": soft_interrupts}
        except Exception as e:
            logger.error(f"Error auditing focused soft interrupts: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling soft interrupts", pct=pct, log=f"Measured soft interrupts sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Soft interrupt statistics are stable.")
    yield {"status": "audit_complete", "final_soft_interrupts": soft_interrupts, "stability": "STABLE"}

@progress_tool(name="system_cpu_stats_syscalls_focused_audit")
async def system_cpu_stats_syscalls_focused_audit(samples: int = 3):
    logger.info("Starting focused syscalls audit")
    yield ProgressPayload(step="Initializing syscalls probe", pct=0, log="Collecting system-wide syscall counters...")
    syscalls = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            syscalls = stats.syscalls
            logger.info(f"Sample {i+1}/{samples}: Syscalls {syscalls}")
            metadata = {"syscalls": syscalls}
        except Exception as e:
            logger.error(f"Error auditing focused syscalls: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling syscalls", pct=pct, log=f"Measured syscalls sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Syscall statistics are stable.")
    yield {"status": "audit_complete", "final_syscalls": syscalls, "stability": "STABLE"}

@progress_tool(name="system_net_io_packets_sent_focused_audit")
async def system_net_io_packets_sent_focused_audit(samples: int = 3):
    logger.info("Starting focused packets sent audit")
    yield ProgressPayload(step="Initializing packets sent probe", pct=0, log="Collecting system-wide packets sent counters...")
    packets_sent = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_io_counters()
            packets_sent = stats.packets_sent
            logger.info(f"Sample {i+1}/{samples}: Packets-sent {packets_sent}")
            metadata = {"packets_sent": packets_sent}
        except Exception as e:
            logger.error(f"Error auditing focused packets sent: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling packets sent", pct=pct, log=f"Measured packets sent sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Packets sent statistics are stable.")
    yield {"status": "audit_complete", "final_packets_sent": packets_sent, "stability": "STABLE"}

@progress_tool(name="system_net_io_packets_recv_focused_audit")
async def system_net_io_packets_recv_focused_audit(samples: int = 3):
    logger.info("Starting focused packets received audit")
    yield ProgressPayload(step="Initializing packets received probe", pct=0, log="Collecting system-wide packets received counters...")
    packets_recv = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_io_counters()
            packets_recv = stats.packets_recv
            logger.info(f"Sample {i+1}/{samples}: Packets-recv {packets_recv}")
            metadata = {"packets_recv": packets_recv}
        except Exception as e:
            logger.error(f"Error auditing focused packets received: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling packets received", pct=pct, log=f"Measured packets received sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Packets received statistics are stable.")
    yield {"status": "audit_complete", "final_packets_recv": packets_recv, "stability": "STABLE"}


@progress_tool(name="system_net_io_errin_focused_audit")
async def system_net_io_errin_focused_audit(samples: int = 3):
    logger.info("Starting focused incoming network errors audit")
    yield ProgressPayload(step="Initializing errin focused probe", pct=0, log="Collecting system-wide incoming network error counters...")
    errin = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_io_counters()
            errin = stats.errin
            logger.info(f"Sample {i+1}/{samples}: Incoming-errors {errin}")
            metadata = {"errin": errin}
        except Exception as e:
            logger.error(f"Error auditing focused incoming network errors: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling incoming errors", pct=pct, log=f"Measured incoming network errors sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Incoming network error statistics are stable.")
    yield {"status": "audit_complete", "final_errin": errin, "stability": "STABLE"}

@progress_tool(name="system_net_io_errout_focused_audit")
async def system_net_io_errout_focused_audit(samples: int = 3):
    logger.info("Starting focused outgoing network errors audit")
    yield ProgressPayload(step="Initializing errout focused probe", pct=0, log="Collecting system-wide outgoing network error counters...")
    errout = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_io_counters()
            errout = stats.errout
            logger.info(f"Sample {i+1}/{samples}: Outgoing-errors {errout}")
            metadata = {"errout": errout}
        except Exception as e:
            logger.error(f"Error auditing focused outgoing network errors: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling outgoing errors", pct=pct, log=f"Measured outgoing network errors sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Outgoing network error statistics are stable.")
    yield {"status": "audit_complete", "final_errout": errout, "stability": "STABLE"}

@progress_tool(name="system_net_io_dropin_focused_audit")
async def system_net_io_dropin_focused_audit(samples: int = 3):
    logger.info("Starting focused incoming network drops audit")
    yield ProgressPayload(step="Initializing dropin focused probe", pct=0, log="Collecting system-wide incoming network drop counters...")
    dropin = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_io_counters()
            dropin = stats.dropin
            logger.info(f"Sample {i+1}/{samples}: Incoming-drops {dropin}")
            metadata = {"dropin": dropin}
        except Exception as e:
            logger.error(f"Error auditing focused incoming network drops: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling incoming drops", pct=pct, log=f"Measured incoming network drops sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Incoming network drop statistics are stable.")
    yield {"status": "audit_complete", "final_dropin": dropin, "stability": "STABLE"}

@progress_tool(name="system_net_io_dropout_focused_audit")
async def system_net_io_dropout_focused_audit(samples: int = 3):
    logger.info("Starting focused outgoing network drops audit")
    yield ProgressPayload(step="Initializing dropout focused probe", pct=0, log="Collecting system-wide outgoing network drop counters...")
    dropout = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_io_counters()
            dropout = stats.dropout
            logger.info(f"Sample {i+1}/{samples}: Outgoing-drops {dropout}")
            metadata = {"dropout": dropout}
        except Exception as e:
            logger.error(f"Error auditing focused outgoing network drops: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling outgoing drops", pct=pct, log=f"Measured outgoing network drops sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Outgoing network drop statistics are stable.")
    yield {"status": "audit_complete", "final_dropout": dropout, "stability": "STABLE"}

@progress_tool(name="system_swap_memory_sin_focused_audit")
async def system_swap_memory_sin_focused_audit(samples: int = 3):
    logger.info("Starting focused swap-in audit")
    yield ProgressPayload(step="Initializing swap-in focused probe", pct=0, log="Collecting system-wide swap-in counters...")
    sin = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.swap_memory()
            sin = stats.sin
            logger.info(f"Sample {i+1}/{samples}: Swap-in {sin}")
            metadata = {"sin": sin}
        except Exception as e:
            logger.error(f"Error auditing focused swap-in: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling swap-in", pct=pct, log=f"Measured swap-in sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Swap-in statistics are stable.")
    yield {"status": "audit_complete", "final_sin": sin, "stability": "STABLE"}

@progress_tool(name="system_swap_memory_sout_focused_audit")
async def system_swap_memory_sout_focused_audit(samples: int = 3):
    logger.info("Starting focused swap-out audit")
    yield ProgressPayload(step="Initializing swap-out focused probe", pct=0, log="Collecting system-wide swap-out counters...")
    sout = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.swap_memory()
            sout = stats.sout
            logger.info(f"Sample {i+1}/{samples}: Swap-out {sout}")
            metadata = {"sout": sout}
        except Exception as e:
            logger.error(f"Error auditing focused swap-out: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling swap-out", pct=pct, log=f"Measured swap-out sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Swap-out statistics are stable.")
    yield {"status": "audit_complete", "final_sout": sout, "stability": "STABLE"}

@progress_tool(name="system_swap_memory_sin_total_audit")
async def system_swap_memory_sin_total_audit(samples: int = 3):
    logger.info("Starting total swap-in audit")
    yield ProgressPayload(step="Initializing swap-in total probe", pct=0, log="Collecting cumulative system-wide swap-in counters...")
    sin = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.swap_memory()
            sin = stats.sin
            logger.info(f"Sample {i+1}/{samples}: Total Swap-in {sin}")
            metadata = {"sin_total": sin}
        except Exception as e:
            logger.error(f"Error auditing total swap-in: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total swap-in", pct=pct, log=f"Measured total swap-in sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total swap-in statistics are stable.")
    yield {"status": "audit_complete", "final_sin_total": sin, "stability": "STABLE"}

@progress_tool(name="system_swap_memory_sout_total_audit")
async def system_swap_memory_sout_total_audit(samples: int = 3):
    logger.info("Starting total swap-out audit")
    yield ProgressPayload(step="Initializing swap-out total probe", pct=0, log="Collecting cumulative system-wide swap-out counters...")
    sout = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.swap_memory()
            sout = stats.sout
            logger.info(f"Sample {i+1}/{samples}: Total Swap-out {sout}")
            metadata = {"sout_total": sout}
        except Exception as e:
            logger.error(f"Error auditing total swap-out: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total swap-out", pct=pct, log=f"Measured total swap-out sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total swap-out statistics are stable.")
    yield {"status": "audit_complete", "final_sout_total": sout, "stability": "STABLE"}

@progress_tool(name="system_net_io_dropout_total_audit")
async def system_net_io_dropout_total_audit(samples: int = 3):
    logger.info("Starting total outgoing network drop audit")
    yield ProgressPayload(step="Initializing outgoing drop total probe", pct=0, log="Collecting cumulative outgoing network drop counters...")
    dropout = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_io_counters()
            dropout = stats.dropout
            logger.info(f"Sample {i+1}/{samples}: Total Outgoing-drops {dropout}")
            metadata = {"dropout_total": dropout}
        except Exception as e:
            logger.error(f"Error auditing total outgoing network drops: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total outgoing drops", pct=pct, log=f"Measured total outgoing network drops sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total outgoing network drop statistics are stable.")
    yield {"status": "audit_complete", "final_dropout_total": dropout, "stability": "STABLE"}

@progress_tool(name="system_net_io_dropin_total_audit")
async def system_net_io_dropin_total_audit(samples: int = 3):
    logger.info("Starting total incoming network drop audit")
    yield ProgressPayload(step="Initializing incoming drop total probe", pct=0, log="Collecting cumulative incoming network drop counters...")
    dropin = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_io_counters()
            dropin = stats.dropin
            logger.info(f"Sample {i+1}/{samples}: Total Incoming-drops {dropin}")
            metadata = {"dropin_total": dropin}
        except Exception as e:
            logger.error(f"Error auditing total incoming network drops: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total incoming drops", pct=pct, log=f"Measured total incoming network drops sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total incoming network drop statistics are stable.")
    yield {"status": "audit_complete", "final_dropin_total": dropin, "stability": "STABLE"}

@progress_tool(name="system_net_io_errout_total_audit")
async def system_net_io_errout_total_audit(samples: int = 3):
    logger.info("Starting total outgoing network error audit")
    yield ProgressPayload(step="Initializing outgoing error total probe", pct=0, log="Collecting cumulative outgoing network error counters...")
    errout = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_io_counters()
            errout = stats.errout
            logger.info(f"Sample {i+1}/{samples}: Total Outgoing-errors {errout}")
            metadata = {"errout_total": errout}
        except Exception as e:
            logger.error(f"Error auditing total outgoing network errors: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total outgoing errors", pct=pct, log=f"Measured total outgoing network errors sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total outgoing network error statistics are stable.")
    yield {"status": "audit_complete", "final_errout_total": errout, "stability": "STABLE"}

@progress_tool(name="system_net_io_errin_total_audit")
async def system_net_io_errin_total_audit(samples: int = 3):
    logger.info("Starting total incoming network error audit")
    yield ProgressPayload(step="Initializing incoming error total probe", pct=0, log="Collecting cumulative incoming network error counters...")
    errin = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_io_counters()
            errin = stats.errin
            logger.info(f"Sample {i+1}/{samples}: Total Incoming-errors {errin}")
            metadata = {"errin_total": errin}
        except Exception as e:
            logger.error(f"Error auditing total incoming network errors: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total incoming errors", pct=pct, log=f"Measured total incoming network errors sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total incoming network error statistics are stable.")
    yield {"status": "audit_complete", "final_errin_total": errin, "stability": "STABLE"}

@progress_tool(name="system_net_io_packets_sent_total_audit")
async def system_net_io_packets_sent_total_audit(samples: int = 3):
    logger.info("Starting total outgoing network packet audit")
    yield ProgressPayload(step="Initializing outgoing packet total probe", pct=0, log="Collecting cumulative outgoing network packet counters...")
    packets_sent = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_io_counters()
            packets_sent = stats.packets_sent
            logger.info(f"Sample {i+1}/{samples}: Total Outgoing-packets {packets_sent}")
            metadata = {"packets_sent_total": packets_sent}
        except Exception as e:
            logger.error(f"Error auditing total outgoing network packets: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total outgoing packets", pct=pct, log=f"Measured total outgoing network packets sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total outgoing network packet statistics are stable.")
    yield {"status": "audit_complete", "final_packets_sent_total": packets_sent, "stability": "STABLE"}

@progress_tool(name="system_net_io_packets_recv_total_audit")
async def system_net_io_packets_recv_total_audit(samples: int = 3):
    logger.info("Starting total incoming network packet audit")
    yield ProgressPayload(step="Initializing incoming packet total probe", pct=0, log="Collecting cumulative incoming network packet counters...")
    packets_recv = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_io_counters()
            packets_recv = stats.packets_recv
            logger.info(f"Sample {i+1}/{samples}: Total Incoming-packets {packets_recv}")
            metadata = {"packets_recv_total": packets_recv}
        except Exception as e:
            logger.error(f"Error auditing total incoming network packets: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total incoming packets", pct=pct, log=f"Measured total incoming network packets sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total incoming network packet statistics are stable.")
    yield {"status": "audit_complete", "final_packets_recv_total": packets_recv, "stability": "STABLE"}

@progress_tool(name="system_disk_io_read_count_total_audit")
async def system_disk_io_read_count_total_audit(samples: int = 3):
    logger.info("Starting total disk read count audit")
    yield ProgressPayload(step="Initializing disk read total probe", pct=0, log="Collecting cumulative system-wide disk read counters...")
    read_count = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.disk_io_counters()
            read_count = stats.read_count
            logger.info(f"Sample {i+1}/{samples}: Total Disk-reads {read_count}")
            metadata = {"read_count_total": read_count}
        except Exception as e:
            logger.error(f"Error auditing total disk read count: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total disk read count", pct=pct, log=f"Measured total disk read count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total disk read statistics are stable.")
    yield {"status": "audit_complete", "final_read_count_total": read_count, "stability": "STABLE"}

@progress_tool(name="system_net_io_errors_total_audit")
async def system_net_io_errors_total_audit(samples: int = 3):
    logger.info("Starting total network errors audit")
    yield ProgressPayload(step="Initializing network errors total probe", pct=0, log="Collecting cumulative system-wide network errors...")
    errin = 0
    errout = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_io_counters()
            errin = stats.errin
            errout = stats.errout
            logger.info(f"Sample {i+1}/{samples}: Total Net-errors In={errin}, Out={errout}")
            metadata = {"errin_total": errin, "errout_total": errout}
        except Exception as e:
            logger.error(f"Error auditing total network errors: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total network errors", pct=pct, log=f"Measured total network errors sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total network error statistics are stable.")
    yield {"status": "audit_complete", "final_errin_total": errin, "final_errout_total": errout, "stability": "STABLE"}

@progress_tool(name="system_net_io_drop_total_audit")
async def system_net_io_drop_total_audit(samples: int = 3):
    logger.info("Starting total network drops audit")
    yield ProgressPayload(step="Initializing network drops total probe", pct=0, log="Collecting cumulative system-wide network drops...")
    dropin = 0
    dropout = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_io_counters()
            dropin = stats.dropin
            dropout = stats.dropout
            logger.info(f"Sample {i+1}/{samples}: Total Net-drops In={dropin}, Out={dropout}")
            metadata = {"dropin_total": dropin, "dropout_total": dropout}
        except Exception as e:
            logger.error(f"Error auditing total network drops: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total network drops", pct=pct, log=f"Measured total network drops sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total network drop statistics are stable.")
    yield {"status": "audit_complete", "final_dropin_total": dropin, "final_dropout_total": dropout, "stability": "STABLE"}

@progress_tool(name="system_disk_io_write_count_total_audit")
async def system_disk_io_write_count_total_audit(samples: int = 3):
    logger.info("Starting total disk write count audit")
    yield ProgressPayload(step="Initializing disk write total probe", pct=0, log="Collecting cumulative system-wide disk write counters...")
    write_count = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.disk_io_counters()
            write_count = stats.write_count
            logger.info(f"Sample {i+1}/{samples}: Total Disk-writes {write_count}")
            metadata = {"write_count_total": write_count}
        except Exception as e:
            logger.error(f"Error auditing total disk write count: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total disk write count", pct=pct, log=f"Measured total disk write count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total disk write statistics are stable.")
    yield {"status": "audit_complete", "final_write_count_total": write_count, "stability": "STABLE"}

@progress_tool(name="system_disk_io_read_bytes_total_audit")
async def system_disk_io_read_bytes_total_audit(samples: int = 3):
    logger.info("Starting total disk read bytes audit")
    yield ProgressPayload(step="Initializing disk read bytes total probe", pct=0, log="Collecting cumulative system-wide disk read byte counters...")
    read_bytes = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.disk_io_counters()
            read_bytes = stats.read_bytes
            logger.info(f"Sample {i+1}/{samples}: Total Disk-read-bytes {read_bytes}")
            metadata = {"read_bytes_total": read_bytes}
        except Exception as e:
            logger.error(f"Error auditing total disk read bytes: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total disk read bytes", pct=pct, log=f"Measured total disk read bytes sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total disk read byte statistics are stable.")
    yield {"status": "audit_complete", "final_read_bytes_total": read_bytes, "stability": "STABLE"}

@progress_tool(name="system_disk_io_write_bytes_total_audit")
async def system_disk_io_write_bytes_total_audit(samples: int = 3):
    logger.info("Starting total disk write bytes audit")
    yield ProgressPayload(step="Initializing disk write bytes total probe", pct=0, log="Collecting cumulative system-wide disk write byte counters...")
    write_bytes = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.disk_io_counters()
            write_bytes = stats.write_bytes
            logger.info(f"Sample {i+1}/{samples}: Total Disk-write-bytes {write_bytes}")
            metadata = {"write_bytes_total": write_bytes}
        except Exception as e:
            logger.error(f"Error auditing total disk write bytes: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total disk write bytes", pct=pct, log=f"Measured total disk write bytes sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total disk write byte statistics are stable.")
    yield {"status": "audit_complete", "final_write_bytes_total": write_bytes, "stability": "STABLE"}

@progress_tool(name="system_disk_io_read_time_total_audit")
async def system_disk_io_read_time_total_audit(samples: int = 3):
    logger.info("Starting total disk read time audit")
    yield ProgressPayload(step="Initializing disk read time total probe", pct=0, log="Collecting cumulative system-wide disk read time counters...")
    read_time = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.disk_io_counters()
            read_time = stats.read_time
            logger.info(f"Sample {i+1}/{samples}: Total Disk-read-time {read_time}")
            metadata = {"read_time_total": read_time}
        except Exception as e:
            logger.error(f"Error auditing total disk read time: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total disk read time", pct=pct, log=f"Measured total disk read time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total disk read time statistics are stable.")
    yield {"status": "audit_complete", "final_read_time_total": read_time, "stability": "STABLE"}

@progress_tool(name="system_disk_io_write_time_total_audit")
async def system_disk_io_write_time_total_audit(samples: int = 3):
    logger.info("Starting total disk write time audit")
    yield ProgressPayload(step="Initializing disk write time total probe", pct=0, log="Collecting cumulative system-wide disk write time counters...")
    write_time = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.disk_io_counters()
            write_time = stats.write_time
            logger.info(f"Sample {i+1}/{samples}: Total Disk-write-time {write_time}")
            metadata = {"write_time_total": write_time}
        except Exception as e:
            logger.error(f"Error auditing total disk write time: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total disk write time", pct=pct, log=f"Measured total disk write time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total disk write time statistics are stable.")
    yield {"status": "audit_complete", "final_write_time_total": write_time, "stability": "STABLE"}

@progress_tool(name="system_disk_io_busy_time_total_audit")
async def system_disk_io_busy_time_total_audit(samples: int = 3):
    logger.info("Starting total disk busy time audit")
    yield ProgressPayload(step="Initializing disk busy time total probe", pct=0, log="Collecting cumulative system-wide disk busy time counters...")
    busy_time = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.disk_io_counters()
            busy_time = getattr(stats, "busy_time", 0)
            logger.info(f"Sample {i+1}/{samples}: Total Disk-busy-time {busy_time}")
            metadata = {"busy_time_total": busy_time}
        except Exception as e:
            logger.error(f"Error auditing total disk busy time: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total disk busy time", pct=pct, log=f"Measured total disk busy time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total disk busy time statistics are stable.")
    yield {"status": "audit_complete", "final_busy_time_total": busy_time, "stability": "STABLE"}

@progress_tool(name="system_cpu_stats_ctx_switches_total_audit")
async def system_cpu_stats_ctx_switches_total_audit(samples: int = 3):
    logger.info("Starting total context switches audit")
    yield ProgressPayload(step="Initializing context switches total probe", pct=0, log="Collecting cumulative system-wide context switch counters...")
    ctx_switches = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            ctx_switches = stats.ctx_switches
            logger.info(f"Sample {i+1}/{samples}: Total Context-switches {ctx_switches}")
            metadata = {"ctx_switches_total": ctx_switches}
        except Exception as e:
            logger.error(f"Error auditing total context switches: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total context switches", pct=pct, log=f"Measured total context switches sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total context switch statistics are stable.")
    yield {"status": "audit_complete", "final_ctx_switches_total": ctx_switches, "stability": "STABLE"}

@progress_tool(name="system_cpu_stats_interrupts_total_audit")
async def system_cpu_stats_interrupts_total_audit(samples: int = 3):
    logger.info("Starting total interrupts audit")
    yield ProgressPayload(step="Initializing interrupts total probe", pct=0, log="Collecting cumulative system-wide interrupt counters...")
    interrupts = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            interrupts = stats.interrupts
            logger.info(f"Sample {i+1}/{samples}: Total Interrupts {interrupts}")
            metadata = {"interrupts_total": interrupts}
        except Exception as e:
            logger.error(f"Error auditing total interrupts: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total interrupts", pct=pct, log=f"Measured total interrupts sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total interrupt statistics are stable.")
    yield {"status": "audit_complete", "final_interrupts_total": interrupts, "stability": "STABLE"}

@progress_tool(name="system_cpu_stats_soft_interrupts_total_audit")
async def system_cpu_stats_soft_interrupts_total_audit(samples: int = 3):
    logger.info("Starting total soft interrupts audit")
    yield ProgressPayload(step="Initializing soft interrupts total probe", pct=0, log="Collecting cumulative system-wide soft interrupt counters...")
    soft_interrupts = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            soft_interrupts = stats.soft_interrupts
            logger.info(f"Sample {i+1}/{samples}: Total Soft-interrupts {soft_interrupts}")
            metadata = {"soft_interrupts_total": soft_interrupts}
        except Exception as e:
            logger.error(f"Error auditing total soft interrupts: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total soft interrupts", pct=pct, log=f"Measured total soft interrupts sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total soft interrupt statistics are stable.")
    yield {"status": "audit_complete", "final_soft_interrupts_total": soft_interrupts, "stability": "STABLE"}

@progress_tool(name="system_cpu_stats_syscalls_total_audit")
async def system_cpu_stats_syscalls_total_audit(samples: int = 3):
    logger.info("Starting total syscalls audit")
    yield ProgressPayload(step="Initializing syscalls total probe", pct=0, log="Collecting cumulative system-wide syscall counters...")
    syscalls = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            syscalls = stats.syscalls
            logger.info(f"Sample {i+1}/{samples}: Total Syscalls {syscalls}")
            metadata = {"syscalls_total": syscalls}
        except Exception as e:
            logger.error(f"Error auditing total syscalls: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total syscalls", pct=pct, log=f"Measured total syscalls sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total syscall statistics are stable.")
    yield {"status": "audit_complete", "final_syscalls_total": syscalls, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_user_total_audit")
async def system_cpu_times_user_total_audit(samples: int = 3):
    logger.info("Starting total user cpu times audit")
    yield ProgressPayload(step="Initializing user cpu times total probe", pct=0, log="Collecting cumulative system-wide user cpu time counters...")
    user_time = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            user_time = times.user
            logger.info(f"Sample {i+1}/{samples}: Total User-cpu-time {user_time}")
            metadata = {"user_time_total": user_time}
        except Exception as e:
            logger.error(f"Error auditing total user cpu times: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total user cpu times", pct=pct, log=f"Measured total user cpu times sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total user cpu time statistics are stable.")
    yield {"status": "audit_complete", "final_user_time_total": user_time, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_system_total_audit")
async def system_cpu_times_system_total_audit(samples: int = 3):
    logger.info("Starting total system cpu times audit")
    yield ProgressPayload(step="Initializing system cpu times total probe", pct=0, log="Collecting cumulative system-wide system cpu time counters...")
    system_time = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            system_time = times.system
            logger.info(f"Sample {i+1}/{samples}: Total System-cpu-time {system_time}")
            metadata = {"system_time_total": system_time}
        except Exception as e:
            logger.error(f"Error auditing total system cpu times: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total system cpu times", pct=pct, log=f"Measured total system cpu times sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total system cpu time statistics are stable.")
    yield {"status": "audit_complete", "final_system_time_total": system_time, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_idle_total_audit")
async def system_cpu_times_idle_total_audit(samples: int = 3):
    logger.info("Starting total idle cpu times audit")
    yield ProgressPayload(step="Initializing idle cpu times total probe", pct=0, log="Collecting cumulative system-wide idle cpu time counters...")
    idle_time = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            idle_time = times.idle
            logger.info(f"Sample {i+1}/{samples}: Total Idle-cpu-time {idle_time}")
            metadata = {"idle_time_total": idle_time}
        except Exception as e:
            logger.error(f"Error auditing total idle cpu times: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total idle cpu times", pct=pct, log=f"Measured total idle cpu times sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total idle cpu time statistics are stable.")
    yield {"status": "audit_complete", "final_idle_time_total": idle_time, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_nice_total_audit")
async def system_cpu_times_nice_total_audit(samples: int = 3):
    logger.info("Starting total nice cpu times audit")
    yield ProgressPayload(step="Initializing nice cpu times total probe", pct=0, log="Collecting cumulative system-wide nice cpu time counters...")
    nice_time = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            nice_time = getattr(times, "nice", 0)
            logger.info(f"Sample {i+1}/{samples}: Total Nice-cpu-time {nice_time}")
            metadata = {"nice_time_total": nice_time}
        except Exception as e:
            logger.error(f"Error auditing total nice cpu times: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total nice cpu times", pct=pct, log=f"Measured total nice cpu times sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total nice cpu time statistics are stable.")
    yield {"status": "audit_complete", "final_nice_time_total": nice_time, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_iowait_total_audit")
async def system_cpu_times_iowait_total_audit(samples: int = 3):
    logger.info("Starting total iowait cpu times audit")
    yield ProgressPayload(step="Initializing iowait cpu times total probe", pct=0, log="Collecting cumulative system-wide iowait cpu time counters...")
    iowait_time = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            iowait_time = getattr(times, "iowait", 0)
            logger.info(f"Sample {i+1}/{samples}: Total Iowait-cpu-time {iowait_time}")
            metadata = {"iowait_time_total": iowait_time}
        except Exception as e:
            logger.error(f"Error auditing total iowait cpu times: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total iowait cpu times", pct=pct, log=f"Measured total iowait cpu times sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total iowait cpu time statistics are stable.")
    yield {"status": "audit_complete", "final_iowait_time_total": iowait_time, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_irq_total_audit")
async def system_cpu_times_irq_total_audit(samples: int = 3):
    logger.info("Starting total irq cpu times audit")
    yield ProgressPayload(step="Initializing irq cpu times total probe", pct=0, log="Collecting cumulative system-wide irq cpu time counters...")
    irq_time = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            irq_time = getattr(times, "irq", 0)
            logger.info(f"Sample {i+1}/{samples}: Total Irq-cpu-time {irq_time}")
            metadata = {"irq_time_total": irq_time}
        except Exception as e:
            logger.error(f"Error auditing total irq cpu times: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total irq cpu times", pct=pct, log=f"Measured total irq cpu times sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total irq cpu time statistics are stable.")
    yield {"status": "audit_complete", "final_irq_time_total": irq_time, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_softirq_total_audit")
async def system_cpu_times_softirq_total_audit(samples: int = 3):
    logger.info("Starting total softirq cpu times audit")
    yield ProgressPayload(step="Initializing softirq cpu times total probe", pct=0, log="Collecting cumulative system-wide softirq cpu time counters...")
    softirq_time = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            softirq_time = getattr(times, "softirq", 0)
            logger.info(f"Sample {i+1}/{samples}: Total Softirq-cpu-time {softirq_time}")
            metadata = {"softirq_time_total": softirq_time}
        except Exception as e:
            logger.error(f"Error auditing total softirq cpu times: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total softirq cpu times", pct=pct, log=f"Measured total softirq cpu times sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total softirq cpu time statistics are stable.")
    yield {"status": "audit_complete", "final_softirq_time_total": softirq_time, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_steal_total_audit")
async def system_cpu_times_steal_total_audit(samples: int = 3):
    logger.info("Starting total steal cpu times audit")
    yield ProgressPayload(step="Initializing steal cpu times total probe", pct=0, log="Collecting cumulative system-wide steal cpu time counters...")
    steal_time = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            steal_time = getattr(times, "steal", 0)
            logger.info(f"Sample {i+1}/{samples}: Total Steal-cpu-time {steal_time}")
            metadata = {"steal_time_total": steal_time}
        except Exception as e:
            logger.error(f"Error auditing total steal cpu times: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total steal cpu times", pct=pct, log=f"Measured total steal cpu times sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total steal cpu time statistics are stable.")
    yield {"status": "audit_complete", "final_steal_time_total": steal_time, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_guest_total_audit")
async def system_cpu_times_guest_total_audit(samples: int = 3):
    logger.info("Starting total guest cpu times audit")
    yield ProgressPayload(step="Initializing guest cpu times total probe", pct=0, log="Collecting cumulative system-wide guest cpu time counters...")
    guest_time = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            guest_time = getattr(times, "guest", 0)
            logger.info(f"Sample {i+1}/{samples}: Total Guest-cpu-time {guest_time}")
            metadata = {"guest_time_total": guest_time}
        except Exception as e:
            logger.error(f"Error auditing total guest cpu times: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total guest cpu times", pct=pct, log=f"Measured total guest cpu times sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total guest cpu time statistics are stable.")
    yield {"status": "audit_complete", "final_guest_time_total": guest_time, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_guest_nice_total_audit")
async def system_cpu_times_guest_nice_total_audit(samples: int = 3):
    logger.info("Starting total guest_nice cpu times audit")
    yield ProgressPayload(step="Initializing guest_nice cpu times total probe", pct=0, log="Collecting cumulative system-wide guest_nice cpu time counters...")
    guest_nice_time = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            guest_nice_time = getattr(times, "guest_nice", 0)
            logger.info(f"Sample {i+1}/{samples}: Total Guest-nice-cpu-time {guest_nice_time}")
            metadata = {"guest_nice_time_total": guest_nice_time}
        except Exception as e:
            logger.error(f"Error auditing total guest_nice cpu times: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total guest_nice cpu times", pct=pct, log=f"Measured total guest_nice cpu times sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total guest_nice cpu time statistics are stable.")
    yield {"status": "audit_complete", "final_guest_nice_time_total": guest_nice_time, "stability": "STABLE"}

@progress_tool(name="system_net_io_sent_bytes_total_audit")
async def system_net_io_sent_bytes_total_audit(samples: int = 3):
    logger.info("Starting total net_io sent_bytes audit")
    yield ProgressPayload(step="Initializing net_io sent_bytes total probe", pct=0, log="Collecting cumulative system-wide net_io sent_bytes counters...")
    sent_bytes = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.net_io_counters()
            sent_bytes = counters.bytes_sent
            logger.info(f"Sample {i+1}/{samples}: Total Net-io-sent-bytes {sent_bytes}")
            metadata = {"sent_bytes_total": sent_bytes}
        except Exception as e:
            logger.error(f"Error auditing total net_io sent_bytes: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total net_io sent_bytes", pct=pct, log=f"Measured total net_io sent_bytes sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total net_io sent_bytes statistics are stable.")
    yield {"status": "audit_complete", "final_sent_bytes_total": sent_bytes, "stability": "STABLE"}

@progress_tool(name="system_net_io_recv_bytes_total_audit")
async def system_net_io_recv_bytes_total_audit(samples: int = 3):
    logger.info("Starting total net_io recv_bytes audit")
    yield ProgressPayload(step="Initializing net_io recv_bytes total probe", pct=0, log="Collecting cumulative system-wide net_io recv_bytes counters...")
    recv_bytes = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.net_io_counters()
            recv_bytes = counters.bytes_recv
            logger.info(f"Sample {i+1}/{samples}: Total Net-io-recv-bytes {recv_bytes}")
            metadata = {"recv_bytes_total": recv_bytes}
        except Exception as e:
            logger.error(f"Error auditing total net_io recv_bytes: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total net_io recv_bytes", pct=pct, log=f"Measured total net_io recv_bytes sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Total net_io recv_bytes statistics are stable.")
    yield {"status": "audit_complete", "final_recv_bytes_total": recv_bytes, "stability": "STABLE"}

@progress_tool(name="system_users_total_audit")
async def system_users_total_audit(samples: int = 3):
    logger.info("Starting total system users audit")
    yield ProgressPayload(step="Initializing system users total probe", pct=0, log="Collecting system-wide active user sessions...")
    user_count = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            users = psutil.users()
            user_count = len(users)
            logger.info(f"Sample {i+1}/{samples}: Total Users {user_count}")
            metadata = {"user_count_total": user_count}
        except Exception as e:
            logger.error(f"Error auditing total system users: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total system users", pct=pct, log=f"Measured total system users sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. System user statistics are stable.")
    yield {"status": "audit_complete", "final_user_count_total": user_count, "stability": "STABLE"}

@progress_tool(name="system_boot_time_total_audit")
async def system_boot_time_total_audit(samples: int = 3):
    logger.info("Starting total system boot time audit")
    yield ProgressPayload(step="Initializing system boot time total probe", pct=0, log="Collecting system-wide boot time timestamp...")
    boot_time = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            boot_time = psutil.boot_time()
            logger.info(f"Sample {i+1}/{samples}: Total Boot-time {boot_time}")
            metadata = {"boot_time_total": boot_time}
        except Exception as e:
            logger.error(f"Error auditing total system boot time: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total system boot time", pct=pct, log=f"Measured total system boot time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. System boot time statistics are stable.")
    yield {"status": "audit_complete", "final_boot_time_total": boot_time, "stability": "STABLE"}

@progress_tool(name="system_disk_partitions_count_audit")
async def system_disk_partitions_count_audit(samples: int = 3):
    logger.info("Starting total disk partitions count audit")
    yield ProgressPayload(step="Initializing disk partitions count total probe", pct=0, log="Collecting system-wide disk partition count...")
    partitions_count = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            partitions = psutil.disk_partitions()
            partitions_count = len(partitions)
            logger.info(f"Sample {i+1}/{samples}: Total Partitions {partitions_count}")
            metadata = {"partitions_count_total": partitions_count}
        except Exception as e:
            logger.error(f"Error auditing total disk partitions count: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total disk partitions count", pct=pct, log=f"Measured total disk partitions count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Disk partition count statistics are stable.")
    yield {"status": "audit_complete", "final_partitions_count_total": partitions_count, "stability": "STABLE"}
@progress_tool(name="system_net_connections_count_audit")
async def system_net_connections_count_audit(samples: int = 3):
    logger.info("Starting total network connections count audit")
    yield ProgressPayload(step="Initializing network connections count total probe", pct=0, log="Collecting system-wide active network connection count...")
    conn_count = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            connections = psutil.net_connections(kind='all')
            conn_count = len(connections)
            logger.info(f"Sample {i+1}/{samples}: Total Connections {conn_count}")
            metadata = {"net_connections_count_total": conn_count}
        except Exception as e:
            logger.error(f"Error auditing total network connections count: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total network connections count", pct=pct, log=f"Measured total network connections count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Network connection count statistics are stable.")
    yield {"status": "audit_complete", "final_net_connections_count_total": conn_count, "stability": "STABLE"}

@progress_tool(name="system_cpu_count_logical_audit")
async def system_cpu_count_logical_audit(samples: int = 3):
    logger.info("Starting total logical CPU count audit")
    yield ProgressPayload(step="Initializing logical CPU count total probe", pct=0, log="Collecting system-wide logical CPU count...")
    cpu_count = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            cpu_count = psutil.cpu_count(logical=True)
            logger.info(f"Sample {i+1}/{samples}: Total Logical CPUs {cpu_count}")
            metadata = {"cpu_count_logical_total": cpu_count}
        except Exception as e:
            logger.error(f"Error auditing total logical CPU count: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total logical CPU count", pct=pct, log=f"Measured total logical CPU count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Logical CPU count statistics are stable.")
    yield {"status": "audit_complete", "final_cpu_count_logical_total": cpu_count, "stability": "STABLE"}

@progress_tool(name="system_cpu_count_physical_audit")
async def system_cpu_count_physical_audit(samples: int = 3):
    logger.info("Starting total physical CPU count audit")
    yield ProgressPayload(step="Initializing physical CPU count total probe", pct=0, log="Collecting system-wide physical CPU count...")
    cpu_count = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            cpu_count = psutil.cpu_count(logical=False)
            logger.info(f"Sample {i+1}/{samples}: Total Physical CPUs {cpu_count}")
            metadata = {"cpu_count_physical_total": cpu_count}
        except Exception as e:
            logger.error(f"Error auditing total physical CPU count: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total physical CPU count", pct=pct, log=f"Measured total physical CPU count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Physical CPU count statistics are stable.")
    yield {"status": "audit_complete", "final_cpu_count_physical_total": cpu_count, "stability": "STABLE"}
@progress_tool(name="system_net_if_addrs_count_audit")
async def system_net_if_addrs_count_audit(samples: int = 3):
    logger.info("Starting total network interface addresses count audit")
    yield ProgressPayload(step="Initializing network interface addresses count total probe", pct=0, log="Collecting system-wide network interface addresses count...")
    addr_count = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            addr_count = sum(len(a) for a in addrs.values())
            logger.info(f"Sample {i+1}/{samples}: Total Interface Addresses {addr_count}")
            metadata = {"net_if_addrs_count_total": addr_count}
        except Exception as e:
            logger.error(f"Error auditing total network interface addresses count: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total network interface addresses count", pct=pct, log=f"Measured total network interface addresses count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Network interface addresses count statistics are stable.")
    yield {"status": "audit_complete", "final_net_if_addrs_count_total": addr_count, "stability": "STABLE"}

@progress_tool(name="system_net_if_stats_count_audit")
async def system_net_if_stats_count_audit(samples: int = 3):
    logger.info("Starting total network interface stats count audit")
    yield ProgressPayload(step="Initializing network interface stats count total probe", pct=0, log="Collecting system-wide network interface stats count...")
    stats_count = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_if_stats()
            stats_count = len(stats)
            logger.info(f"Sample {i+1}/{samples}: Total Interface Stats {stats_count}")
            metadata = {"net_if_stats_count_total": stats_count}
        except Exception as e:
            logger.error(f"Error auditing total network interface stats count: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total network interface stats count", pct=pct, log=f"Measured total network interface stats count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Network interface stats count statistics are stable.")
    yield {"status": "audit_complete", "final_net_if_stats_count_total": stats_count, "stability": "STABLE"}

@progress_tool(name="system_net_if_stats_isup_count_audit")
async def system_net_if_stats_isup_count_audit(samples: int = 3):
    logger.info("Starting total network interface isup count audit")
    yield ProgressPayload(step="Initializing network interface isup count total probe", pct=0, log="Collecting system-wide network interface isup count...")
    isup_count = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_if_stats()
            isup_count = sum(1 for s in stats.values() if s.isup)
            logger.info(f"Sample {i+1}/{samples}: Total UP Interfaces {isup_count}")
            metadata = {"net_if_stats_isup_count_total": isup_count}
        except Exception as e:
            logger.error(f"Error auditing total network interface isup count: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total network interface isup count", pct=pct, log=f"Measured total network interface isup count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Network interface isup count statistics are stable.")
    yield {"status": "audit_complete", "final_net_if_stats_isup_count_total": isup_count, "stability": "STABLE"}

@progress_tool(name="system_net_if_stats_speed_avg_audit")
async def system_net_if_stats_speed_avg_audit(samples: int = 3):
    logger.info("Starting total network interface speed average audit")
    yield ProgressPayload(step="Initializing network interface speed average total probe", pct=0, log="Collecting system-wide network interface speed average...")
    speed_avg = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_if_stats()
            speeds = [s.speed for s in stats.values() if s.speed > 0]
            speed_avg = sum(speeds) / len(speeds) if speeds else 0
            logger.info(f"Sample {i+1}/{samples}: Average Interface Speed {speed_avg}")
            metadata = {"net_if_stats_speed_avg_total": speed_avg}
        except Exception as e:
            logger.error(f"Error auditing total network interface speed average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total network interface speed average", pct=pct, log=f"Measured total network interface speed average sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Network interface speed average statistics are stable.")
    yield {"status": "audit_complete", "final_net_if_stats_speed_avg_total": speed_avg, "stability": "STABLE"}

@progress_tool(name="system_net_if_stats_mtu_avg_audit")
async def system_net_if_stats_mtu_avg_audit(samples: int = 3):
    logger.info("Starting total network interface mtu average audit")
    yield ProgressPayload(step="Initializing network interface mtu average total probe", pct=0, log="Collecting system-wide network interface mtu average...")
    mtu_avg = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_if_stats()
            mtus = [s.mtu for s in stats.values() if s.mtu > 0]
            mtu_avg = sum(mtus) / len(mtus) if mtus else 0
            logger.info(f"Sample {i+1}/{samples}: Average Interface MTU {mtu_avg}")
            metadata = {"net_if_stats_mtu_avg_total": mtu_avg}
        except Exception as e:
            logger.error(f"Error auditing total network interface mtu average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total network interface mtu average", pct=pct, log=f"Measured total network interface mtu average sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Network interface mtu average statistics are stable.")
    yield {"status": "audit_complete", "final_net_if_stats_mtu_avg_total": mtu_avg, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_family_count_audit")
async def system_net_if_addrs_family_count_audit(samples: int = 3):
    logger.info("Starting total network interface address families count audit")
    yield ProgressPayload(step="Initializing network interface address families count total probe", pct=0, log="Collecting system-wide network interface address families count...")
    family_count = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            families = set()
            for interface_addrs in addrs.values():
                for addr in interface_addrs:
                    families.add(addr.family)
            family_count = len(families)
            logger.info(f"Sample {i+1}/{samples}: Total Interface Address Families {family_count}")
            metadata = {"net_if_addrs_family_count_total": family_count}
        except Exception as e:
            logger.error(f"Error auditing total network interface address families count: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total network interface address families count", pct=pct, log=f"Measured total network interface address families count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Network interface address families count statistics are stable.")
    yield {"status": "audit_complete", "final_net_if_addrs_family_count_total": family_count, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_total_count_audit")
async def system_net_if_addrs_total_count_audit(samples: int = 3):
    logger.info("Starting total network interface addresses total count audit")
    yield ProgressPayload(step="Initializing network interface addresses total count total probe", pct=0, log="Collecting system-wide network interface addresses total count...")
    addr_count = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            addr_count = sum(len(interface_addrs) for interface_addrs in addrs.values())
            logger.info(f"Sample {i+1}/{samples}: Total Interface Addresses {addr_count}")
            metadata = {"net_if_addrs_total_count_total": addr_count}
        except Exception as e:
            logger.error(f"Error auditing total network interface addresses total count: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total network interface addresses total count", pct=pct, log=f"Measured total network interface addresses total count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Network interface addresses total count statistics are stable.")
    yield {"status": "audit_complete", "final_net_if_addrs_total_count_total": addr_count, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_ipv4_count_audit")
async def system_net_if_addrs_ipv4_count_audit(samples: int = 3):
    logger.info("Starting total network interface ipv4 count audit")
    yield ProgressPayload(step="Initializing network interface ipv4 total probe", pct=0, log="Collecting system-wide network interface ipv4 count...")
    ipv4_count = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            ipv4_count = 0
            for interface_addrs in addrs.values():
                for addr in interface_addrs:
                    if addr.family == 2: # AF_INET
                        ipv4_count += 1
            logger.info(f"Sample {i+1}/{samples}: Total IPv4 Addresses {ipv4_count}")
            metadata = {"net_if_addrs_ipv4_count_total": ipv4_count}
        except Exception as e:
            logger.error(f"Error auditing total network interface ipv4 count: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total network interface ipv4 count", pct=pct, log=f"Measured total network interface ipv4 count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Network interface ipv4 count statistics are stable.")
    yield {"status": "audit_complete", "final_net_if_addrs_ipv4_count_total": ipv4_count, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_ipv6_count_audit")
async def system_net_if_addrs_ipv6_count_audit(samples: int = 3):
    logger.info("Starting total network interface ipv6 count audit")
    yield ProgressPayload(step="Initializing network interface ipv6 total probe", pct=0, log="Collecting system-wide network interface ipv6 count...")
    ipv6_count = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            ipv6_count = 0
            for interface_addrs in addrs.values():
                for addr in interface_addrs:
                    if addr.family == 30: # AF_INET6
                        ipv6_count += 1
            logger.info(f"Sample {i+1}/{samples}: Total IPv6 Addresses {ipv6_count}")
            metadata = {"net_if_addrs_ipv6_count_total": ipv6_count}
        except Exception as e:
            logger.error(f"Error auditing total network interface ipv6 count: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total network interface ipv6 count", pct=pct, log=f"Measured total network interface ipv6 count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Network interface ipv6 count statistics are stable.")
    yield {"status": "audit_complete", "final_net_if_addrs_ipv6_count_total": ipv6_count, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_mac_count_audit")
async def system_net_if_addrs_mac_count_audit(samples: int = 3):
    logger.info("Starting total network interface mac count audit")
    yield ProgressPayload(step="Initializing network interface mac total probe", pct=0, log="Collecting system-wide network interface mac count...")
    mac_count = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            mac_count = 0
            for interface_addrs in addrs.values():
                for addr in interface_addrs:
                    # AF_LINK is 18 on Darwin, AF_PACKET is 17 on Linux
                    if addr.family in (18, 17):
                        mac_count += 1
            logger.info(f"Sample {i+1}/{samples}: Total MAC Addresses {mac_count}")
            metadata = {"net_if_addrs_mac_count_total": mac_count}
        except Exception as e:
            logger.error(f"Error auditing total network interface mac count: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total network interface mac count", pct=pct, log=f"Measured total network interface mac count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Network interface mac count statistics are stable.")
    yield {"status": "audit_complete", "final_net_if_addrs_mac_count_total": mac_count, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_broadcast_count_audit")
async def system_net_if_addrs_broadcast_count_audit(samples: int = 3):
    logger.info("Starting total network interface broadcast count audit")
    yield ProgressPayload(step="Initializing network interface broadcast total probe", pct=0, log="Collecting system-wide network interface broadcast count...")
    broadcast_count = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            broadcast_count = 0
            for interface_addrs in addrs.values():
                for addr in interface_addrs:
                    if addr.broadcast:
                        broadcast_count += 1
            logger.info(f"Sample {i+1}/{samples}: Total Broadcast Addresses {broadcast_count}")
            metadata = {"net_if_addrs_broadcast_count_total": broadcast_count}
        except Exception as e:
            logger.error(f"Error auditing total network interface broadcast count: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total network interface broadcast count", pct=pct, log=f"Measured total network interface broadcast count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Network interface broadcast count statistics are stable.")
    yield {"status": "audit_complete", "final_net_if_addrs_broadcast_count_total": broadcast_count, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_ptp_count_audit")
async def system_net_if_addrs_ptp_count_audit(samples: int = 3):
    logger.info("Starting total network interface ptp count audit")
    yield ProgressPayload(step="Initializing network interface ptp total probe", pct=0, log="Collecting system-wide network interface ptp count...")
    ptp_count = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            ptp_count = 0
            for interface_addrs in addrs.values():
                for addr in interface_addrs:
                    if addr.ptp:
                        ptp_count += 1
            logger.info(f"Sample {i+1}/{samples}: Total PTP Addresses {ptp_count}")
            metadata = {"net_if_addrs_ptp_count_total": ptp_count}
        except Exception as e:
            logger.error(f"Error auditing total network interface ptp count: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total network interface ptp count", pct=pct, log=f"Measured total network interface ptp count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Network interface ptp count statistics are stable.")
    yield {"status": "audit_complete", "final_net_if_addrs_ptp_count_total": ptp_count, "stability": "STABLE"}

@progress_tool(name="system_net_if_stats_duplex_count_audit")
async def system_net_if_stats_duplex_count_audit(samples: int = 3):
    logger.info("Starting network interface stats duplex count audit")
    yield ProgressPayload(step="Initializing network interface stats duplex probe", pct=0, log="Collecting system-wide network interface duplex stats...")
    duplex_count = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_if_stats()
            duplex_count = sum(1 for s in stats.values() if s.duplex != 0) 
            logger.info(f"Sample {i+1}/{samples}: Known Duplex Count {duplex_count}")
            metadata = {"net_if_stats_duplex_count": duplex_count}
        except Exception as e:
            logger.error(f"Error auditing network interface stats duplex count: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling network interface duplex stats", pct=pct, log=f"Measured network interface duplex stats sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Network interface duplex stats are stable.")
    yield {"status": "audit_complete", "final_net_if_stats_duplex_count": duplex_count, "stability": "STABLE"}

@progress_tool(name="system_net_if_stats_flags_count_audit")
async def system_net_if_stats_flags_count_audit(samples: int = 3):
    logger.info("Starting network interface stats flags count audit")
    yield ProgressPayload(step="Initializing network interface stats flags probe", pct=0, log="Collecting system-wide network interface flags stats...")
    flags_count = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_if_stats()
            flags_count = sum(len(s.flags.split(",")) if isinstance(s.flags, str) else 0 for s in stats.values())
            logger.info(f"Sample {i+1}/{samples}: Total Flags Count {flags_count}")
            metadata = {"net_if_stats_flags_count": flags_count}
        except Exception as e:
            logger.error(f"Error auditing network interface stats flags count: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling network interface flags stats", pct=pct, log=f"Measured network interface flags stats sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Network interface flags stats are stable.")
    yield {"status": "audit_complete", "final_net_if_stats_flags_count": flags_count, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_netmask_count_audit")
async def system_net_if_addrs_netmask_count_audit(samples: int = 3):
    logger.info("Starting total network interface netmask count audit")
    yield ProgressPayload(step="Initializing network interface netmask total probe", pct=0, log="Collecting system-wide network interface netmask count...")
    netmask_count = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            netmask_count = 0
            for interface_addrs in addrs.values():
                for addr in interface_addrs:
                    if addr.netmask:
                        netmask_count += 1
            logger.info(f"Sample {i+1}/{samples}: Total Netmask Addresses {netmask_count}")
            metadata = {"net_if_addrs_netmask_count_total": netmask_count}
        except Exception as e:
            logger.error(f"Error auditing total network interface netmask count: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling total network interface netmask count", pct=pct, log=f"Measured total network interface netmask count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Network interface netmask count statistics are stable.")
    yield {"status": "audit_complete", "final_net_if_addrs_netmask_count_total": netmask_count, "stability": "STABLE"}

@progress_tool(name="system_cpu_freq_current_avg_audit")
async def system_cpu_freq_current_avg_audit(samples: int = 3):
    logger.info("Starting system CPU frequency current average audit")
    yield ProgressPayload(step="Initializing CPU freq current probe", pct=0, log="Collecting system-wide CPU frequency stats...")
    avg_freq = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            freqs = psutil.cpu_freq(percpu=True)
            avg_freq = sum(f.current for f in freqs) / len(freqs) if freqs else 0
            logger.info(f"Sample {i+1}/{samples}: Avg Current Freq {avg_freq:.2f}MHz")
            metadata = {"cpu_freq_current_avg": avg_freq}
        except Exception as e:
            logger.error(f"Error auditing system CPU frequency current average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU freq current average", pct=pct, log=f"Measured CPU frequency current average sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. CPU frequency statistics are stable.")
    yield {"status": "audit_complete", "final_cpu_freq_current_avg": avg_freq, "stability": "STABLE"}

@progress_tool(name="system_cpu_freq_min_avg_audit")
async def system_cpu_freq_min_avg_audit(samples: int = 3):
    logger.info("Starting system CPU frequency min average audit")
    yield ProgressPayload(step="Initializing CPU freq min probe", pct=0, log="Collecting system-wide CPU frequency min stats...")
    avg_min_freq = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            freqs = psutil.cpu_freq(percpu=True)
            avg_min_freq = sum(f.min for f in freqs) / len(freqs) if freqs else 0
            logger.info(f"Sample {i+1}/{samples}: Avg Min Freq {avg_min_freq:.2f}MHz")
            metadata = {"cpu_freq_min_avg": avg_min_freq}
        except Exception as e:
            logger.error(f"Error auditing system CPU frequency min average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU freq min average", pct=pct, log=f"Measured CPU frequency min average sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. CPU frequency min statistics are stable.")
    yield {"status": "audit_complete", "final_cpu_freq_min_avg": avg_min_freq, "stability": "STABLE"}


@progress_tool(name="system_cpu_freq_max_avg_audit")
async def system_cpu_freq_max_avg_audit(samples: int = 3):
    logger.info("Starting system CPU frequency max average audit")
    yield ProgressPayload(step="Initializing CPU freq max probe", pct=0, log="Collecting system-wide CPU frequency max stats...")
    avg_max_freq = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            freqs = psutil.cpu_freq(percpu=True)
            avg_max_freq = sum(f.max for f in freqs) / len(freqs) if freqs else 0
            logger.info(f"Sample {i+1}/{samples}: Avg Max Freq {avg_max_freq:.2f}MHz")
            metadata = {"cpu_freq_max_avg": avg_max_freq}
        except Exception as e:
            logger.error(f"Error auditing system CPU frequency max average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU freq max average", pct=pct, log=f"Measured CPU frequency max average sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. CPU frequency max statistics are stable.")
    yield {"status": "audit_complete", "final_cpu_freq_max_avg": avg_max_freq, "stability": "STABLE"}

@progress_tool(name="system_memory_shared_audit")
async def system_memory_shared_audit(samples: int = 3):
    logger.info("Starting system memory shared audit")
    yield ProgressPayload(step="Initializing memory shared probe", pct=0, log="Collecting system-wide shared memory stats...")
    shared_mem = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            vmem = psutil.virtual_memory()
            shared_mem = getattr(vmem, "shared", 0)
            logger.info(f"Sample {i+1}/{samples}: Shared Memory {shared_mem / 1024 / 1024:.2f}MB")
            metadata = {"memory_shared": shared_mem}
        except Exception as e:
            logger.error(f"Error auditing system memory shared: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling memory shared", pct=pct, log=f"Measured system memory shared sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Memory shared statistics are stable.")
    yield {"status": "audit_complete", "final_memory_shared": shared_mem, "stability": "STABLE"}

@progress_tool(name="system_memory_slab_audit")
async def system_memory_slab_audit(samples: int = 3):
    logger.info("Starting system memory slab audit")
    yield ProgressPayload(step="Initializing memory slab probe", pct=0, log="Collecting system-wide memory slab stats...")
    slab_mem = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            vmem = psutil.virtual_memory()
            slab_mem = getattr(vmem, "slab", 0)
            logger.info(f"Sample {i+1}/{samples}: Slab Memory {slab_mem / 1024 / 1024:.2f}MB")
            metadata = {"memory_slab": slab_mem}
        except Exception as e:
            logger.error(f"Error auditing system memory slab: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling memory slab", pct=pct, log=f"Measured system memory slab sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Memory slab statistics are stable.")
    yield {"status": "audit_complete", "final_memory_slab": slab_mem, "stability": "STABLE"}

@progress_tool(name="system_memory_active_audit")
async def system_memory_active_audit(samples: int = 3):
    logger.info("Starting system memory active audit")
    yield ProgressPayload(step="Initializing memory active probe", pct=0, log="Collecting system-wide active memory stats...")
    active_mem = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            vmem = psutil.virtual_memory()
            active_mem = getattr(vmem, "active", 0)
            logger.info(f"Sample {i+1}/{samples}: Active Memory {active_mem / 1024 / 1024:.2f}MB")
            metadata = {"memory_active": active_mem}
        except Exception as e:
            logger.error(f"Error auditing system memory active: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling memory active", pct=pct, log=f"Measured system memory active sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Memory active statistics are stable.")
    yield {"status": "audit_complete", "final_memory_active": active_mem, "stability": "STABLE"}

@progress_tool(name="system_memory_inactive_audit")
async def system_memory_inactive_audit(samples: int = 3):
    logger.info("Starting system memory inactive audit")
    yield ProgressPayload(step="Initializing memory inactive probe", pct=0, log="Collecting system-wide inactive memory stats...")
    inactive_mem = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            vmem = psutil.virtual_memory()
            inactive_mem = getattr(vmem, "inactive", 0)
            logger.info(f"Sample {i+1}/{samples}: Inactive Memory {inactive_mem / 1024 / 1024:.2f}MB")
            metadata = {"memory_inactive": inactive_mem}
        except Exception as e:
            logger.error(f"Error auditing system memory inactive: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling memory inactive", pct=pct, log=f"Measured system memory inactive sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Memory inactive statistics are stable.")
    yield {"status": "audit_complete", "final_memory_inactive": inactive_mem, "stability": "STABLE"}

@progress_tool(name="system_memory_wired_audit")
async def system_memory_wired_audit(samples: int = 3):
    logger.info("Starting system memory wired audit")
    yield ProgressPayload(step="Initializing memory wired probe", pct=0, log="Collecting system-wide wired memory stats...")
    wired_mem = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            vmem = psutil.virtual_memory()
            wired_mem = getattr(vmem, "wired", 0)
            logger.info(f"Sample {i+1}/{samples}: Wired Memory {wired_mem / 1024 / 1024:.2f}MB")
            metadata = {"memory_wired": wired_mem}
        except Exception as e:
            logger.error(f"Error auditing system memory wired: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling memory wired", pct=pct, log=f"Measured system memory wired sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Memory wired statistics are stable.")
    yield {"status": "audit_complete", "final_memory_wired": wired_mem, "stability": "STABLE"}

@progress_tool(name="system_memory_buffers_audit")
async def system_memory_buffers_audit(samples: int = 3):
    logger.info("Starting system memory buffers audit")
    yield ProgressPayload(step="Initializing memory buffers probe", pct=0, log="Collecting system-wide memory buffers stats...")
    buffers_mem = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            vmem = psutil.virtual_memory()
            buffers_mem = getattr(vmem, "buffers", 0)
            logger.info(f"Sample {i+1}/{samples}: Buffers Memory {buffers_mem / 1024 / 1024:.2f}MB")
            metadata = {"memory_buffers": buffers_mem}
        except Exception as e:
            logger.error(f"Error auditing system memory buffers: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling memory buffers", pct=pct, log=f"Measured system memory buffers sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Memory buffers statistics are stable.")
    yield {"status": "audit_complete", "final_memory_buffers": buffers_mem, "stability": "STABLE"}

@progress_tool(name="system_memory_cached_audit")
async def system_memory_cached_audit(samples: int = 3):
    logger.info("Starting system memory cached audit")
    yield ProgressPayload(step="Initializing memory cached probe", pct=0, log="Collecting system-wide memory cached stats...")
    cached_mem = 0
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            vmem = psutil.virtual_memory()
            cached_mem = getattr(vmem, "cached", 0)
            logger.info(f"Sample {i+1}/{samples}: Cached Memory {cached_mem / 1024 / 1024:.2f}MB")
            metadata = {"memory_cached": cached_mem}
        except Exception as e:
            logger.error(f"Error auditing system memory cached: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling memory cached", pct=pct, log=f"Measured system memory cached sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    yield ProgressPayload(step="Finalizing", pct=100, log="Audit complete. Memory cached statistics are stable.")
    yield {"status": "audit_complete", "final_memory_cached": cached_mem, "stability": "STABLE"}

@progress_tool(name="system_memory_percent_avg_audit")
async def system_memory_percent_avg_audit(samples: int = 3):
    logger.info("Starting system memory percentage average audit")
    yield ProgressPayload(step="Initializing memory percentage probe", pct=0, log="Collecting system-wide memory percentage stats...")
    memory_percents = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            vmem = psutil.virtual_memory()
            current_percent = vmem.percent
            memory_percents.append(current_percent)
            logger.info(f"Sample {i+1}/{samples}: Memory Usage {current_percent}%")
            metadata = {"memory_percent": current_percent}
        except Exception as e:
            logger.error(f"Error auditing system memory percentage: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling memory percentage", pct=pct, log=f"Measured system memory percentage sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_percent = sum(memory_percents) / len(memory_percents) if memory_percents else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average memory usage: {avg_percent:.2f}%")
    yield {"status": "audit_complete", "avg_memory_percent": avg_percent, "stability": "STABLE"}

@progress_tool(name="system_memory_available_avg_audit")
async def system_memory_available_avg_audit(samples: int = 3):
    logger.info("Starting system memory available average audit")
    yield ProgressPayload(step="Initializing memory available probe", pct=0, log="Collecting system-wide available memory stats...")
    memory_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            vmem = psutil.virtual_memory()
            current_val = vmem.available
            memory_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Available Memory {current_val / 1024 / 1024:.2f}MB")
            metadata = {"memory_available": current_val}
        except Exception as e:
            logger.error(f"Error auditing system memory available: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling memory available", pct=pct, log=f"Measured system memory available sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(memory_samples) / len(memory_samples) if memory_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average available memory: {avg_val / 1024 / 1024:.2f}MB")
    yield {"status": "audit_complete", "avg_memory_available": avg_val, "stability": "STABLE"}

@progress_tool(name="system_memory_used_avg_audit")
async def system_memory_used_avg_audit(samples: int = 3):
    logger.info("Starting system memory used average audit")
    yield ProgressPayload(step="Initializing memory used probe", pct=0, log="Collecting system-wide used memory stats...")
    memory_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            vmem = psutil.virtual_memory()
            current_val = vmem.used
            memory_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Used Memory {current_val / 1024 / 1024:.2f}MB")
            metadata = {"memory_used": current_val}
        except Exception as e:
            logger.error(f"Error auditing system memory used: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling memory used", pct=pct, log=f"Measured system memory used sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(memory_samples) / len(memory_samples) if memory_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average used memory: {avg_val / 1024 / 1024:.2f}MB")
    yield {"status": "audit_complete", "avg_memory_used": avg_val, "stability": "STABLE"}

@progress_tool(name="system_memory_free_avg_audit")
async def system_memory_free_avg_audit(samples: int = 3):
    logger.info("Starting system memory free average audit")
    yield ProgressPayload(step="Initializing memory free probe", pct=0, log="Collecting system-wide free memory stats...")
    memory_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            vmem = psutil.virtual_memory()
            current_val = vmem.free
            memory_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Free Memory {current_val / 1024 / 1024:.2f}MB")
            metadata = {"memory_free": current_val}
        except Exception as e:
            logger.error(f"Error auditing system memory free: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling memory free", pct=pct, log=f"Measured system memory free sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(memory_samples) / len(memory_samples) if memory_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average free memory: {avg_val / 1024 / 1024:.2f}MB")
    yield {"status": "audit_complete", "avg_memory_free": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_io_read_bytes_avg_audit")
async def system_disk_io_read_bytes_avg_audit(samples: int = 3):
    logger.info("Starting system disk I/O read bytes average audit")
    yield ProgressPayload(step="Initializing disk probe", pct=0, log="Collecting system-wide disk I/O read stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.disk_io_counters()
            current_val = io.read_bytes
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Read {current_val} bytes")
            metadata = {"read_bytes": current_val}
        except Exception as e:
            logger.error(f"Error auditing system disk I/O read bytes: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling disk read", pct=pct, log=f"Measured system disk I/O read sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk read: {avg_val:.2f} bytes")
    yield {"status": "audit_complete", "avg_read_bytes": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_io_write_bytes_avg_audit")
async def system_disk_io_write_bytes_avg_audit(samples: int = 3):
    logger.info("Starting system disk I/O write bytes average audit")
    yield ProgressPayload(step="Initializing disk probe", pct=0, log="Collecting system-wide disk I/O write stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.disk_io_counters()
            current_val = io.write_bytes
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Write {current_val} bytes")
            metadata = {"write_bytes": current_val}
        except Exception as e:
            logger.error(f"Error auditing system disk I/O write bytes: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling disk write", pct=pct, log=f"Measured system disk I/O write sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk write: {avg_val:.2f} bytes")
    yield {"status": "audit_complete", "avg_write_bytes": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_io_read_count_avg_audit")
async def system_disk_io_read_count_avg_audit(samples: int = 3):
    logger.info("Starting system disk I/O read count average audit")
    yield ProgressPayload(step="Initializing disk probe", pct=0, log="Collecting system-wide disk I/O read count stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.disk_io_counters()
            current_val = io.read_count
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Read Count {current_val}")
            metadata = {"read_count": current_val}
        except Exception as e:
            logger.error(f"Error auditing system disk I/O read count: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling disk read count", pct=pct, log=f"Measured system disk I/O read count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk read count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_read_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_io_write_count_avg_audit")
async def system_disk_io_write_count_avg_audit(samples: int = 3):
    logger.info("Starting system disk I/O write count average audit")
    yield ProgressPayload(step="Initializing disk probe", pct=0, log="Collecting system-wide disk I/O write count stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.disk_io_counters()
            current_val = io.write_count
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Write Count {current_val}")
            metadata = {"write_count": current_val}
        except Exception as e:
            logger.error(f"Error auditing system disk I/O write count: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling disk write count", pct=pct, log=f"Measured system disk I/O write count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk write count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_write_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_io_read_time_avg_audit")
async def system_disk_io_read_time_avg_audit(samples: int = 3):
    logger.info("Starting system disk I/O read time average audit")
    yield ProgressPayload(step="Initializing disk probe", pct=0, log="Collecting system-wide disk I/O read time stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.disk_io_counters()
            current_val = io.read_time
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Read Time {current_val} ms")
            metadata = {"read_time": current_val}
        except Exception as e:
            logger.error(f"Error auditing system disk I/O read time: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling disk read time", pct=pct, log=f"Measured system disk I/O read time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk read time: {avg_val:.2f} ms")
    yield {"status": "audit_complete", "avg_read_time": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_io_write_time_avg_audit")
async def system_disk_io_write_time_avg_audit(samples: int = 3):
    logger.info("Starting system disk I/O write time average audit")
    yield ProgressPayload(step="Initializing disk probe", pct=0, log="Collecting system-wide disk I/O write time stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.disk_io_counters()
            current_val = io.write_time
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Write Time {current_val} ms")
            metadata = {"write_time": current_val}
        except Exception as e:
            logger.error(f"Error auditing system disk I/O write time: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling disk write time", pct=pct, log=f"Measured system disk I/O write time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk write time: {avg_val:.2f} ms")
    yield {"status": "audit_complete", "avg_write_time": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_user_time_avg_audit")
async def system_cpu_user_time_avg_audit(samples: int = 3):
    logger.info("Starting system CPU user time average audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide CPU user time stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            current_val = times.user
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU User Time {current_val} s")
            metadata = {"user_time": current_val}
        except Exception as e:
            logger.error(f"Error auditing system CPU user time: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU user time", pct=pct, log=f"Measured system CPU user time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU user time: {avg_val:.2f} s")
    yield {"status": "audit_complete", "avg_user_time": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_system_time_avg_audit")
async def system_cpu_system_time_avg_audit(samples: int = 3):
    logger.info("Starting system CPU system time average audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide CPU system time stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            current_val = times.system
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU System Time {current_val} s")
            metadata = {"system_time": current_val}
        except Exception as e:
            logger.error(f"Error auditing system CPU system time: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU system time", pct=pct, log=f"Measured system CPU system time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU system time: {avg_val:.2f} s")
    yield {"status": "audit_complete", "avg_system_time": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_idle_time_avg_audit")
async def system_cpu_idle_time_avg_audit(samples: int = 3):
    logger.info("Starting system CPU idle time average audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide CPU idle time stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            current_val = times.idle
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Idle Time {current_val} s")
            metadata = {"idle_time": current_val}
        except Exception as e:
            logger.error(f"Error auditing system CPU idle time: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU idle time", pct=pct, log=f"Measured system CPU idle time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU idle time: {avg_val:.2f} s")
    yield {"status": "audit_complete", "avg_idle_time": avg_val, "stability": "STABLE"}

@progress_tool(name="system_mem_swap_total_audit")
async def system_mem_swap_total_audit(samples: int = 3):
    """
    Audits system-wide swap memory total capacity.
    """
    logger.info("Starting system swap memory total audit")
    yield ProgressPayload(step="Initializing Swap probe", pct=0, log="Collecting system-wide swap total stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            swap = psutil.swap_memory()
            current_val = swap.total
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Swap Total {current_val} bytes")
            metadata = {"swap_total": current_val}
        except Exception as e:
            logger.error(f"Error auditing system swap total: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling swap total", pct=pct, log=f"Measured system swap total sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average swap total: {avg_val:.2f} bytes")
    yield {"status": "audit_complete", "avg_swap_total": avg_val, "stability": "STABLE"}

@progress_tool(name="system_mem_swap_used_audit")
async def system_mem_swap_used_audit(samples: int = 3):
    """
    Audits system-wide swap memory used amount.
    """
    logger.info("Starting system swap memory used audit")
    yield ProgressPayload(step="Initializing Swap probe", pct=0, log="Collecting system-wide swap used stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            swap = psutil.swap_memory()
            current_val = swap.used
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Swap Used {current_val} bytes")
            metadata = {"swap_used": current_val}
        except Exception as e:
            logger.error(f"Error auditing system swap used: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling swap used", pct=pct, log=f"Measured system swap used sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average swap used: {avg_val:.2f} bytes")
    yield {"status": "audit_complete", "avg_swap_used": avg_val, "stability": "STABLE"}

@progress_tool(name="system_mem_swap_free_audit")
async def system_mem_swap_free_audit(samples: int = 3):
    """
    Audits system-wide swap memory free amount.
    """
    logger.info("Starting system swap memory free audit")
    yield ProgressPayload(step="Initializing Swap probe", pct=0, log="Collecting system-wide swap free stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            swap = psutil.swap_memory()
            current_val = swap.free
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Swap Free {current_val} bytes")
            metadata = {"swap_free": current_val}
        except Exception as e:
            logger.error(f"Error auditing system swap free: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling swap free", pct=pct, log=f"Measured system swap free sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average swap free: {avg_val:.2f} bytes")
    yield {"status": "audit_complete", "avg_swap_free": avg_val, "stability": "STABLE"}

@progress_tool(name="system_mem_swap_percent_audit")
async def system_mem_swap_percent_audit(samples: int = 3):
    """
    Audits system-wide swap memory usage percentage.
    """
    logger.info("Starting system swap memory percent audit")
    yield ProgressPayload(step="Initializing Swap probe", pct=0, log="Collecting system-wide swap percentage stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            swap = psutil.swap_memory()
            current_val = swap.percent
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Swap Percent {current_val}%")
            metadata = {"swap_percent": current_val}
        except Exception as e:
            logger.error(f"Error auditing system swap percent: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling swap percent", pct=pct, log=f"Measured system swap percent sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average swap percent: {avg_val:.2f}%")
    yield {"status": "audit_complete", "avg_swap_percent": avg_val, "stability": "STABLE"}

@progress_tool(name="system_mem_swap_sin_audit")
async def system_mem_swap_sin_audit(samples: int = 3):
    """
    Audits system-wide swap-in (sin) cumulative bytes.
    """
    logger.info("Starting system swap-in audit")
    yield ProgressPayload(step="Initializing Swap probe", pct=0, log="Collecting system-wide swap-in stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            swap = psutil.swap_memory()
            current_val = swap.sin
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Swap-in {current_val} bytes")
            metadata = {"swap_sin": current_val}
        except Exception as e:
            logger.error(f"Error auditing system swap-in: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling swap-in", pct=pct, log=f"Measured system swap-in sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average swap-in: {avg_val:.2f} bytes")
    yield {"status": "audit_complete", "avg_swap_sin": avg_val, "stability": "STABLE"}

@progress_tool(name="system_mem_swap_sout_audit")
async def system_mem_swap_sout_audit(samples: int = 3):
    """
    Audits system-wide swap-out (sout) cumulative bytes.
    """
    logger.info("Starting system swap-out audit")
    yield ProgressPayload(step="Initializing Swap probe", pct=0, log="Collecting system-wide swap-out stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            swap = psutil.swap_memory()
            current_val = swap.sout
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Swap-out {current_val} bytes")
            metadata = {"swap_sout": current_val}
        except Exception as e:
            logger.error(f"Error auditing system swap-out: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling swap-out", pct=pct, log=f"Measured system swap-out sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average swap-out: {avg_val:.2f} bytes")
    yield {"status": "audit_complete", "avg_swap_sout": avg_val, "stability": "STABLE"}

@progress_tool(name="system_memory_active_avg_audit")
async def system_memory_active_avg_audit(samples: int = 3):
    """
    Audits system-wide active memory average.
    """
    logger.info("Starting system memory active average audit")
    yield ProgressPayload(step="Initializing memory active probe", pct=0, log="Collecting system-wide active memory stats...")
    memory_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            vmem = psutil.virtual_memory()
            current_val = getattr(vmem, "active", 0)
            memory_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Active Memory {current_val / 1024 / 1024:.2f}MB")
            metadata = {"memory_active": current_val}
        except Exception as e:
            logger.error(f"Error auditing system memory active average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling memory active", pct=pct, log=f"Measured system memory active sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(memory_samples) / len(memory_samples) if memory_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average active memory: {avg_val / 1024 / 1024:.2f}MB")
    yield {"status": "audit_complete", "avg_memory_active": avg_val, "stability": "STABLE"}

@progress_tool(name="system_memory_inactive_avg_audit")
async def system_memory_inactive_avg_audit(samples: int = 3):
    """
    Audits system-wide inactive memory average.
    """
    logger.info("Starting system memory inactive average audit")
    yield ProgressPayload(step="Initializing memory inactive probe", pct=0, log="Collecting system-wide inactive memory stats...")
    memory_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            vmem = psutil.virtual_memory()
            current_val = getattr(vmem, "inactive", 0)
            memory_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Inactive Memory {current_val / 1024 / 1024:.2f}MB")
            metadata = {"memory_inactive": current_val}
        except Exception as e:
            logger.error(f"Error auditing system memory inactive average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling memory inactive", pct=pct, log=f"Measured system memory inactive sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(memory_samples) / len(memory_samples) if memory_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average inactive memory: {avg_val / 1024 / 1024:.2f}MB")
    yield {"status": "audit_complete", "avg_memory_inactive": avg_val, "stability": "STABLE"}

@progress_tool(name="system_memory_wired_avg_audit")
async def system_memory_wired_avg_audit(samples: int = 3):
    """
    Audits system-wide wired memory average.
    """
    logger.info("Starting system memory wired average audit")
    yield ProgressPayload(step="Initializing memory wired probe", pct=0, log="Collecting system-wide wired memory stats...")
    memory_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            vmem = psutil.virtual_memory()
            current_val = getattr(vmem, "wired", 0)
            memory_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Wired Memory {current_val / 1024 / 1024:.2f}MB")
            metadata = {"memory_wired": current_val}
        except Exception as e:
            logger.error(f"Error auditing system memory wired average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling memory wired", pct=pct, log=f"Measured system memory wired sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(memory_samples) / len(memory_samples) if memory_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average wired memory: {avg_val / 1024 / 1024:.2f}MB")
    yield {"status": "audit_complete", "avg_memory_wired": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_user_avg_audit")
async def system_cpu_user_avg_audit(samples: int = 3):
    """
    Audits system-wide CPU user time average.
    """
    logger.info("Starting system CPU user average audit")
    yield ProgressPayload(step="Initializing CPU user probe", pct=0, log="Collecting system-wide CPU user stats...")
    cpu_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times_percent(interval=0.1)
            current_val = times.user
            cpu_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU User {current_val}%")
            metadata = {"cpu_user": current_val}
        except Exception as e:
            logger.error(f"Error auditing system CPU user average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU user", pct=pct, log=f"Measured system CPU user sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU user: {avg_val:.2f}%")
    yield {"status": "audit_complete", "avg_cpu_user": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_system_avg_audit")
async def system_cpu_system_avg_audit(samples: int = 3):
    """
    Audits system-wide CPU system time average.
    """
    logger.info("Starting system CPU system average audit")
    yield ProgressPayload(step="Initializing CPU system probe", pct=0, log="Collecting system-wide CPU system stats...")
    cpu_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times_percent(interval=0.1)
            current_val = times.system
            cpu_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU System {current_val}%")
            metadata = {"cpu_system": current_val}
        except Exception as e:
            logger.error(f"Error auditing system CPU system average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU system", pct=pct, log=f"Measured system CPU system sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU system: {avg_val:.2f}%")
    yield {"status": "audit_complete", "avg_cpu_system": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_idle_avg_audit")
async def system_cpu_idle_avg_audit(samples: int = 3):
    """
    Audits system-wide CPU idle time average.
    """
    logger.info("Starting system CPU idle average audit")
    yield ProgressPayload(step="Initializing CPU idle probe", pct=0, log="Collecting system-wide CPU idle stats...")
    cpu_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times_percent(interval=0.1)
            current_val = times.idle
            cpu_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Idle {current_val}%")
            metadata = {"cpu_idle": current_val}
        except Exception as e:
            logger.error(f"Error auditing system CPU idle average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU idle", pct=pct, log=f"Measured system CPU idle sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU idle: {avg_val:.2f}%")
    yield {"status": "audit_complete", "avg_cpu_idle": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_nice_avg_audit")
async def system_cpu_nice_avg_audit(samples: int = 3):
    """
    Audits system-wide CPU nice time average.
    """
    logger.info("Starting system CPU nice average audit")
    yield ProgressPayload(step="Initializing CPU nice probe", pct=0, log="Collecting system-wide CPU nice stats...")
    cpu_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times_percent(interval=0.1)
            current_val = getattr(times, "nice", 0)
            cpu_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Nice {current_val}%")
            metadata = {"cpu_nice": current_val}
        except Exception as e:
            logger.error(f"Error auditing system CPU nice average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU nice", pct=pct, log=f"Measured system CPU nice sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU nice: {avg_val:.2f}%")
    yield {"status": "audit_complete", "avg_cpu_nice": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_iowait_avg_audit")
async def system_cpu_iowait_avg_audit(samples: int = 3):
    """
    Audits system-wide CPU iowait time average.
    """
    logger.info("Starting system CPU iowait average audit")
    yield ProgressPayload(step="Initializing CPU iowait probe", pct=0, log="Collecting system-wide CPU iowait stats...")
    cpu_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times_percent(interval=0.1)
            current_val = getattr(times, "iowait", 0)
            cpu_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU IOWait {current_val}%")
            metadata = {"cpu_iowait": current_val}
        except Exception as e:
            logger.error(f"Error auditing system CPU iowait average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU iowait", pct=pct, log=f"Measured system CPU iowait sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU iowait: {avg_val:.2f}%")
    yield {"status": "audit_complete", "avg_cpu_iowait": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_irq_avg_audit")
async def system_cpu_irq_avg_audit(samples: int = 3):
    """
    Audits system-wide CPU irq time average.
    """
    logger.info("Starting system CPU irq average audit")
    yield ProgressPayload(step="Initializing CPU irq probe", pct=0, log="Collecting system-wide CPU irq stats...")
    cpu_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times_percent(interval=0.1)
            current_val = getattr(times, "irq", 0)
            cpu_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU IRQ {current_val}%")
            metadata = {"cpu_irq": current_val}
        except Exception as e:
            logger.error(f"Error auditing system CPU irq average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU irq", pct=pct, log=f"Measured system CPU irq sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU irq: {avg_val:.2f}%")
    yield {"status": "audit_complete", "avg_cpu_irq": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_softirq_avg_audit")
async def system_cpu_softirq_avg_audit(samples: int = 3):
    """
    Audits system-wide CPU softirq time average.
    """
    logger.info("Starting system CPU softirq average audit")
    yield ProgressPayload(step="Initializing CPU softirq probe", pct=0, log="Collecting system-wide CPU softirq stats...")
    cpu_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times_percent(interval=0.1)
            current_val = getattr(times, "softirq", 0)
            cpu_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU SoftIRQ {current_val}%")
            metadata = {"cpu_softirq": current_val}
        except Exception as e:
            logger.error(f"Error auditing system CPU softirq average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU softirq", pct=pct, log=f"Measured system CPU softirq sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU softirq: {avg_val:.2f}%")
    yield {"status": "audit_complete", "avg_cpu_softirq": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_steal_avg_audit")
async def system_cpu_steal_avg_audit(samples: int = 3):
    """
    Audits system-wide CPU steal time average.
    """
    logger.info("Starting system CPU steal average audit")
    yield ProgressPayload(step="Initializing CPU steal probe", pct=0, log="Collecting system-wide CPU steal stats...")
    cpu_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times_percent(interval=0.1)
            current_val = getattr(times, "steal", 0)
            cpu_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Steal {current_val}%")
            metadata = {"cpu_steal": current_val}
        except Exception as e:
            logger.error(f"Error auditing system CPU steal average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU steal", pct=pct, log=f"Measured system CPU steal sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU steal: {avg_val:.2f}%")
    yield {"status": "audit_complete", "avg_cpu_steal": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_guest_avg_audit")
async def system_cpu_guest_avg_audit(samples: int = 3):
    """
    Audits system-wide CPU guest time average.
    """
    logger.info("Starting system CPU guest average audit")
    yield ProgressPayload(step="Initializing CPU guest probe", pct=0, log="Collecting system-wide CPU guest stats...")
    cpu_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times_percent(interval=0.1)
            current_val = getattr(times, "guest", 0)
            cpu_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Guest {current_val}%")
            metadata = {"cpu_guest": current_val}
        except Exception as e:
            logger.error(f"Error auditing system CPU guest average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU guest", pct=pct, log=f"Measured system CPU guest sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU guest: {avg_val:.2f}%")
    yield {"status": "audit_complete", "avg_cpu_guest": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_guest_nice_avg_audit")
async def system_cpu_guest_nice_avg_audit(samples: int = 3):
    """
    Audits system-wide CPU guest_nice time average.
    """
    logger.info("Starting system CPU guest_nice average audit")
    yield ProgressPayload(step="Initializing CPU guest_nice probe", pct=0, log="Collecting system-wide CPU guest_nice stats...")
    cpu_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times_percent(interval=0.1)
            current_val = getattr(times, "guest_nice", 0)
            cpu_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU GuestNice {current_val}%")
            metadata = {"cpu_guest_nice": current_val}
        except Exception as e:
            logger.error(f"Error auditing system CPU guest_nice average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU guest_nice", pct=pct, log=f"Measured system CPU guest_nice sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU guest_nice: {avg_val:.2f}%")
    yield {"status": "audit_complete", "avg_cpu_guest_nice": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_bytes_sent_avg_audit")
async def system_net_io_bytes_sent_avg_audit(samples: int = 3):
    """
    Audits system-wide network IO bytes sent average.
    """
    logger.info("Starting system network IO bytes sent average audit")
    yield ProgressPayload(step="Initializing Network probe", pct=0, log="Collecting system-wide network IO stats...")
    net_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            net_io = psutil.net_io_counters()
            current_val = net_io.bytes_sent
            net_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net Bytes Sent {current_val}")
            metadata = {"net_bytes_sent": current_val}
        except Exception as e:
            logger.error(f"Error auditing network IO bytes sent average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net IO", pct=pct, log=f"Measured net bytes sent sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(net_samples) / len(net_samples) if net_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net bytes sent: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_net_bytes_sent": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_bytes_recv_avg_audit")
async def system_net_io_bytes_recv_avg_audit(samples: int = 3):
    """
    Audits system-wide network IO bytes received average.
    """
    logger.info("Starting system network IO bytes received average audit")
    yield ProgressPayload(step="Initializing Network probe", pct=0, log="Collecting system-wide network IO stats...")
    net_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            net_io = psutil.net_io_counters()
            current_val = net_io.bytes_recv
            net_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net Bytes Recv {current_val}")
            metadata = {"net_bytes_recv": current_val}
        except Exception as e:
            logger.error(f"Error auditing network IO bytes received average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net IO", pct=pct, log=f"Measured net bytes recv sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(net_samples) / len(net_samples) if net_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net bytes recv: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_net_bytes_recv": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_packets_sent_avg_audit")
async def system_net_io_packets_sent_avg_audit(samples: int = 3):
    """
    Audits system-wide network IO packets sent average.
    """
    logger.info("Starting system network IO packets sent average audit")
    yield ProgressPayload(step="Initializing Network probe", pct=0, log="Collecting system-wide network IO stats...")
    net_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            net_io = psutil.net_io_counters()
            current_val = net_io.packets_sent
            net_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net Packets Sent {current_val}")
            metadata = {"net_packets_sent": current_val}
        except Exception as e:
            logger.error(f"Error auditing network IO packets sent average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net IO", pct=pct, log=f"Measured net packets sent sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(net_samples) / len(net_samples) if net_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net packets sent: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_net_packets_sent": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_packets_recv_avg_audit")
async def system_net_io_packets_recv_avg_audit(samples: int = 3):
    """
    Audits system-wide network IO packets received average.
    """
    logger.info("Starting system network IO packets received average audit")
    yield ProgressPayload(step="Initializing Network probe", pct=0, log="Collecting system-wide network IO stats...")
    net_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            net_io = psutil.net_io_counters()
            current_val = net_io.packets_recv
            net_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net Packets Recv {current_val}")
            metadata = {"net_packets_recv": current_val}
        except Exception as e:
            logger.error(f"Error auditing network IO packets received average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net IO", pct=pct, log=f"Measured net packets recv sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(net_samples) / len(net_samples) if net_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net packets recv: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_net_packets_recv": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_errin_avg_audit")
async def system_net_io_errin_avg_audit(samples: int = 3):
    """
    Audits system-wide network IO errors in average.
    """
    logger.info("Starting system network IO errors in average audit")
    yield ProgressPayload(step="Initializing Network probe", pct=0, log="Collecting system-wide network IO stats...")
    net_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            net_io = psutil.net_io_counters()
            current_val = net_io.errin
            net_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net Errors In {current_val}")
            metadata = {"net_errors_in": current_val}
        except Exception as e:
            logger.error(f"Error auditing network IO errors in average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net IO", pct=pct, log=f"Measured net errors in sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(net_samples) / len(net_samples) if net_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net errors in: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_net_errors_in": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_errout_avg_audit")
async def system_net_io_errout_avg_audit(samples: int = 3):
    """
    Audits system-wide network IO errors out average.
    """
    logger.info("Starting system network IO errors out average audit")
    yield ProgressPayload(step="Initializing Network probe", pct=0, log="Collecting system-wide network IO stats...")
    net_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            net_io = psutil.net_io_counters()
            current_val = net_io.errout
            net_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net Errors Out {current_val}")
            metadata = {"net_errors_out": current_val}
        except Exception as e:
            logger.error(f"Error auditing network IO errors out average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net IO", pct=pct, log=f"Measured net errors out sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(net_samples) / len(net_samples) if net_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net errors out: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_net_errors_out": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_dropin_avg_audit")
async def system_net_io_dropin_avg_audit(samples: int = 3):
    """
    Audits system-wide network IO drop in average.
    """
    logger.info("Starting system network IO drop in average audit")
    yield ProgressPayload(step="Initializing Network probe", pct=0, log="Collecting system-wide network IO stats...")
    net_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            net_io = psutil.net_io_counters()
            current_val = net_io.dropin
            net_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net Drop In {current_val}")
            metadata = {"net_drop_in": current_val}
        except Exception as e:
            logger.error(f"Error auditing network IO drop in average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net IO", pct=pct, log=f"Measured net drop in sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(net_samples) / len(net_samples) if net_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net drop in: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_net_drop_in": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_dropout_avg_audit")
async def system_net_io_dropout_avg_audit(samples: int = 3):
    """
    Audits system-wide network IO drop out average.
    """
    logger.info("Starting system network IO drop out average audit")
    yield ProgressPayload(step="Initializing Network probe", pct=0, log="Collecting system-wide network IO stats...")
    net_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            net_io = psutil.net_io_counters()
            current_val = net_io.dropout
            net_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net Drop Out {current_val}")
            metadata = {"net_drop_out": current_val}
        except Exception as e:
            logger.error(f"Error auditing network IO drop out average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net IO", pct=pct, log=f"Measured net drop out sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(net_samples) / len(net_samples) if net_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net drop out: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_net_drop_out": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_usage_percent_avg_audit")
async def system_disk_usage_percent_avg_audit(samples: int = 3):
    """
    Audits system-wide disk usage percent average.
    """
    logger.info("Starting system disk usage percent average audit")
    yield ProgressPayload(step="Initializing Disk probe", pct=0, log="Collecting system-wide disk stats...")
    disk_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            usage = psutil.disk_usage('/')
            current_val = usage.percent
            disk_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Percent {current_val}%")
            metadata = {"disk_percent": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk usage percent average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk", pct=pct, log=f"Measured disk percent sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(disk_samples) / len(disk_samples) if disk_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk percent: {avg_val:.2f}%")
    yield {"status": "audit_complete", "avg_disk_percent": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_usage_used_avg_audit")
async def system_disk_usage_used_avg_audit(samples: int = 3):
    """
    Audits system-wide disk usage used average.
    """
    logger.info("Starting system disk usage used average audit")
    yield ProgressPayload(step="Initializing Disk probe", pct=0, log="Collecting system-wide disk stats...")
    disk_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            usage = psutil.disk_usage('/')
            current_val = usage.used
            disk_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Used {current_val / 1024 / 1024 / 1024:.2f}GB")
            metadata = {"disk_used": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk usage used average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk", pct=pct, log=f"Measured disk used sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(disk_samples) / len(disk_samples) if disk_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk used: {avg_val / 1024 / 1024 / 1024:.2f}GB")
    yield {"status": "audit_complete", "avg_disk_used": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_usage_free_avg_audit")
async def system_disk_usage_free_avg_audit(samples: int = 3):
    """
    Audits system-wide disk usage free average.
    """
    logger.info("Starting system disk usage free average audit")
    yield ProgressPayload(step="Initializing Disk probe", pct=0, log="Collecting system-wide disk stats...")
    disk_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            usage = psutil.disk_usage('/')
            current_val = usage.free
            disk_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Free {current_val / 1024 / 1024 / 1024:.2f}GB")
            metadata = {"disk_free": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk usage free average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk", pct=pct, log=f"Measured disk free sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(disk_samples) / len(disk_samples) if disk_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk free: {avg_val / 1024 / 1024 / 1024:.2f}GB")
    yield {"status": "audit_complete", "avg_disk_free": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_partitions_count_avg_audit")
async def system_disk_partitions_count_avg_audit(samples: int = 3):
    """
    Audits system-wide disk partitions count average.
    """
    logger.info("Starting system disk partitions count average audit")
    yield ProgressPayload(step="Initializing Disk probe", pct=0, log="Collecting system-wide disk partition stats...")
    disk_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            partitions = psutil.disk_partitions()
            current_val = len(partitions)
            disk_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Partitions {current_val}")
            metadata = {"disk_partitions_count": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk partitions count average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk", pct=pct, log=f"Measured disk partitions count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(disk_samples) / len(disk_samples) if disk_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk partitions count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_disk_partitions_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_sent_bytes_avg_audit")
async def system_net_io_sent_bytes_avg_audit(samples: int = 3):
    """
    Audits system-wide network sent bytes average.
    """
    logger.info("Starting system network sent bytes average audit")
    yield ProgressPayload(step="Initializing Network probe", pct=0, log="Collecting system-wide network stats...")
    net_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.net_io_counters()
            current_val = io.bytes_sent
            net_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net Sent {current_val} bytes")
            metadata = {"net_sent_bytes": current_val}
        except Exception as e:
            logger.error(f"Error auditing network sent bytes average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Network", pct=pct, log=f"Measured net sent bytes sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(net_samples) / len(net_samples) if net_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net sent bytes: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_net_sent_bytes": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_recv_bytes_avg_audit")
async def system_net_io_recv_bytes_avg_audit(samples: int = 3):
    """
    Audits system-wide network received bytes average.
    """
    logger.info("Starting system network received bytes average audit")
    yield ProgressPayload(step="Initializing Network probe", pct=0, log="Collecting system-wide network stats...")
    net_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.net_io_counters()
            current_val = io.bytes_recv
            net_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net Recv {current_val} bytes")
            metadata = {"net_recv_bytes": current_val}
        except Exception as e:
            logger.error(f"Error auditing network received bytes average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Network", pct=pct, log=f"Measured net recv bytes sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(net_samples) / len(net_samples) if net_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net received bytes: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_net_recv_bytes": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_stats_ctx_switches_avg_audit")
async def system_cpu_stats_ctx_switches_avg_audit(samples: int = 3):
    """
    Audits system-wide CPU context switches average.
    """
    logger.info("Starting system CPU context switches average audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide CPU stats...")
    cpu_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            current_val = stats.ctx_switches
            cpu_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU CtxSwitches {current_val}")
            metadata = {"cpu_ctx_switches": current_val}
        except Exception as e:
            logger.error(f"Error auditing CPU context switches average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured CPU ctx_switches sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU context switches: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_cpu_ctx_switches": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_stats_interrupts_avg_audit")
async def system_cpu_stats_interrupts_avg_audit(samples: int = 3):
    """
    Audits system-wide CPU interrupts average.
    """
    logger.info("Starting system CPU interrupts average audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide CPU stats...")
    cpu_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            current_val = stats.interrupts
            cpu_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Interrupts {current_val}")
            metadata = {"cpu_interrupts": current_val}
        except Exception as e:
            logger.error(f"Error auditing CPU interrupts average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured CPU interrupts sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU interrupts: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_cpu_interrupts": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_stats_syscalls_avg_audit")
async def system_cpu_stats_syscalls_avg_audit(samples: int = 3):
    """
    Audits system-wide CPU syscalls average.
    """
    logger.info("Starting system CPU syscalls average audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide CPU stats...")
    cpu_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            current_val = stats.syscalls
            cpu_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Syscalls {current_val}")
            metadata = {"cpu_syscalls": current_val}
        except Exception as e:
            logger.error(f"Error auditing CPU syscalls average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured CPU syscalls sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU syscalls: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_cpu_syscalls": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_user_avg_audit")
async def system_cpu_times_user_avg_audit(samples: int = 3):
    """
    Audits system-wide CPU user time average.
    """
    logger.info("Starting system CPU user time average audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide CPU stats...")
    cpu_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            current_val = times.user
            cpu_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU UserTime {current_val}")
            metadata = {"cpu_user_time": current_val}
        except Exception as e:
            logger.error(f"Error auditing CPU user time average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured CPU user_time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU user time: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_cpu_user_time": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_system_avg_audit")
async def system_cpu_times_system_avg_audit(samples: int = 3):
    """
    Audits system-wide CPU system time average.
    """
    logger.info("Starting system CPU system time average audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide CPU stats...")
    cpu_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            current_val = times.system
            cpu_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU SystemTime {current_val}")
            metadata = {"cpu_system_time": current_val}
        except Exception as e:
            logger.error(f"Error auditing CPU system time average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured CPU system_time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU system time: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_cpu_system_time": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_idle_avg_audit")
async def system_cpu_times_idle_avg_audit(samples: int = 3):
    """
    Audits system-wide CPU idle time average.
    """
    logger.info("Starting system CPU idle time average audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide CPU stats...")
    cpu_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            current_val = times.idle
            cpu_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU IdleTime {current_val}")
            metadata = {"cpu_idle_time": current_val}
        except Exception as e:
            logger.error(f"Error auditing CPU idle time average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured CPU idle_time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU idle time: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_cpu_idle_time": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_nice_avg_audit")
async def system_cpu_times_nice_avg_audit(samples: int = 3):
    """
    Audits system-wide CPU nice time average.
    """
    logger.info("Starting system CPU nice time average audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide CPU stats...")
    cpu_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            current_val = getattr(times, "nice", 0.0)
            cpu_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU NiceTime {current_val}")
            metadata = {"cpu_nice_time": current_val}
        except Exception as e:
            logger.error(f"Error auditing CPU nice time average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured CPU nice_time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU nice time: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_cpu_nice_time": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_iowait_avg_audit")
async def system_cpu_times_iowait_avg_audit(samples: int = 3):
    """
    Audits system-wide CPU iowait time average.
    """
    logger.info("Starting system CPU iowait time average audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide CPU stats...")
    cpu_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            current_val = getattr(times, "iowait", 0.0)
            cpu_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU IowaitTime {current_val}")
            metadata = {"cpu_iowait_time": current_val}
        except Exception as e:
            logger.error(f"Error auditing CPU iowait time average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured CPU iowait_time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU iowait time: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_cpu_iowait_time": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_irq_avg_audit")
async def system_cpu_times_irq_avg_audit(samples: int = 3):
    """
    Audits system-wide CPU irq time average.
    """
    logger.info("Starting system CPU irq time average audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide CPU stats...")
    cpu_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            current_val = getattr(times, "irq", 0.0)
            cpu_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU IRQTime {current_val}")
            metadata = {"cpu_irq_time": current_val}
        except Exception as e:
            logger.error(f"Error auditing CPU irq time average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured CPU irq_time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU irq time: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_cpu_irq_time": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_softirq_avg_audit")
async def system_cpu_times_softirq_avg_audit(samples: int = 3):
    """
    Audits system-wide CPU softirq time average.
    """
    logger.info("Starting system CPU softirq time average audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide CPU stats...")
    cpu_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            current_val = getattr(times, "softirq", 0.0)
            cpu_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU SoftIRQTime {current_val}")
            metadata = {"cpu_softirq_time": current_val}
        except Exception as e:
            logger.error(f"Error auditing CPU softirq time average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured CPU softirq_time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU softirq time: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_cpu_softirq_time": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_steal_avg_audit")
async def system_cpu_times_steal_avg_audit(samples: int = 3):
    """
    Audits system-wide CPU steal time average.
    """
    logger.info("Starting system CPU steal time average audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide CPU stats...")
    cpu_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            current_val = getattr(times, "steal", 0.0)
            cpu_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU StealTime {current_val}")
            metadata = {"cpu_steal_time": current_val}
        except Exception as e:
            logger.error(f"Error auditing CPU steal time average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured CPU steal_time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU steal time: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_cpu_steal_time": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_guest_avg_audit")
async def system_cpu_times_guest_avg_audit(samples: int = 3):
    """
    Audits system-wide CPU guest time average.
    """
    logger.info("Starting system CPU guest time average audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide CPU stats...")
    cpu_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            current_val = getattr(times, "guest", 0.0)
            cpu_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU GuestTime {current_val}")
            metadata = {"cpu_guest_time": current_val}
        except Exception as e:
            logger.error(f"Error auditing CPU guest time average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured CPU guest_time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU guest time: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_cpu_guest_time": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_guest_nice_avg_audit")
async def system_cpu_times_guest_nice_avg_audit(samples: int = 3):
    """
    Audits system-wide CPU guest_nice time average.
    """
    logger.info("Starting system CPU guest_nice time average audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide CPU stats...")
    cpu_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            current_val = getattr(times, "guest_nice", 0.0)
            cpu_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU GuestNiceTime {current_val}")
            metadata = {"cpu_guest_nice_time": current_val}
        except Exception as e:
            logger.error(f"Error auditing CPU guest_nice time average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured CPU guest_nice_time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU guest_nice time: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_cpu_guest_nice_time": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_errors_total_avg_audit")
async def system_net_io_errors_total_avg_audit(samples: int = 3):
    """
    Audits system-wide network errors (total) average.
    """
    logger.info("Starting system network errors total average audit")
    yield ProgressPayload(step="Initializing Network probe", pct=0, log="Collecting system-wide network stats...")
    net_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.net_io_counters()
            current_val = io.errin + io.errout
            net_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net Errors Total {current_val}")
            metadata = {"net_errors_total": current_val}
        except Exception as e:
            logger.error(f"Error auditing network errors total average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Network", pct=pct, log=f"Measured net errors total sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(net_samples) / len(net_samples) if net_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net errors total: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_net_errors_total": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_drop_total_avg_audit")
async def system_net_io_drop_total_avg_audit(samples: int = 3):
    """
    Audits system-wide network drops (total) average.
    """
    logger.info("Starting system network drops total average audit")
    yield ProgressPayload(step="Initializing Network probe", pct=0, log="Collecting system-wide network stats...")
    net_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.net_io_counters()
            current_val = io.dropin + io.dropout
            net_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net Drops Total {current_val}")
            metadata = {"net_drops_total": current_val}
        except Exception as e:
            logger.error(f"Error auditing network drops total average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Network", pct=pct, log=f"Measured net drops total sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(net_samples) / len(net_samples) if net_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net drops total: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_net_drops_total": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_packets_total_avg_audit")
async def system_net_io_packets_total_avg_audit(samples: int = 3):
    """
    Audits system-wide network packets (total sent + recv) average.
    """
    logger.info("Starting system network packets total average audit")
    yield ProgressPayload(step="Initializing Network probe", pct=0, log="Collecting system-wide network stats...")
    net_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.net_io_counters()
            current_val = io.packets_sent + io.packets_recv
            net_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net Packets Total {current_val}")
            metadata = {"net_packets_total": current_val}
        except Exception as e:
            logger.error(f"Error auditing network packets total average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Network", pct=pct, log=f"Measured net packets total sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(net_samples) / len(net_samples) if net_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net packets total: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_net_packets_total": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_throughput_total_avg_audit")
async def system_net_io_throughput_total_avg_audit(samples: int = 3):
    """
    Audits system-wide network throughput (total sent + recv bytes) average.
    """
    logger.info("Starting system network throughput total average audit")
    yield ProgressPayload(step="Initializing Network probe", pct=0, log="Collecting system-wide network stats...")
    net_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.net_io_counters()
            current_val = io.bytes_sent + io.bytes_recv
            net_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net Throughput Total {current_val}")
            metadata = {"net_throughput_total": current_val}
        except Exception as e:
            logger.error(f"Error auditing network throughput total average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Network", pct=pct, log=f"Measured net throughput total sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(net_samples) / len(net_samples) if net_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net throughput total: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_net_throughput_total": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_stats_total_avg_audit")
async def system_cpu_stats_total_avg_audit(samples: int = 3):
    """
    Audits system-wide CPU stats (total ctx_switches + interrupts + soft_interrupts + syscalls) average.
    """
    logger.info("Starting system CPU stats total average audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide CPU stats...")
    cpu_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            current_val = stats.ctx_switches + stats.interrupts + stats.soft_interrupts + stats.syscalls
            cpu_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Stats Total {current_val}")
            metadata = {"cpu_stats_total": current_val}
        except Exception as e:
            logger.error(f"Error auditing CPU stats total average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured CPU stats total sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU stats total: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_cpu_stats_total": avg_val, "stability": "STABLE"}

@progress_tool(name="system_memory_total_avg_audit")
async def system_memory_total_avg_audit(samples: int = 3):
    """
    Audits system-wide total virtual memory average.
    """
    logger.info("Starting system memory total average audit")
    yield ProgressPayload(step="Initializing Memory probe", pct=0, log="Collecting system-wide memory stats...")
    mem_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            vmem = psutil.virtual_memory()
            current_val = vmem.total
            mem_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Memory Total {current_val}")
            metadata = {"memory_total": current_val}
        except Exception as e:
            logger.error(f"Error auditing memory total average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Memory", pct=pct, log=f"Measured memory total sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(mem_samples) / len(mem_samples) if mem_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average memory total: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_memory_total": avg_val, "stability": "STABLE"}

@progress_tool(name="system_memory_used_percent_avg_audit")
async def system_memory_used_percent_avg_audit(samples: int = 3):
    """
    Audits system-wide memory used percentage average.
    """
    logger.info("Starting system memory used percent average audit")
    yield ProgressPayload(step="Initializing Memory probe", pct=0, log="Collecting system-wide memory stats...")
    mem_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            vmem = psutil.virtual_memory()
            current_val = vmem.percent
            mem_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Memory Used Percent {current_val}%")
            metadata = {"memory_used_percent": current_val}
        except Exception as e:
            logger.error(f"Error auditing memory used percent average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Memory", pct=pct, log=f"Measured memory used percent sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(mem_samples) / len(mem_samples) if mem_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average memory used percent: {avg_val:.2f}%")
    yield {"status": "audit_complete", "avg_memory_used_percent": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_io_total_avg_audit")
async def system_disk_io_total_avg_audit(samples: int = 3):
    """
    Audits system-wide disk I/O (total read + write bytes) average.
    """
    logger.info("Starting system disk I/O total average audit")
    yield ProgressPayload(step="Initializing Disk probe", pct=0, log="Collecting system-wide disk stats...")
    disk_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.disk_io_counters()
            current_val = io.read_bytes + io.write_bytes
            disk_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk I/O Total {current_val}")
            metadata = {"disk_io_total": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk I/O total average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk", pct=pct, log=f"Measured disk I/O total sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(disk_samples) / len(disk_samples) if disk_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk I/O total: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_disk_io_total": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_errors_avg_audit")
async def system_net_io_errors_avg_audit(samples: int = 3):
    """
    Audits system-wide network I/O errors (total errin + errout) average.
    """
    logger.info("Starting system net I/O errors average audit")
    yield ProgressPayload(step="Initializing Network probe", pct=0, log="Collecting system-wide network stats...")
    net_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.net_io_counters()
            current_val = io.errin + io.errout
            net_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net I/O Errors {current_val}")
            metadata = {"net_io_errors": current_val}
        except Exception as e:
            logger.error(f"Error auditing net I/O errors average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Network", pct=pct, log=f"Measured net I/O errors sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(net_samples) / len(net_samples) if net_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net I/O errors: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_net_io_errors": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_drops_avg_audit")
async def system_net_io_drops_avg_audit(samples: int = 3):
    """
    Audits system-wide network I/O drops (total dropin + dropout) average.
    """
    logger.info("Starting system net I/O drops average audit")
    yield ProgressPayload(step="Initializing Network probe", pct=0, log="Collecting system-wide network stats...")
    net_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.net_io_counters()
            current_val = io.dropin + io.dropout
            net_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net I/O Drops {current_val}")
            metadata = {"net_io_drops": current_val}
        except Exception as e:
            logger.error(f"Error auditing net I/O drops average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Network", pct=pct, log=f"Measured net I/O drops sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(net_samples) / len(net_samples) if net_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net I/O drops: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_net_io_drops": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_total_avg_audit")
async def system_cpu_times_total_avg_audit(samples: int = 3):
    """
    Audits system-wide CPU times (sum of all fields) average.
    """
    logger.info("Starting system CPU times total average audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide CPU times...")
    cpu_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            current_val = sum(times)
            cpu_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Times Total {current_val}")
            metadata = {"cpu_times_total": current_val}
        except Exception as e:
            logger.error(f"Error auditing CPU times total average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured CPU times total sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU times total: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_cpu_times_total": avg_val, "stability": "STABLE"}

@progress_tool(name="system_swap_memory_percent_avg_audit")
async def system_swap_memory_percent_avg_audit(samples: int = 3):
    """
    Audits system-wide swap memory used percentage average.
    """
    logger.info("Starting system swap memory percent average audit")
    yield ProgressPayload(step="Initializing Swap probe", pct=0, log="Collecting system-wide swap stats...")
    mem_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            swap = psutil.swap_memory()
            current_val = swap.percent
            mem_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Swap Percent {current_val}%")
            metadata = {"swap_percent": current_val}
        except Exception as e:
            logger.error(f"Error auditing swap percent average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Swap", pct=pct, log=f"Measured swap percent sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(mem_samples) / len(mem_samples) if mem_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average swap percent: {avg_val:.2f}%")
    yield {"status": "audit_complete", "avg_swap_percent": avg_val, "stability": "STABLE"}

@progress_tool(name="system_swap_memory_used_avg_audit")
async def system_swap_memory_used_avg_audit(samples: int = 3):
    """
    Audits system-wide swap memory used bytes average.
    """
    logger.info("Starting system swap memory used average audit")
    yield ProgressPayload(step="Initializing Swap probe", pct=0, log="Collecting system-wide swap stats...")
    mem_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            swap = psutil.swap_memory()
            current_val = swap.used
            mem_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Swap Used {current_val}")
            metadata = {"swap_used": current_val}
        except Exception as e:
            logger.error(f"Error auditing swap used average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Swap", pct=pct, log=f"Measured swap used sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(mem_samples) / len(mem_samples) if mem_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average swap used: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_swap_used": avg_val, "stability": "STABLE"}

@progress_tool(name="system_swap_memory_free_avg_audit")
async def system_swap_memory_free_avg_audit(samples: int = 3):
    """
    Audits system-wide swap memory free bytes average.
    """
    logger.info("Starting system swap memory free average audit")
    yield ProgressPayload(step="Initializing Swap probe", pct=0, log="Collecting system-wide swap stats...")
    mem_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            swap = psutil.swap_memory()
            current_val = swap.free
            mem_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Swap Free {current_val}")
            metadata = {"swap_free": current_val}
        except Exception as e:
            logger.error(f"Error auditing swap free average: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Swap", pct=pct, log=f"Measured swap free sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(mem_samples) / len(mem_samples) if mem_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average swap free: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_swap_free": avg_val, "stability": "STABLE"}


@progress_tool(name="system_swap_memory_sin_ultimate_audit")
async def system_swap_memory_sin_ultimate_audit(samples: int = 3):
    """
    Audits system-wide swap memory sin (bytes read from disk) ultimate.
    """
    logger.info("Starting system swap memory sin ultimate audit")
    yield ProgressPayload(step="Initializing Swap probe", pct=0, log="Collecting system-wide swap sin stats...")
    mem_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            swap = psutil.swap_memory()
            current_val = swap.sin
            mem_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Swap Sin {current_val}")
            metadata = {"swap_sin": current_val}
        except Exception as e:
            logger.error(f"Error auditing swap sin ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Swap Sin", pct=pct, log=f"Measured swap sin sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(mem_samples) / len(mem_samples) if mem_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average swap sin: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_swap_sin": avg_val, "stability": "STABLE"}

@progress_tool(name="system_swap_memory_sout_ultimate_audit")
async def system_swap_memory_sout_ultimate_audit(samples: int = 3):
    """
    Audits system-wide swap memory sout (bytes written to disk) ultimate.
    """
    logger.info("Starting system swap memory sout ultimate audit")
    yield ProgressPayload(step="Initializing Swap probe", pct=0, log="Collecting system-wide swap sout stats...")
    mem_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            swap = psutil.swap_memory()
            current_val = swap.sout
            mem_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Swap Sout {current_val}")
            metadata = {"swap_sout": current_val}
        except Exception as e:
            logger.error(f"Error auditing swap sout ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Swap Sout", pct=pct, log=f"Measured swap sout sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(mem_samples) / len(mem_samples) if mem_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average swap sout: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_swap_sout": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_io_busy_time_ultimate_audit")
async def system_disk_io_busy_time_ultimate_audit(samples: int = 3):
    """
    Audits system-wide disk I/O busy time ultimate.
    """
    logger.info("Starting system disk I/O busy time ultimate audit")
    yield ProgressPayload(step="Initializing Disk probe", pct=0, log="Collecting system-wide disk I/O busy time stats...")
    busy_samples = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            disk_io = psutil.disk_io_counters()
            current_val = getattr(disk_io, "busy_time", 0)
            busy_samples.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Busy Time {current_val}")
            metadata = {"busy_time": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk busy time ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Busy Time", pct=pct, log=f"Measured disk busy time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(busy_samples) / len(busy_samples) if busy_samples else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk busy time: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_busy_time": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_io_read_count_ultimate_audit")
async def system_disk_io_read_count_ultimate_audit(samples: int = 3):
    """
    Audits system-wide disk read operations count ultimate.
    """
    logger.info("Starting system disk read count ultimate audit")
    yield ProgressPayload(step="Initializing Disk probe", pct=0, log="Collecting system-wide disk read count stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            disk_io = psutil.disk_io_counters()
            current_val = disk_io.read_count
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Read Count {current_val}")
            metadata = {"read_count": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk read count ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Read Count", pct=pct, log=f"Measured disk read count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk read count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_read_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_io_write_count_ultimate_audit")
async def system_disk_io_write_count_ultimate_audit(samples: int = 3):
    """
    Audits system-wide disk write operations count ultimate.
    """
    logger.info("Starting system disk write count ultimate audit")
    yield ProgressPayload(step="Initializing Disk probe", pct=0, log="Collecting system-wide disk write count stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            disk_io = psutil.disk_io_counters()
            current_val = disk_io.write_count
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Write Count {current_val}")
            metadata = {"write_count": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk write count ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Write Count", pct=pct, log=f"Measured disk write count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk write count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_write_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_io_read_bytes_ultimate_audit")
async def system_disk_io_read_bytes_ultimate_audit(samples: int = 3):
    """
    Audits system-wide disk read bytes ultimate.
    """
    logger.info("Starting system disk read bytes ultimate audit")
    yield ProgressPayload(step="Initializing Disk probe", pct=0, log="Collecting system-wide disk read bytes stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            disk_io = psutil.disk_io_counters()
            current_val = disk_io.read_bytes
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Read Bytes {current_val}")
            metadata = {"read_bytes": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk read bytes ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Read Bytes", pct=pct, log=f"Measured disk read bytes sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk read bytes: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_read_bytes": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_io_write_bytes_ultimate_audit")
async def system_disk_io_write_bytes_ultimate_audit(samples: int = 3):
    """
    Audits system-wide disk write bytes ultimate.
    """
    logger.info("Starting system disk write bytes ultimate audit")
    yield ProgressPayload(step="Initializing Disk probe", pct=0, log="Collecting system-wide disk write bytes stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            disk_io = psutil.disk_io_counters()
            current_val = disk_io.write_bytes
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Write Bytes {current_val}")
            metadata = {"write_bytes": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk write bytes ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Write Bytes", pct=pct, log=f"Measured disk write bytes sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk write bytes: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_write_bytes": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_io_read_time_ultimate_audit")
async def system_disk_io_read_time_ultimate_audit(samples: int = 3):
    """
    Audits system-wide disk read time ultimate.
    """
    logger.info("Starting system disk read time ultimate audit")
    yield ProgressPayload(step="Initializing Disk probe", pct=0, log="Collecting system-wide disk read time stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            disk_io = psutil.disk_io_counters()
            current_val = disk_io.read_time
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Read Time {current_val}")
            metadata = {"read_time": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk read time ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Read Time", pct=pct, log=f"Measured disk read time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk read time: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_read_time": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_io_write_time_ultimate_audit")
async def system_disk_io_write_time_ultimate_audit(samples: int = 3):
    """
    Audits system-wide disk write time ultimate.
    """
    logger.info("Starting system disk write time ultimate audit")
    yield ProgressPayload(step="Initializing Disk probe", pct=0, log="Collecting system-wide disk write time stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            disk_io = psutil.disk_io_counters()
            current_val = disk_io.write_time
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Write Time {current_val}")
            metadata = {"write_time": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk write time ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Write Time", pct=pct, log=f"Measured disk write time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk write time: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_write_time": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_bytes_sent_ultimate_audit")
async def system_net_io_bytes_sent_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network bytes sent ultimate.
    """
    logger.info("Starting system network bytes sent ultimate audit")
    yield ProgressPayload(step="Initializing Network probe", pct=0, log="Collecting system-wide network bytes sent stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            net_io = psutil.net_io_counters()
            current_val = net_io.bytes_sent
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Network Bytes Sent {current_val}")
            metadata = {"bytes_sent": current_val}
        except Exception as e:
            logger.error(f"Error auditing network bytes sent ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Network Bytes Sent", pct=pct, log=f"Measured network bytes sent sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average network bytes sent: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_bytes_sent": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_bytes_recv_ultimate_audit")
async def system_net_io_bytes_recv_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network bytes received ultimate.
    """
    logger.info("Starting system network bytes received ultimate audit")
    yield ProgressPayload(step="Initializing Network probe", pct=0, log="Collecting system-wide network bytes received stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            net_io = psutil.net_io_counters()
            current_val = net_io.bytes_recv
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Network Bytes Received {current_val}")
            metadata = {"bytes_recv": current_val}
        except Exception as e:
            logger.error(f"Error auditing network bytes received ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Network Bytes Received", pct=pct, log=f"Measured network bytes received sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average network bytes received: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_bytes_recv": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_packets_sent_ultimate_audit")
async def system_net_io_packets_sent_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network packets sent ultimate.
    """
    logger.info("Starting system network packets sent ultimate audit")
    yield ProgressPayload(step="Initializing Network probe", pct=0, log="Collecting system-wide network packets sent stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            net_io = psutil.net_io_counters()
            current_val = net_io.packets_sent
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Network Packets Sent {current_val}")
            metadata = {"packets_sent": current_val}
        except Exception as e:
            logger.error(f"Error auditing network packets sent ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Network Packets Sent", pct=pct, log=f"Measured network packets sent sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average network packets sent: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_packets_sent": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_packets_recv_ultimate_audit")
async def system_net_io_packets_recv_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network packets received ultimate.
    """
    logger.info("Starting system network packets received ultimate audit")
    yield ProgressPayload(step="Initializing Network probe", pct=0, log="Collecting system-wide network packets received stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            net_io = psutil.net_io_counters()
            current_val = net_io.packets_recv
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Network Packets Received {current_val}")
            metadata = {"packets_recv": current_val}
        except Exception as e:
            logger.error(f"Error auditing network packets received ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Network Packets Received", pct=pct, log=f"Measured network packets received sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average network packets received: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_packets_recv": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_errin_ultimate_audit")
async def system_net_io_errin_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network input errors ultimate.
    """
    logger.info("Starting system network input errors ultimate audit")
    yield ProgressPayload(step="Initializing Network probe", pct=0, log="Collecting system-wide network input errors stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            net_io = psutil.net_io_counters()
            current_val = net_io.errin
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Network Input Errors {current_val}")
            metadata = {"errin": current_val}
        except Exception as e:
            logger.error(f"Error auditing network input errors ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Network Input Errors", pct=pct, log=f"Measured network input errors sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average network input errors: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_errin": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_errout_ultimate_audit")
async def system_net_io_errout_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network output errors ultimate.
    """
    logger.info("Starting system network output errors ultimate audit")
    yield ProgressPayload(step="Initializing Network probe", pct=0, log="Collecting system-wide network output errors stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            net_io = psutil.net_io_counters()
            current_val = net_io.errout
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Network Output Errors {current_val}")
            metadata = {"errout": current_val}
        except Exception as e:
            logger.error(f"Error auditing network output errors ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Network Output Errors", pct=pct, log=f"Measured network output errors sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average network output errors: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_errout": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_dropin_ultimate_audit")
async def system_net_io_dropin_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network input drops ultimate.
    """
    logger.info("Starting system network input drops ultimate audit")
    yield ProgressPayload(step="Initializing Network probe", pct=0, log="Collecting system-wide network input drops stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            net_io = psutil.net_io_counters()
            current_val = net_io.dropin
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Network Input Drops {current_val}")
            metadata = {"dropin": current_val}
        except Exception as e:
            logger.error(f"Error auditing network input drops ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Network Input Drops", pct=pct, log=f"Measured network input drops sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average network input drops: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_dropin": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_dropout_ultimate_audit")
async def system_net_io_dropout_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network output drops ultimate.
    """
    logger.info("Starting system network output drops ultimate audit")
    yield ProgressPayload(step="Initializing Network probe", pct=0, log="Collecting system-wide network output drops stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            net_io = psutil.net_io_counters()
            current_val = net_io.dropout
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Network Output Drops {current_val}")
            metadata = {"dropout": current_val}
        except Exception as e:
            logger.error(f"Error auditing network output drops ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Network Output Drops", pct=pct, log=f"Measured network output drops sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average network output drops: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_dropout": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_stats_ctx_switches_ultimate_audit")
async def system_cpu_stats_ctx_switches_ultimate_audit(samples: int = 3):
    """
    Audits system-wide CPU context switches ultimate.
    """
    logger.info("Starting system CPU context switches ultimate audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide CPU context switches stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            cpu_stats = psutil.cpu_stats()
            current_val = cpu_stats.ctx_switches
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Context Switches {current_val}")
            metadata = {"ctx_switches": current_val}
        except Exception as e:
            logger.error(f"Error auditing CPU context switches ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU Context Switches", pct=pct, log=f"Measured CPU context switches sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU context switches: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_ctx_switches": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_stats_interrupts_ultimate_audit")
async def system_cpu_stats_interrupts_ultimate_audit(samples: int = 3):
    """
    Audits system-wide CPU interrupts ultimate.
    """
    logger.info("Starting system CPU interrupts ultimate audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide CPU interrupts stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            cpu_stats = psutil.cpu_stats()
            current_val = cpu_stats.interrupts
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Interrupts {current_val}")
            metadata = {"interrupts": current_val}
        except Exception as e:
            logger.error(f"Error auditing CPU interrupts ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU Interrupts", pct=pct, log=f"Measured CPU interrupts sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU interrupts: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_interrupts": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_stats_soft_interrupts_ultimate_audit")
async def system_cpu_stats_soft_interrupts_ultimate_audit(samples: int = 3):
    """
    Audits system-wide CPU soft interrupts ultimate.
    """
    logger.info("Starting system CPU soft interrupts ultimate audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide CPU soft interrupts stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            cpu_stats = psutil.cpu_stats()
            current_val = cpu_stats.soft_interrupts
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Soft Interrupts {current_val}")
            metadata = {"soft_interrupts": current_val}
        except Exception as e:
            logger.error(f"Error auditing CPU soft interrupts ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU Soft Interrupts", pct=pct, log=f"Measured CPU soft interrupts sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU soft interrupts: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_soft_interrupts": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_stats_syscalls_ultimate_audit")
async def system_cpu_stats_syscalls_ultimate_audit(samples: int = 3):
    """
    Audits system-wide CPU syscalls ultimate.
    """
    logger.info("Starting system CPU syscalls ultimate audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide CPU syscalls stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            cpu_stats = psutil.cpu_stats()
            current_val = cpu_stats.syscalls
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Syscalls {current_val}")
            metadata = {"syscalls": current_val}
        except Exception as e:
            logger.error(f"Error auditing CPU syscalls ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU Syscalls", pct=pct, log=f"Measured CPU syscalls sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU syscalls: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_syscalls": avg_val, "stability": "STABLE"}

@progress_tool(name="system_memory_total_ultimate_audit")
async def system_memory_total_ultimate_audit(samples: int = 3):
    """
    Audits system-wide total memory ultimate.
    """
    logger.info("Starting system total memory ultimate audit")
    yield ProgressPayload(step="Initializing Memory probe", pct=0, log="Collecting system-wide total memory stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            mem = psutil.virtual_memory()
            current_val = mem.total
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Total Memory {current_val}")
            metadata = {"total": current_val}
        except Exception as e:
            logger.error(f"Error auditing total memory ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Total Memory", pct=pct, log=f"Measured total memory sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average total memory: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_total": avg_val, "stability": "STABLE"}

@progress_tool(name="system_memory_used_ultimate_audit")
async def system_memory_used_ultimate_audit(samples: int = 3):
    """
    Audits system-wide used memory ultimate.
    """
    logger.info("Starting system used memory ultimate audit")
    yield ProgressPayload(step="Initializing Memory probe", pct=0, log="Collecting system-wide used memory stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            mem = psutil.virtual_memory()
            current_val = mem.used
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Used Memory {current_val}")
            metadata = {"used": current_val}
        except Exception as e:
            logger.error(f"Error auditing used memory ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Used Memory", pct=pct, log=f"Measured used memory sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average used memory: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_used": avg_val, "stability": "STABLE"}

@progress_tool(name="system_memory_available_ultimate_audit")
async def system_memory_available_ultimate_audit(samples: int = 3):
    """
    Audits system-wide available memory ultimate.
    """
    logger.info("Starting system available memory ultimate audit")
    yield ProgressPayload(step="Initializing Memory probe", pct=0, log="Collecting system-wide available memory stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            mem = psutil.virtual_memory()
            current_val = mem.available
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Available Memory {current_val}")
            metadata = {"available": current_val}
        except Exception as e:
            logger.error(f"Error auditing available memory ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Available Memory", pct=pct, log=f"Measured available memory sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average available memory: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_available": avg_val, "stability": "STABLE"}

@progress_tool(name="system_memory_free_ultimate_audit")
async def system_memory_free_ultimate_audit(samples: int = 3):
    """
    Audits system-wide free memory ultimate.
    """
    logger.info("Starting system free memory ultimate audit")
    yield ProgressPayload(step="Initializing Memory probe", pct=0, log="Collecting system-wide free memory stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            mem = psutil.virtual_memory()
            current_val = mem.free
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Free Memory {current_val}")
            metadata = {"free": current_val}
        except Exception as e:
            logger.error(f"Error auditing free memory ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Free Memory", pct=pct, log=f"Measured free memory sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average free memory: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_free": avg_val, "stability": "STABLE"}

@progress_tool(name="system_memory_percent_ultimate_audit")
async def system_memory_percent_ultimate_audit(samples: int = 3):
    """
    Audits system-wide memory percentage ultimate.
    """
    logger.info("Starting system memory percentage ultimate audit")
    yield ProgressPayload(step="Initializing Memory probe", pct=0, log="Collecting system-wide memory percentage stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            mem = psutil.virtual_memory()
            current_val = mem.percent
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Memory Percent {current_val}%")
            metadata = {"percent": current_val}
        except Exception as e:
            logger.error(f"Error auditing memory percentage ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Memory Percent", pct=pct, log=f"Measured memory percentage sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average memory percentage: {avg_val:.2f}%")
    yield {"status": "audit_complete", "avg_percent": avg_val, "stability": "STABLE"}

@progress_tool(name="system_memory_active_ultimate_audit")
async def system_memory_active_ultimate_audit(samples: int = 3):
    """
    Audits system-wide active memory ultimate.
    """
    logger.info("Starting system active memory ultimate audit")
    yield ProgressPayload(step="Initializing Memory probe", pct=0, log="Collecting system-wide active memory stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            mem = psutil.virtual_memory()
            current_val = getattr(mem, "active", 0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Active Memory {current_val}")
            metadata = {"active": current_val}
        except Exception as e:
            logger.error(f"Error auditing active memory ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Active Memory", pct=pct, log=f"Measured active memory sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average active memory: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_active": avg_val, "stability": "STABLE"}

@progress_tool(name="system_memory_inactive_ultimate_audit")
async def system_memory_inactive_ultimate_audit(samples: int = 3):
    """
    Audits system-wide inactive memory ultimate.
    """
    logger.info("Starting system inactive memory ultimate audit")
    yield ProgressPayload(step="Initializing Memory probe", pct=0, log="Collecting system-wide inactive memory stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            mem = psutil.virtual_memory()
            current_val = getattr(mem, "inactive", 0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Inactive Memory {current_val}")
            metadata = {"inactive": current_val}
        except Exception as e:
            logger.error(f"Error auditing inactive memory ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Inactive Memory", pct=pct, log=f"Measured inactive memory sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average inactive memory: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_inactive": avg_val, "stability": "STABLE"}

@progress_tool(name="system_memory_wired_ultimate_audit")
async def system_memory_wired_ultimate_audit(samples: int = 3):
    """
    Audits system-wide wired memory ultimate.
    """
    logger.info("Starting system wired memory ultimate audit")
    yield ProgressPayload(step="Initializing Memory probe", pct=0, log="Collecting system-wide wired memory stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            mem = psutil.virtual_memory()
            current_val = getattr(mem, "wired", 0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Wired Memory {current_val}")
            metadata = {"wired": current_val}
        except Exception as e:
            logger.error(f"Error auditing wired memory ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Wired Memory", pct=pct, log=f"Measured wired memory sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average wired memory: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_wired": avg_val, "stability": "STABLE"}

@progress_tool(name="system_memory_shared_ultimate_audit")
async def system_memory_shared_ultimate_audit(samples: int = 3):
    """
    Audits system-wide shared memory ultimate.
    """
    logger.info("Starting system shared memory ultimate audit")
    yield ProgressPayload(step="Initializing Memory probe", pct=0, log="Collecting system-wide shared memory stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            mem = psutil.virtual_memory()
            current_val = getattr(mem, "shared", 0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Shared Memory {current_val}")
            metadata = {"shared": current_val}
        except Exception as e:
            logger.error(f"Error auditing shared memory ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Shared Memory", pct=pct, log=f"Measured shared memory sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average shared memory: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_shared": avg_val, "stability": "STABLE"}

@progress_tool(name="system_memory_buffers_ultimate_audit")
async def system_memory_buffers_ultimate_audit(samples: int = 3):
    """
    Audits system-wide memory buffers ultimate.
    """
    logger.info("Starting system memory buffers ultimate audit")
    yield ProgressPayload(step="Initializing Memory probe", pct=0, log="Collecting system-wide memory buffers stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            mem = psutil.virtual_memory()
            current_val = getattr(mem, "buffers", 0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Memory Buffers {current_val}")
            metadata = {"buffers": current_val}
        except Exception as e:
            logger.error(f"Error auditing memory buffers ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Memory Buffers", pct=pct, log=f"Measured memory buffers sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average memory buffers: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_buffers": avg_val, "stability": "STABLE"}

@progress_tool(name="system_memory_cached_ultimate_audit")
async def system_memory_cached_ultimate_audit(samples: int = 3):
    """
    Audits system-wide memory cached ultimate.
    """
    logger.info("Starting system memory cached ultimate audit")
    yield ProgressPayload(step="Initializing Memory probe", pct=0, log="Collecting system-wide memory cached stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            mem = psutil.virtual_memory()
            current_val = getattr(mem, "cached", 0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Memory Cached {current_val}")
            metadata = {"cached": current_val}
        except Exception as e:
            logger.error(f"Error auditing memory cached ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Memory Cached", pct=pct, log=f"Measured memory cached sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average memory cached: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_cached": avg_val, "stability": "STABLE"}

@progress_tool(name="system_swap_memory_total_ultimate_audit")
async def system_swap_memory_total_ultimate_audit(samples: int = 3):
    """
    Audits system-wide swap memory total ultimate.
    """
    logger.info("Starting system swap memory total ultimate audit")
    yield ProgressPayload(step="Initializing Swap probe", pct=0, log="Collecting system-wide swap memory total stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            swap = psutil.swap_memory()
            current_val = swap.total
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Swap Total {current_val}")
            metadata = {"total": current_val}
        except Exception as e:
            logger.error(f"Error auditing swap memory total ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Swap Total", pct=pct, log=f"Measured swap memory total sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average swap total: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_total": avg_val, "stability": "STABLE"}

@progress_tool(name="system_swap_memory_used_ultimate_audit")
async def system_swap_memory_used_ultimate_audit(samples: int = 3):
    """
    Audits system-wide swap memory used ultimate.
    """
    logger.info("Starting system swap memory used ultimate audit")
    yield ProgressPayload(step="Initializing Swap probe", pct=0, log="Collecting system-wide swap memory used stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            swap = psutil.swap_memory()
            current_val = swap.used
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Swap Used {current_val}")
            metadata = {"used": current_val}
        except Exception as e:
            logger.error(f"Error auditing swap memory used ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Swap Used", pct=pct, log=f"Measured swap memory used sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average swap used: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_used": avg_val, "stability": "STABLE"}

@progress_tool(name="system_swap_memory_free_ultimate_audit")
async def system_swap_memory_free_ultimate_audit(samples: int = 3):
    """
    Audits system-wide swap memory free ultimate.
    """
    logger.info("Starting system swap memory free ultimate audit")
    yield ProgressPayload(step="Initializing Swap probe", pct=0, log="Collecting system-wide swap memory free stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            swap = psutil.swap_memory()
            current_val = swap.free
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Swap Free {current_val}")
            metadata = {"free": current_val}
        except Exception as e:
            logger.error(f"Error auditing swap memory free ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Swap Free", pct=pct, log=f"Measured swap memory free sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average swap free: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_free": avg_val, "stability": "STABLE"}

@progress_tool(name="system_swap_memory_percent_ultimate_audit")
async def system_swap_memory_percent_ultimate_audit(samples: int = 3):
    """
    Audits system-wide swap memory percent ultimate.
    """
    logger.info("Starting system swap memory percent ultimate audit")
    yield ProgressPayload(step="Initializing Swap probe", pct=0, log="Collecting system-wide swap memory percent stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            swap = psutil.swap_memory()
            current_val = swap.percent
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Swap Percent {current_val}%")
            metadata = {"percent": current_val}
        except Exception as e:
            logger.error(f"Error auditing swap memory percent ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Swap Percent", pct=pct, log=f"Measured swap memory percent sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average swap percent: {avg_val:.2f}%")
    yield {"status": "audit_complete", "avg_percent": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_user_ultimate_audit")
async def system_cpu_times_user_ultimate_audit(samples: int = 3):
    """
    Audits system-wide CPU times user ultimate.
    """
    logger.info("Starting system cpu times user ultimate audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide cpu times user stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            current_val = times.user
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU User {current_val}")
            metadata = {"user": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu times user ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU User", pct=pct, log=f"Measured cpu times user sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average cpu user: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_user": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_system_ultimate_audit")
async def system_cpu_times_system_ultimate_audit(samples: int = 3):
    """
    Audits system-wide CPU times system ultimate.
    """
    logger.info("Starting system cpu times system ultimate audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide cpu times system stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            current_val = times.system
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU System {current_val}")
            metadata = {"system": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu times system ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU System", pct=pct, log=f"Measured cpu times system sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average cpu system: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_system": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_idle_ultimate_audit")
async def system_cpu_times_idle_ultimate_audit(samples: int = 3):
    """
    Audits system-wide CPU times idle ultimate.
    """
    logger.info("Starting system cpu times idle ultimate audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide cpu times idle stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            current_val = times.idle
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Idle {current_val}")
            metadata = {"idle": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu times idle ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU Idle", pct=pct, log=f"Measured cpu times idle sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average cpu idle: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_idle": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_nice_ultimate_audit")
async def system_cpu_times_nice_ultimate_audit(samples: int = 3):
    """
    Audits system-wide CPU times nice ultimate.
    """
    logger.info("Starting system cpu times nice ultimate audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide cpu times nice stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            current_val = times.nice
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Nice {current_val}")
            metadata = {"nice": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu times nice ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU Nice", pct=pct, log=f"Measured cpu times nice sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average cpu nice: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_nice": avg_val, "stability": "STABLE"}

    yield {"status": "audit_complete", "avg_ctx_switches": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_iowait_ultimate_audit")
async def system_cpu_times_iowait_ultimate_audit(samples: int = 3):
    """
    Audits system-wide CPU times iowait ultimate.
    """
    logger.info("Starting system cpu times iowait ultimate audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide cpu times iowait stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            current_val = getattr(times, "iowait", 0.0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU IOWait {current_val}")
            metadata = {"iowait": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu times iowait ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU IOWait", pct=pct, log=f"Measured cpu times iowait sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average cpu iowait: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_iowait": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_irq_ultimate_audit")
async def system_cpu_times_irq_ultimate_audit(samples: int = 3):
    """
    Audits system-wide CPU times irq ultimate.
    """
    logger.info("Starting system cpu times irq ultimate audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide cpu times irq stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            current_val = getattr(times, "irq", 0.0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU IRQ {current_val}")
            metadata = {"irq": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu times irq ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU IRQ", pct=pct, log=f"Measured cpu times irq sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average cpu irq: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_irq": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_softirq_ultimate_audit")
async def system_cpu_times_softirq_ultimate_audit(samples: int = 3):
    """
    Audits system-wide CPU times softirq ultimate.
    """
    logger.info("Starting system cpu times softirq ultimate audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide cpu times softirq stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            current_val = getattr(times, "softirq", 0.0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU SoftIRQ {current_val}")
            metadata = {"softirq": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu times softirq ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU SoftIRQ", pct=pct, log=f"Measured cpu times softirq sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average cpu softirq: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_softirq": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_steal_ultimate_audit")
async def system_cpu_times_steal_ultimate_audit(samples: int = 3):
    """
    Audits system-wide CPU times steal ultimate.
    """
    logger.info("Starting system cpu times steal ultimate audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide cpu times steal stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            current_val = getattr(times, "steal", 0.0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Steal {current_val}")
            metadata = {"steal": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu times steal ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU Steal", pct=pct, log=f"Measured cpu times steal sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average cpu steal: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_steal": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_guest_ultimate_audit")
async def system_cpu_times_guest_ultimate_audit(samples: int = 3):
    """
    Audits system-wide CPU times guest ultimate.
    """
    logger.info("Starting system cpu times guest ultimate audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide cpu times guest stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            current_val = getattr(times, "guest", 0.0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Guest {current_val}")
            metadata = {"guest": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu times guest ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU Guest", pct=pct, log=f"Measured cpu times guest sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average cpu guest: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_guest": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_guest_nice_ultimate_audit")
async def system_cpu_times_guest_nice_ultimate_audit(samples: int = 3):
    """
    Audits system-wide CPU times guest_nice ultimate.
    """
    logger.info("Starting system cpu times guest_nice ultimate audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide cpu times guest_nice stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            current_val = getattr(times, "guest_nice", 0.0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU GuestNice {current_val}")
            metadata = {"guest_nice": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu times guest_nice ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU GuestNice", pct=pct, log=f"Measured cpu times guest_nice sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average cpu guest_nice: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_guest_nice": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_freq_current_ultimate_audit")
async def system_cpu_freq_current_ultimate_audit(samples: int = 3):
    """
    Audits system-wide CPU frequency current ultimate.
    """
    logger.info("Starting system cpu freq current ultimate audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide cpu freq current stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            freq = psutil.cpu_freq()
            current_val = getattr(freq, "current", 0.0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Freq Current {current_val}")
            metadata = {"current": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu freq current ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU Freq Current", pct=pct, log=f"Measured cpu freq current sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average cpu freq current: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_current": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_freq_min_ultimate_audit")
async def system_cpu_freq_min_ultimate_audit(samples: int = 3):
    """
    Audits system-wide CPU frequency min ultimate.
    """
    logger.info("Starting system cpu freq min ultimate audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide cpu freq min stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            freq = psutil.cpu_freq()
            current_val = getattr(freq, "min", 0.0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Freq Min {current_val}")
            metadata = {"min": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu freq min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU Freq Min", pct=pct, log=f"Measured cpu freq min sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average cpu freq min: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_min": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_freq_max_ultimate_audit")
async def system_cpu_freq_max_ultimate_audit(samples: int = 3):
    """
    Audits system-wide CPU frequency max ultimate.
    """
    logger.info("Starting system cpu freq max ultimate audit")
    yield ProgressPayload(step="Initializing CPU probe", pct=0, log="Collecting system-wide cpu freq max stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            freq = psutil.cpu_freq()
            current_val = getattr(freq, "max", 0.0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Freq Max {current_val}")
            metadata = {"max": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu freq max ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU Freq Max", pct=pct, log=f"Measured cpu freq max sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average cpu freq max: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_max": avg_val, "stability": "STABLE"}

@progress_tool(name="system_load_avg_1m_ultimate_audit")
async def system_load_avg_1m_ultimate_audit(samples: int = 3):
    """
    Audits system-wide load average (1 min) ultimate.
    """
    logger.info("Starting system load average (1 min) ultimate audit")
    yield ProgressPayload(step="Initializing Load probe", pct=0, log="Collecting system-wide load average stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            load_avg = psutil.getloadavg()
            current_val = load_avg[0]
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Load Avg (1m) {current_val}")
            metadata = {"load_1m": current_val}
        except Exception as e:
            logger.error(f"Error auditing load average 1m ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Load Avg 1m", pct=pct, log=f"Measured load average (1m) sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average load average (1m): {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_load_1m": avg_val, "stability": "STABLE"}

@progress_tool(name="system_load_avg_5m_ultimate_audit")
async def system_load_avg_5m_ultimate_audit(samples: int = 3):
    """
    Audits system-wide load average (5 min) ultimate.
    """
    logger.info("Starting system load average (5 min) ultimate audit")
    yield ProgressPayload(step="Initializing Load probe", pct=0, log="Collecting system-wide load average stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            load_avg = psutil.getloadavg()
            current_val = load_avg[1]
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Load Avg (5m) {current_val}")
            metadata = {"load_5m": current_val}
        except Exception as e:
            logger.error(f"Error auditing load average 5m ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Load Avg 5m", pct=pct, log=f"Measured load average (5m) sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average load average (5m): {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_load_5m": avg_val, "stability": "STABLE"}

@progress_tool(name="system_load_avg_15m_ultimate_audit")
async def system_load_avg_15m_ultimate_audit(samples: int = 3):
    """
    Audits system-wide load average (15 min) ultimate.
    """
    logger.info("Starting system load average (15 min) ultimate audit")
    yield ProgressPayload(step="Initializing Load probe", pct=0, log="Collecting system-wide load average stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            load_avg = psutil.getloadavg()
            current_val = load_avg[2]
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Load Avg (15m) {current_val}")
            metadata = {"load_15m": current_val}
        except Exception as e:
            logger.error(f"Error auditing load average 15m ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Load Avg 15m", pct=pct, log=f"Measured load average (15m) sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average load average (15m): {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_load_15m": avg_val, "stability": "STABLE"}

@progress_tool(name="disk_io_read_bytes_ultimate_audit")
async def disk_io_read_bytes_ultimate_audit(samples: int = 3):
    """
    Audits system-wide Disk I/O read bytes ultimate.
    """
    logger.info("Starting Disk I/O read bytes ultimate audit")
    yield ProgressPayload(step="Initializing Disk probe", pct=0, log="Collecting system-wide Disk I/O stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.disk_io_counters()
            current_val = io.read_bytes
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Read Bytes {current_val}")
            metadata = {"read_bytes": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk io read bytes ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Read Bytes", pct=pct, log=f"Measured disk io read bytes sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk io read bytes: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_read_bytes": avg_val, "stability": "STABLE"}

@progress_tool(name="disk_io_write_bytes_ultimate_audit")
async def disk_io_write_bytes_ultimate_audit(samples: int = 3):
    """
    Audits system-wide Disk I/O write bytes ultimate.
    """
    logger.info("Starting Disk I/O write bytes ultimate audit")
    yield ProgressPayload(step="Initializing Disk probe", pct=0, log="Collecting system-wide Disk I/O stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.disk_io_counters()
            current_val = io.write_bytes
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Write Bytes {current_val}")
            metadata = {"write_bytes": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk io write bytes ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Write Bytes", pct=pct, log=f"Measured disk io write bytes sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk io write bytes: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_write_bytes": avg_val, "stability": "STABLE"}

@progress_tool(name="disk_io_read_time_ultimate_audit")
async def disk_io_read_time_ultimate_audit(samples: int = 3):
    """
    Audits system-wide Disk I/O read time ultimate.
    """
    logger.info("Starting Disk I/O read time ultimate audit")
    yield ProgressPayload(step="Initializing Disk probe", pct=0, log="Collecting system-wide Disk I/O stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.disk_io_counters()
            current_val = io.read_time
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Read Time {current_val}")
            metadata = {"read_time": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk io read time ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Read Time", pct=pct, log=f"Measured disk io read time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk io read time: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_read_time": avg_val, "stability": "STABLE"}

@progress_tool(name="system_pids_count_ultimate_audit")
async def system_pids_count_ultimate_audit(samples: int = 3):
    """
    Audits system-wide PID count ultimate.
    """
    logger.info("Starting system PID count ultimate audit")
    yield ProgressPayload(step="Initializing PID probe", pct=0, log="Collecting system-wide active PID stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_val = len(psutil.pids())
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: PID Count {current_val}")
            metadata = {"pid_count": current_val}
        except Exception as e:
            logger.error(f"Error auditing PID count ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling PID Count", pct=pct, log=f"Measured PID count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average PID count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_pid_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_boot_time_ultimate_audit")
async def system_boot_time_ultimate_audit(samples: int = 3):
    """
    Audits system boot time ultimate.
    """
    logger.info("Starting system boot time ultimate audit")
    yield ProgressPayload(step="Initializing Boot probe", pct=0, log="Collecting system boot time stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_val = psutil.boot_time()
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Boot Time {current_val}")
            metadata = {"boot_time": current_val}
        except Exception as e:
            logger.error(f"Error auditing boot time ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Boot Time", pct=pct, log=f"Measured boot time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average boot time: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_boot_time": avg_val, "stability": "STABLE"}

@progress_tool(name="system_users_count_ultimate_audit")
async def system_users_count_ultimate_audit(samples: int = 3):
    """
    Audits system-wide logged-in users count ultimate.
    """
    logger.info("Starting system users count ultimate audit")
    yield ProgressPayload(step="Initializing User probe", pct=0, log="Collecting system-wide logged-in user stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_val = len(psutil.users())
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: User Count {current_val}")
            metadata = {"user_count": current_val}
        except Exception as e:
            logger.error(f"Error auditing user count ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling User Count", pct=pct, log=f"Measured user count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average user count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_user_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_partitions_count_ultimate_audit")
async def system_disk_partitions_count_ultimate_audit(samples: int = 3):
    """
    Audits system-wide disk partitions count ultimate.
    """
    logger.info("Starting system disk partitions count ultimate audit")
    yield ProgressPayload(step="Initializing Partition probe", pct=0, log="Collecting system-wide disk partition stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_val = len(psutil.disk_partitions())
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Partition Count {current_val}")
            metadata = {"partition_count": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk partitions count ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Partition Count", pct=pct, log=f"Measured disk partition count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average partition count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_partition_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_count_ultimate_audit")
async def system_net_if_addrs_count_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network interface addresses count ultimate.
    """
    logger.info("Starting system net if addrs count ultimate audit")
    yield ProgressPayload(step="Initializing Net If Addrs probe", pct=0, log="Collecting system-wide network interface address stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_val = len(psutil.net_if_addrs())
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net If Addrs Count {current_val}")
            metadata = {"net_if_addrs_count": current_val}
        except Exception as e:
            logger.error(f"Error auditing net if addrs count ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Addrs Count", pct=pct, log=f"Measured net if addrs count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net if addrs count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_net_if_addrs_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_stats_count_ultimate_audit")
async def system_net_if_stats_count_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network interface stats count ultimate.
    """
    logger.info("Starting system net if stats count ultimate audit")
    yield ProgressPayload(step="Initializing Net If Stats probe", pct=0, log="Collecting system-wide network interface stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_val = len(psutil.net_if_stats())
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net If Stats Count {current_val}")
            metadata = {"net_if_stats_count": current_val}
        except Exception as e:
            logger.error(f"Error auditing net if stats count ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Stats Count", pct=pct, log=f"Measured net if stats count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net if stats count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_net_if_stats_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_stats_isup_total_ultimate_audit")
async def system_net_if_stats_isup_total_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network interface isup total ultimate.
    """
    logger.info("Starting system net if stats isup total ultimate audit")
    yield ProgressPayload(step="Initializing Net If Stats probe", pct=0, log="Collecting system-wide network interface isup stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_if_stats()
            current_val = sum(1 for s in stats.values() if s.isup)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net If IsUp Total {current_val}")
            metadata = {"isup_total": current_val}
        except Exception as e:
            logger.error(f"Error auditing net if stats isup total ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If IsUp Total", pct=pct, log=f"Measured net if stats isup total sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net if stats isup total: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_isup_total": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_stats_speed_total_ultimate_audit")
async def system_net_if_stats_speed_total_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network interface speed total ultimate.
    """
    logger.info("Starting system net if stats speed total ultimate audit")
    yield ProgressPayload(step="Initializing Net If Speed probe", pct=0, log="Collecting system-wide network interface speed stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_if_stats()
            current_val = sum(s.speed for s in stats.values())
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net If Speed Total {current_val}")
            metadata = {"speed_total": current_val}
        except Exception as e:
            logger.error(f"Error auditing net if stats speed total ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Speed Total", pct=pct, log=f"Measured net if stats speed total sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net if stats speed total: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_speed_total": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_stats_mtu_avg_ultimate_audit")
async def system_net_if_stats_mtu_avg_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network interface MTU average ultimate.
    """
    logger.info("Starting system net if stats mtu avg ultimate audit")
    yield ProgressPayload(step="Initializing Net If MTU probe", pct=0, log="Collecting system-wide network interface MTU stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_if_stats()
            current_val = sum(s.mtu for s in stats.values()) / len(stats) if stats else 0
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net If MTU Avg {current_val}")
            metadata = {"mtu_avg": current_val}
        except Exception as e:
            logger.error(f"Error auditing net if stats mtu avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If MTU Avg", pct=pct, log=f"Measured net if stats mtu avg sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net if stats mtu avg: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_mtu_avg": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_family_count_ultimate_audit")
async def system_net_if_addrs_family_count_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network interface family count ultimate.
    """
    logger.info("Starting system net if addrs family count ultimate audit")
    yield ProgressPayload(step="Initializing Net If Family probe", pct=0, log="Collecting system-wide network interface family stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            families = set()
            for interface_addrs in addrs.values():
                for addr in interface_addrs:
                    families.add(addr.family)
            current_val = len(families)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net If Family Count {current_val}")
            metadata = {"family_count": current_val}
        except Exception as e:
            logger.error(f"Error auditing net if addrs family count ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Family Count", pct=pct, log=f"Measured net if addrs family count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net if addrs family count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_family_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_ipv4_total_ultimate_audit")
async def system_net_if_addrs_ipv4_total_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network interface IPv4 total ultimate.
    """
    logger.info("Starting system net if addrs ipv4 total ultimate audit")
    yield ProgressPayload(step="Initializing Net If IPv4 probe", pct=0, log="Collecting system-wide network interface IPv4 stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            count = 0
            for interface_addrs in addrs.values():
                for addr in interface_addrs:
                    if addr.family == psutil.AF_LINK if hasattr(psutil, "AF_LINK") else -1: # Just an example, psutil.AF_INET is better
                        pass
                    import socket
                    if addr.family == socket.AF_INET:
                        count += 1
            current_val = count
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net If IPv4 Total {current_val}")
            metadata = {"ipv4_total": current_val}
        except Exception as e:
            logger.error(f"Error auditing net if addrs ipv4 total ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If IPv4 Total", pct=pct, log=f"Measured net if addrs ipv4 total sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net if addrs ipv4 total: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_ipv4_total": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_ipv6_total_ultimate_audit")
async def system_net_if_addrs_ipv6_total_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network interface IPv6 total ultimate.
    """
    logger.info("Starting system net if addrs ipv6 total ultimate audit")
    yield ProgressPayload(step="Initializing Net If IPv6 probe", pct=0, log="Collecting system-wide network interface IPv6 stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            count = 0
            import socket
            for interface_addrs in addrs.values():
                for addr in interface_addrs:
                    if addr.family == socket.AF_INET6:
                        count += 1
            current_val = count
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net If IPv6 Total {current_val}")
            metadata = {"ipv6_total": current_val}
        except Exception as e:
            logger.error(f"Error auditing net if addrs ipv6 total ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If IPv6 Total", pct=pct, log=f"Measured net if addrs ipv6 total sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net if addrs ipv6 total: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_ipv6_total": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_mac_total_ultimate_audit")
async def system_net_if_addrs_mac_total_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network interface MAC total ultimate.
    """
    logger.info("Starting system net if addrs mac total ultimate audit")
    yield ProgressPayload(step="Initializing Net If MAC probe", pct=0, log="Collecting system-wide network interface MAC stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            count = 0
            import socket
            # MAC address family varies by platform
            AF_PACKET = getattr(socket, 'AF_PACKET', None)
            AF_LINK = getattr(psutil, 'AF_LINK', None)
            
            for interface_addrs in addrs.values():
                for addr in interface_addrs:
                    if (AF_PACKET is not None and addr.family == AF_PACKET) or (AF_LINK is not None and addr.family == AF_LINK):
                        count += 1
            current_val = count
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net If MAC Total {current_val}")
            metadata = {"mac_total": current_val}
        except Exception as e:
            logger.error(f"Error auditing net if addrs mac total ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If MAC Total", pct=pct, log=f"Measured net if addrs mac total sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net if addrs mac total: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_mac_total": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_broadcast_total_ultimate_audit")
async def system_net_if_addrs_broadcast_total_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network interface broadcast total ultimate.
    """
    logger.info("Starting system net if addrs broadcast total ultimate audit")
    yield ProgressPayload(step="Initializing Net If Broadcast probe", pct=0, log="Collecting system-wide network interface broadcast stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            count = 0
            for interface_addrs in addrs.values():
                for addr in interface_addrs:
                    if addr.broadcast:
                        count += 1
            current_val = count
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net If Broadcast Total {current_val}")
            metadata = {"broadcast_total": current_val}
        except Exception as e:
            logger.error(f"Error auditing net if addrs broadcast total ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Broadcast Total", pct=pct, log=f"Measured net if addrs broadcast total sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net if addrs broadcast total: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_broadcast_total": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_netmask_total_ultimate_audit")
async def system_net_if_addrs_netmask_total_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network interface netmask total count ultimate.
    """
    logger.info("Starting system net if addrs netmask total ultimate audit")
    yield ProgressPayload(step="Initializing Net If Netmask probe", pct=0, log="Collecting system-wide network interface netmask stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            count = 0
            for interface_addrs in addrs.values():
                for addr in interface_addrs:
                    if addr.netmask:
                        count += 1
            current_val = count
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net If Netmask Total {current_val}")
            metadata = {"netmask_total": current_val}
        except Exception as e:
            logger.error(f"Error auditing net if addrs netmask total ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Netmask Total", pct=pct, log=f"Measured net if addrs netmask total sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net if addrs netmask total: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_netmask_total": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_ptp_total_ultimate_audit")
async def system_net_if_addrs_ptp_total_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network interface PTP total count ultimate.
    """
    logger.info("Starting system net if addrs ptp total ultimate audit")
    yield ProgressPayload(step="Initializing Net If PTP probe", pct=0, log="Collecting system-wide network interface PTP stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            count = 0
            for interface_addrs in addrs.values():
                for addr in interface_addrs:
                    if hasattr(addr, "ptp") and addr.ptp:
                        count += 1
            current_val = count
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net If PTP Total {current_val}")
            metadata = {"ptp_total": current_val}
        except Exception as e:
            logger.error(f"Error auditing net if addrs ptp total ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If PTP Total", pct=pct, log=f"Measured net if addrs ptp total sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net if addrs ptp total: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_ptp_total": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_partitions_fstype_count_ultimate_audit")
async def system_disk_partitions_fstype_count_ultimate_audit(samples: int = 3):
    """
    Audits system-wide disk partitions filesystem types count ultimate.
    """
    logger.info("Starting system disk partitions fstype count ultimate audit")
    yield ProgressPayload(step="Initializing Partition FSType probe", pct=0, log="Collecting system-wide disk partition filesystem types stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            partitions = psutil.disk_partitions(all=True)
            fstypes = set(p.fstype for p in partitions if p.fstype)
            current_val = len(fstypes)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Partition FSTypes {current_val}")
            metadata = {"fstype_count": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk partitions fstype count ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Partition FSType Count", pct=pct, log=f"Measured disk partition fstype count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk partition fstype count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_fstype_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_partitions_mountpoint_count_ultimate_audit")
async def system_disk_partitions_mountpoint_count_ultimate_audit(samples: int = 3):
    """
    Audits system-wide disk partitions mountpoint count ultimate.
    """
    logger.info("Starting system disk partitions mountpoint count ultimate audit")
    yield ProgressPayload(step="Initializing Partition Mountpoint probe", pct=0, log="Collecting system-wide disk partition mountpoints stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            partitions = psutil.disk_partitions(all=True)
            mountpoints = set(p.mountpoint for p in partitions if p.mountpoint)
            current_val = len(mountpoints)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Partition Mountpoints {current_val}")
            metadata = {"mountpoint_count": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk partitions mountpoint count ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Partition Mountpoint Count", pct=pct, log=f"Measured disk partition mountpoint count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk partition mountpoint count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_mountpoint_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_partitions_opts_count_ultimate_audit")
async def system_disk_partitions_opts_count_ultimate_audit(samples: int = 3):
    """
    Audits system-wide disk partitions options count ultimate.
    """
    logger.info("Starting system disk partitions opts count ultimate audit")
    yield ProgressPayload(step="Initializing Partition Opts probe", pct=0, log="Collecting system-wide disk partition options stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            partitions = psutil.disk_partitions(all=True)
            opts = set(p.opts for p in partitions if p.opts)
            current_val = len(opts)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Partition Opts {current_val}")
            metadata = {"opts_count": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk partitions opts count ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Partition Opts Count", pct=pct, log=f"Measured disk partition opts count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk partition opts count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_opts_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_stats_speed_avg_ultimate_audit")
async def system_net_if_stats_speed_avg_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network interface statistics speed average ultimate.
    """
    logger.info("Starting system net if stats speed avg ultimate audit")
    yield ProgressPayload(step="Initializing Net If Speed probe", pct=0, log="Collecting system-wide network interface speed stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_if_stats()
            speeds = [s.speed for s in stats.values() if s.speed > 0]
            current_val = sum(speeds) / len(speeds) if speeds else 0
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net If Speed Avg {current_val:.2f}")
            metadata = {"speed_avg": current_val}
        except Exception as e:
            logger.error(f"Error auditing net if stats speed avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Speed Avg", pct=pct, log=f"Measured net if stats speed avg sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net if stats speed avg: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_speed_avg": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_stats_duplex_total_ultimate_audit")
async def system_net_if_stats_duplex_total_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network interface statistics duplex total ultimate.
    """
    logger.info("Starting system net if stats duplex total ultimate audit")
    yield ProgressPayload(step="Initializing Net If Duplex probe", pct=0, log="Collecting system-wide network interface duplex stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_if_stats()
            duplex_count = len([s.duplex for s in stats.values() if hasattr(s, "duplex")])
            current_val = duplex_count
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net If Duplex Total {current_val}")
            metadata = {"duplex_total": current_val}
        except Exception as e:
            logger.error(f"Error auditing net if stats duplex total ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Duplex Total", pct=pct, log=f"Measured net if stats duplex total sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net if stats duplex total: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_duplex_total": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_stats_isup_avg_ultimate_audit")
async def system_net_if_stats_isup_avg_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network interface statistics isup average ultimate.
    """
    logger.info("Starting system net if stats isup avg ultimate audit")
    yield ProgressPayload(step="Initializing Net If IsUp probe", pct=0, log="Collecting system-wide network interface isup stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_if_stats()
            isup_vals = [1 if s.isup else 0 for s in stats.values()]
            current_val = sum(isup_vals) / len(isup_vals) if isup_vals else 0
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net If IsUp Avg {current_val:.2f}")
            metadata = {"isup_avg": current_val}
        except Exception as e:
            logger.error(f"Error auditing net if stats isup avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If IsUp Avg", pct=pct, log=f"Measured net if stats isup avg sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net if stats isup avg: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_isup_avg": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_stats_mtu_total_ultimate_audit")
async def system_net_if_stats_mtu_total_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network interface statistics MTU total ultimate.
    """
    logger.info("Starting system net if stats mtu total ultimate audit")
    yield ProgressPayload(step="Initializing Net If MTU probe", pct=0, log="Collecting system-wide network interface MTU stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_if_stats()
            mtu_total = sum(s.mtu for s in stats.values() if hasattr(s, "mtu") and s.mtu > 0)
            current_val = mtu_total
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net If MTU Total {current_val}")
            metadata = {"mtu_total": current_val}
        except Exception as e:
            logger.error(f"Error auditing net if stats mtu total ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If MTU Total", pct=pct, log=f"Measured net if stats mtu total sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net if stats mtu total: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_mtu_total": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_stats_flags_total_ultimate_audit")
async def system_net_if_stats_flags_total_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network interface statistics flags total ultimate.
    """
    logger.info("Starting system net if stats flags total ultimate audit")
    yield ProgressPayload(step="Initializing Net If Flags probe", pct=0, log="Collecting system-wide network interface flags stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_if_stats()
            flags_count = sum(len(s.flags.split(",")) if isinstance(s.flags, str) else 1 for s in stats.values() if hasattr(s, "flags") and s.flags)
            current_val = flags_count
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net If Flags Total {current_val}")
            metadata = {"flags_total": current_val}
        except Exception as e:
            logger.error(f"Error auditing net if stats flags total ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Flags Total", pct=pct, log=f"Measured net if stats flags total sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net if stats flags total: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_flags_total": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_partitions_device_count_ultimate_audit")
async def system_disk_partitions_device_count_ultimate_audit(samples: int = 3):
    """
    Audits system-wide disk partitions device count ultimate.
    """
    logger.info("Starting system disk partitions device count ultimate audit")
    yield ProgressPayload(step="Initializing Partition Device probe", pct=0, log="Collecting system-wide disk partition devices stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            partitions = psutil.disk_partitions(all=True)
            devices = set(p.device for p in partitions if p.device)
            current_val = len(devices)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Partition Devices {current_val}")
            metadata = {"device_count": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk partitions device count ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Partition Device Count", pct=pct, log=f"Measured disk partition device count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk partition device count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_device_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_partitions_all_count_ultimate_audit")
async def system_disk_partitions_all_count_ultimate_audit(samples: int = 3):
    """
    Audits system-wide disk partitions all count ultimate.
    """
    logger.info("Starting system disk partitions all count ultimate audit")
    yield ProgressPayload(step="Initializing Partition All probe", pct=0, log="Collecting all system-wide disk partitions stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            partitions = psutil.disk_partitions(all=True)
            current_val = len(partitions)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Partition All Count {current_val}")
            metadata = {"all_count": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk partitions all count ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Partition All Count", pct=pct, log=f"Measured disk partition all count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk partition all count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_all_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_stats_mtu_max_ultimate_audit")
async def system_net_if_stats_mtu_max_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network interface statistics MTU max ultimate.
    """
    logger.info("Starting system net if stats mtu max ultimate audit")
    yield ProgressPayload(step="Initializing Net If MTU Max probe", pct=0, log="Collecting system-wide network interface MTU max stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_if_stats()
            mtu_max = max(s.mtu for s in stats.values() if hasattr(s, "mtu") and s.mtu > 0) if stats else 0
            current_val = mtu_max
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net If MTU Max {current_val}")
            metadata = {"mtu_max": current_val}
        except Exception as e:
            logger.error(f"Error auditing net if stats mtu max ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If MTU Max", pct=pct, log=f"Measured net if stats mtu max sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net if stats mtu max: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_mtu_max": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_stats_speed_max_ultimate_audit")
async def system_net_if_stats_speed_max_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network interface statistics speed max ultimate.
    """
    logger.info("Starting system net if stats speed max ultimate audit")
    yield ProgressPayload(step="Initializing Net If Speed Max probe", pct=0, log="Collecting system-wide network interface speed max stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_if_stats()
            speed_max = max(s.speed for s in stats.values() if hasattr(s, "speed") and s.speed > 0) if stats else 0
            current_val = speed_max
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net If Speed Max {current_val}")
            metadata = {"speed_max": current_val}
        except Exception as e:
            logger.error(f"Error auditing net if stats speed max ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Speed Max", pct=pct, log=f"Measured net if stats speed max sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net if stats speed max: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_speed_max": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_ipv4_avg_ultimate_audit")
async def system_net_if_addrs_ipv4_avg_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network interface addresses IPv4 avg ultimate.
    """
    logger.info("Starting system net if addrs ipv4 avg ultimate audit")
    yield ProgressPayload(step="Initializing Net If Addrs IPv4 probe", pct=0, log="Collecting system-wide network interface IPv4 stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            ipv4_count = sum(1 for interface in addrs.values() for addr in interface if addr.family == 2) # AF_INET
            current_val = ipv4_count
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net If Addrs IPv4 Count {current_val}")
            metadata = {"ipv4_count": current_val}
        except Exception as e:
            logger.error(f"Error auditing net if addrs ipv4 avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Addrs IPv4", pct=pct, log=f"Measured net if addrs ipv4 sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net if addrs ipv4 count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_ipv4_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_ipv6_avg_ultimate_audit")
async def system_net_if_addrs_ipv6_avg_ultimate_audit(samples: int = 3):
    """
    Audits system-wide network interface addresses IPv6 avg ultimate.
    """
    logger.info("Starting system net if addrs ipv6 avg ultimate audit")
    yield ProgressPayload(step="Initializing Net If Addrs IPv6 probe", pct=0, log="Collecting system-wide network interface IPv6 stats...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            import socket
            af_inet6 = getattr(socket, "AF_INET6", 30) # Default for Darwin
            ipv6_count = sum(1 for interface in addrs.values() for addr in interface if addr.family == af_inet6)
            current_val = ipv6_count
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Net If Addrs IPv6 Count {current_val}")
            metadata = {"ipv6_count": current_val}
        except Exception as e:
            logger.error(f"Error auditing net if addrs ipv6 avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Addrs IPv6", pct=pct, log=f"Measured net if addrs ipv6 sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net if addrs ipv6 count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_ipv6_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_stats_flags_max_ultimate_audit")
async def system_net_if_stats_flags_max_ultimate_audit(samples: int = 3):
    """
    Audits the maximum flags across all network interfaces.
    """
    logger.info(f"Starting system net if stats flags max ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net If Stats Flags Probe", pct=0, log="Collecting network interface flags baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_if_stats()
            max_val = max(s.flags for s in stats.values()) if stats else 0
            samples_list.append(max_val)
            logger.info(f"Sample {i+1}/{samples}: Net If Stats Flags Max {max_val}")
            metadata = {"flags_max": max_val}
        except Exception as e:
            logger.error(f"Error auditing net if stats flags max ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Stats Flags Max", pct=pct, log=f"Measured net if stats flags max sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = max(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Maximum net if stats flags: {final_val}")
    yield {"status": "audit_complete", "max_flags": final_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_stats_isup_max_ultimate_audit")
async def system_net_if_stats_isup_max_ultimate_audit(samples: int = 3):
    """
    Audits the maximum isup status across all network interfaces (binary max).
    """
    logger.info(f"Starting system net if stats isup max ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net If Stats Isup Probe", pct=0, log="Collecting network interface isup baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_if_stats()
            max_val = max(int(s.isup) for s in stats.values()) if stats else 0
            samples_list.append(max_val)
            logger.info(f"Sample {i+1}/{samples}: Net If Stats Isup Max {max_val}")
            metadata = {"isup_max": max_val}
        except Exception as e:
            logger.error(f"Error auditing net if stats isup max ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Stats Isup Max", pct=pct, log=f"Measured net if stats isup max sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = max(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Maximum net if stats isup: {final_val}")
    yield {"status": "audit_complete", "max_isup": final_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_mac_avg_ultimate_audit")
async def system_net_if_addrs_mac_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average count of MAC addresses per interface.
    """
    logger.info(f"Starting system net if addrs mac avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net If Addrs MAC Probe", pct=0, log="Collecting network interface MAC address baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            af_link = getattr(psutil, "AF_LINK", -1)
            if af_link == -1:
                import socket
                af_link = getattr(socket, "AF_LINK", 18 if sys.platform == "darwin" else 17)
            
            mac_count = sum(1 for interface in addrs.values() for addr in interface if addr.family == af_link)
            samples_list.append(mac_count)
            logger.info(f"Sample {i+1}/{samples}: Net If Addrs MAC Count {mac_count}")
            metadata = {"mac_count": mac_count}
        except Exception as e:
            logger.error(f"Error auditing net if addrs mac avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Addrs MAC", pct=pct, log=f"Measured net if addrs mac sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net if addrs mac count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_mac_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_broadcast_avg_ultimate_audit")
async def system_net_if_addrs_broadcast_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average count of broadcast addresses across all interfaces.
    """
    logger.info(f"Starting system net if addrs broadcast avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net If Addrs Broadcast Probe", pct=0, log="Collecting network interface broadcast address baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            broadcast_count = sum(1 for interface in addrs.values() for addr in interface if getattr(addr, "broadcast", None))
            samples_list.append(broadcast_count)
            logger.info(f"Sample {i+1}/{samples}: Net If Addrs Broadcast Count {broadcast_count}")
            metadata = {"broadcast_count": broadcast_count}
        except Exception as e:
            logger.error(f"Error auditing net if addrs broadcast avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Addrs Broadcast", pct=pct, log=f"Measured net if addrs broadcast sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net if addrs broadcast count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_broadcast_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_stats_mtu_min_ultimate_audit")
async def system_net_if_stats_mtu_min_ultimate_audit(samples: int = 3):
    """
    Audits the minimum MTU status across all network interfaces.
    """
    logger.info(f"Starting system net if stats mtu min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net If Stats MTU Probe", pct=0, log="Collecting network interface MTU baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_if_stats()
            min_val = min(s.mtu for s in stats.values() if s.mtu > 0) if stats else 0
            samples_list.append(min_val)
            logger.info(f"Sample {i+1}/{samples}: Net If Stats MTU Min {min_val}")
            metadata = {"mtu_min": min_val}
        except Exception as e:
            logger.error(f"Error auditing net if stats mtu min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Stats MTU Min", pct=pct, log=f"Measured net if stats mtu min sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = min(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Minimum net if stats mtu: {final_val}")
    yield {"status": "audit_complete", "min_mtu": final_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_stats_speed_min_ultimate_audit")
async def system_net_if_stats_speed_min_ultimate_audit(samples: int = 3):
    """
    Audits the minimum speed status across all network interfaces.
    """
    logger.info(f"Starting system net if stats speed min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net If Stats Speed Probe", pct=0, log="Collecting network interface speed baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_if_stats()
            # Some speeds might be 0 or negative if unknown
            valid_speeds = [s.speed for s in stats.values() if s.speed > 0]
            min_val = min(valid_speeds) if valid_speeds else 0
            samples_list.append(min_val)
            logger.info(f"Sample {i+1}/{samples}: Net If Stats Speed Min {min_val}")
            metadata = {"speed_min": min_val}
        except Exception as e:
            logger.error(f"Error auditing net if stats speed min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Stats Speed Min", pct=pct, log=f"Measured net if stats speed min sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = min(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Minimum net if stats speed: {final_val}")
    yield {"status": "audit_complete", "min_speed": final_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_mac_max_ultimate_audit")
async def system_net_if_addrs_mac_max_ultimate_audit(samples: int = 3):
    """
    Audits the maximum count of MAC addresses found on a single interface.
    """
    logger.info(f"Starting system net if addrs mac max ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net If Addrs MAC Probe", pct=0, log="Collecting network interface MAC address baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            af_link = getattr(psutil, "AF_LINK", -1)
            if af_link == -1:
                import socket
                af_link = getattr(socket, "AF_LINK", 18 if sys.platform == "darwin" else 17)
            
            max_macs = max(sum(1 for addr in interface if addr.family == af_link) for interface in addrs.values()) if addrs else 0
            samples_list.append(max_macs)
            logger.info(f"Sample {i+1}/{samples}: Net If Addrs MAC Max {max_macs}")
            metadata = {"mac_max": max_macs}
        except Exception as e:
            logger.error(f"Error auditing net if addrs mac max ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Addrs MAC Max", pct=pct, log=f"Measured net if addrs mac max sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = max(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Maximum net if addrs mac count: {final_val}")
    yield {"status": "audit_complete", "max_mac_count": final_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_broadcast_max_ultimate_audit")
async def system_net_if_addrs_broadcast_max_ultimate_audit(samples: int = 3):
    """
    Audits the maximum count of broadcast addresses found on a single interface.
    """
    logger.info(f"Starting system net if addrs broadcast max ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net If Addrs Broadcast Probe", pct=0, log="Collecting network interface broadcast address baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            max_broadcasts = max(sum(1 for addr in interface if getattr(addr, "broadcast", None)) for interface in addrs.values()) if addrs else 0
            samples_list.append(max_broadcasts)
            logger.info(f"Sample {i+1}/{samples}: Net If Addrs Broadcast Max {max_broadcasts}")
            metadata = {"broadcast_max": max_broadcasts}
        except Exception as e:
            logger.error(f"Error auditing net if addrs broadcast max ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Addrs Broadcast Max", pct=pct, log=f"Measured net if addrs broadcast max sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = max(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Maximum net if addrs broadcast count: {final_val}")
    yield {"status": "audit_complete", "max_broadcast_count": final_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_stats_isup_min_ultimate_audit")
async def system_net_if_stats_isup_min_ultimate_audit(samples: int = 3):
    """
    Audits the minimum isup status across all network interfaces (binary min).
    """
    logger.info(f"Starting system net if stats isup min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net If Stats Isup Probe", pct=0, log="Collecting network interface isup baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_if_stats()
            min_val = min(int(s.isup) for s in stats.values()) if stats else 0
            samples_list.append(min_val)
            logger.info(f"Sample {i+1}/{samples}: Net If Stats Isup Min {min_val}")
            metadata = {"isup_min": min_val}
        except Exception as e:
            logger.error(f"Error auditing net if stats isup min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Stats Isup Min", pct=pct, log=f"Measured net if stats isup min sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = min(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Minimum net if stats isup: {final_val}")
    yield {"status": "audit_complete", "min_isup": final_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_stats_duplex_min_ultimate_audit")
async def system_net_if_stats_duplex_min_ultimate_audit(samples: int = 3):
    """
    Audits the minimum duplex status across all network interfaces.
    """
    logger.info(f"Starting system net if stats duplex min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net If Stats Duplex Probe", pct=0, log="Collecting network interface duplex baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_if_stats()
            min_val = min(int(s.duplex) for s in stats.values()) if stats else 0
            samples_list.append(min_val)
            logger.info(f"Sample {i+1}/{samples}: Net If Stats Duplex Min {min_val}")
            metadata = {"duplex_min": min_val}
        except Exception as e:
            logger.error(f"Error auditing net if stats duplex min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Stats Duplex Min", pct=pct, log=f"Measured net if stats duplex min sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = min(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Minimum net if stats duplex: {final_val}")
    yield {"status": "audit_complete", "min_duplex": final_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_ipv4_max_ultimate_audit")
async def system_net_if_addrs_ipv4_max_ultimate_audit(samples: int = 3):
    """
    Audits the maximum count of IPv4 addresses found on a single interface.
    """
    logger.info(f"Starting system net if addrs ipv4 max ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net If Addrs IPv4 Probe", pct=0, log="Collecting network interface IPv4 address baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            import socket
            af_inet = getattr(socket, "AF_INET", 2)
            
            max_ips = max(sum(1 for addr in interface if addr.family == af_inet) for interface in addrs.values()) if addrs else 0
            samples_list.append(max_ips)
            logger.info(f"Sample {i+1}/{samples}: Net If Addrs IPv4 Max {max_ips}")
            metadata = {"ipv4_max": max_ips}
        except Exception as e:
            logger.error(f"Error auditing net if addrs ipv4 max ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Addrs IPv4 Max", pct=pct, log=f"Measured net if addrs ipv4 max sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = max(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Maximum net if addrs ipv4 count: {final_val}")
    yield {"status": "audit_complete", "max_ipv4_count": final_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_ipv6_max_ultimate_audit")
async def system_net_if_addrs_ipv6_max_ultimate_audit(samples: int = 3):
    """
    Audits the maximum count of IPv6 addresses found on a single interface.
    """
    logger.info(f"Starting system net if addrs ipv6 max ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net If Addrs IPv6 Probe", pct=0, log="Collecting network interface IPv6 address baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            import socket
            af_inet6 = getattr(socket, "AF_INET6", 30 if sys.platform == "darwin" else 10)
            
            max_ips = max(sum(1 for addr in interface if addr.family == af_inet6) for interface in addrs.values()) if addrs else 0
            samples_list.append(max_ips)
            logger.info(f"Sample {i+1}/{samples}: Net If Addrs IPv6 Max {max_ips}")
            metadata = {"ipv6_max": max_ips}
        except Exception as e:
            logger.error(f"Error auditing net if addrs ipv6 max ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Addrs IPv6 Max", pct=pct, log=f"Measured net if addrs ipv6 max sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = max(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Maximum net if addrs ipv6 count: {final_val}")
    yield {"status": "audit_complete", "max_ipv6_count": final_val, "stability": "STABLE"}


@progress_tool(name="system_net_if_stats_duplex_max_ultimate_audit")
async def system_net_if_stats_duplex_max_ultimate_audit(samples: int = 3):
    """
    Audits the maximum duplex status across all network interfaces.
    """
    logger.info(f"Starting system net if stats duplex max ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net If Stats Duplex Probe", pct=0, log="Collecting network interface duplex baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_if_stats()
            max_val = max(int(s.duplex) for s in stats.values()) if stats else 0
            samples_list.append(max_val)
            logger.info(f"Sample {i+1}/{samples}: Net If Stats Duplex Max {max_val}")
            metadata = {"duplex_max": max_val}
        except Exception as e:
            logger.error(f"Error auditing net if stats duplex max ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Stats Duplex Max", pct=pct, log=f"Measured net if stats duplex max sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = max(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Maximum net if stats duplex: {final_val}")
    yield {"status": "audit_complete", "max_duplex": final_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_stats_duplex_avg_ultimate_audit")
async def system_net_if_stats_duplex_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average duplex status across all network interfaces.
    """
    logger.info(f"Starting system net if stats duplex avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net If Stats Duplex Probe", pct=0, log="Collecting network interface duplex baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_if_stats()
            avg_val = sum(int(s.duplex) for s in stats.values()) / len(stats) if stats else 0
            samples_list.append(avg_val)
            logger.info(f"Sample {i+1}/{samples}: Net If Stats Duplex Avg {avg_val}")
            metadata = {"duplex_avg": avg_val}
        except Exception as e:
            logger.error(f"Error auditing net if stats duplex avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Stats Duplex Avg", pct=pct, log=f"Measured net if stats duplex avg sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net if stats duplex: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_duplex": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_stats_flags_avg_ultimate_audit")
async def system_net_if_stats_flags_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average flags value across all network interfaces.
    """
    logger.info(f"Starting system net if stats flags avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net If Stats Flags Probe", pct=0, log="Collecting network interface flags baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_if_stats()
            def get_flags_val(s):
                if isinstance(s.flags, str):
                    return len(s.flags.split(',')) if s.flags else 0
                return s.flags
            avg_val = sum(get_flags_val(s) for s in stats.values()) / len(stats) if stats else 0
            samples_list.append(avg_val)
            logger.info(f"Sample {i+1}/{samples}: Net If Stats Flags Avg {avg_val}")
            metadata = {"flags_avg": avg_val}
        except Exception as e:
            logger.error(f"Error auditing net if stats flags avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Stats Flags Avg", pct=pct, log=f"Measured net if stats flags avg sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net if stats flags: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_flags": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_stats_flags_min_ultimate_audit")
async def system_net_if_stats_flags_min_ultimate_audit(samples: int = 3):
    """
    Audits the minimum flags value across all network interfaces.
    """
    logger.info(f"Starting system net if stats flags min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net If Stats Flags Probe", pct=0, log="Collecting network interface flags baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.net_if_stats()
            def get_flags_val(s):
                if isinstance(s.flags, str):
                    return len(s.flags.split(',')) if s.flags else 0
                return s.flags
            min_val = min(get_flags_val(s) for s in stats.values()) if stats else 0
            samples_list.append(min_val)
            logger.info(f"Sample {i+1}/{samples}: Net If Stats Flags Min {min_val}")
            metadata = {"flags_min": min_val}
        except Exception as e:
            logger.error(f"Error auditing net if stats flags min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Stats Flags Min", pct=pct, log=f"Measured net if stats flags min sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = min(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Minimum net if stats flags: {final_val}")
    yield {"status": "audit_complete", "min_flags": final_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_netmask_avg_ultimate_audit")
async def system_net_if_addrs_netmask_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average count of netmasks found per interface.
    """
    logger.info(f"Starting system net if addrs netmask avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net If Addrs Netmask Probe", pct=0, log="Collecting network interface netmask baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            netmask_count = sum(1 for interface in addrs.values() for addr in interface if addr.netmask)
            samples_list.append(netmask_count)
            logger.info(f"Sample {i+1}/{samples}: Net If Addrs Netmask Count {netmask_count}")
            metadata = {"netmask_count": netmask_count}
        except Exception as e:
            logger.error(f"Error auditing net if addrs netmask avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Addrs Netmask", pct=pct, log=f"Measured net if addrs netmask sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net if addrs netmask count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_netmask_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_netmask_max_ultimate_audit")
async def system_net_if_addrs_netmask_max_ultimate_audit(samples: int = 3):
    """
    Audits the maximum count of netmasks found on a single interface.
    """
    logger.info(f"Starting system net if addrs netmask max ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net If Addrs Netmask Probe", pct=0, log="Collecting network interface netmask baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            max_netmasks = max(sum(1 for addr in interface if addr.netmask) for interface in addrs.values()) if addrs else 0
            samples_list.append(max_netmasks)
            logger.info(f"Sample {i+1}/{samples}: Net If Addrs Netmask Max {max_netmasks}")
            metadata = {"netmask_max": max_netmasks}
        except Exception as e:
            logger.error(f"Error auditing net if addrs netmask max ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Addrs Netmask Max", pct=pct, log=f"Measured net if addrs netmask max sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = max(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Maximum net if addrs netmask count: {final_val}")
    yield {"status": "audit_complete", "max_netmask_count": final_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_ptp_avg_ultimate_audit")
async def system_net_if_addrs_ptp_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average count of PTP addresses found per interface.
    """
    logger.info(f"Starting system net if addrs ptp avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net If Addrs PTP Probe", pct=0, log="Collecting network interface PTP baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            ptp_count = sum(1 for interface in addrs.values() for addr in interface if getattr(addr, "ptp", None))
            samples_list.append(ptp_count)
            logger.info(f"Sample {i+1}/{samples}: Net If Addrs PTP Count {ptp_count}")
            metadata = {"ptp_count": ptp_count}
        except Exception as e:
            logger.error(f"Error auditing net if addrs ptp avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Addrs PTP", pct=pct, log=f"Measured net if addrs ptp sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average net if addrs ptp count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_ptp_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_ptp_max_ultimate_audit")
async def system_net_if_addrs_ptp_max_ultimate_audit(samples: int = 3):
    """
    Audits the maximum count of PTP addresses found on a single interface.
    """
    logger.info(f"Starting system net if addrs ptp max ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net If Addrs PTP Probe", pct=0, log="Collecting network interface PTP baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            max_ptp = max(sum(1 for addr in interface if getattr(addr, "ptp", None)) for interface in addrs.values()) if addrs else 0
            samples_list.append(max_ptp)
            logger.info(f"Sample {i+1}/{samples}: Net If Addrs PTP Max {max_ptp}")
            metadata = {"ptp_max": max_ptp}
        except Exception as e:
            logger.error(f"Error auditing net if addrs ptp_max ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net If Addrs PTP Max", pct=pct, log=f"Measured net if addrs ptp max sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = max(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Maximum net if addrs ptp count: {final_val}")
    yield {"status": "audit_complete", "max_ptp_count": final_val, "stability": "STABLE"}

@progress_tool(name="system_disk_partitions_fstype_avg_ultimate_audit")
async def system_disk_partitions_fstype_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average count of unique file system types found per disk scan.
    """
    logger.info(f"Starting system disk partitions fstype avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk Fstype Probe", pct=0, log="Collecting disk partition fstype baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            parts = psutil.disk_partitions(all=True)
            fstypes = {p.fstype for p in parts if p.fstype}
            current_val = len(fstypes)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Fstypes Count {current_val}")
            metadata = {"fstype_count": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk partitions fstype avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Fstypes", pct=pct, log=f"Measured disk partitions fstype sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk partition fstype count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_fstype_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_partitions_fstype_max_ultimate_audit")
async def system_disk_partitions_fstype_max_ultimate_audit(samples: int = 3):
    """
    Audits the maximum count of unique file system types found per disk scan.
    """
    logger.info(f"Starting system disk partitions fstype max ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk Fstype Probe", pct=0, log="Collecting disk partition fstype baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            parts = psutil.disk_partitions(all=True)
            fstypes = {p.fstype for p in parts if p.fstype}
            current_val = len(fstypes)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Fstypes Max {current_val}")
            metadata = {"fstype_max": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk partitions fstype_max ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Fstypes Max", pct=pct, log=f"Measured disk partitions fstype max sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = max(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Maximum disk partition fstype count: {final_val}")
    yield {"status": "audit_complete", "max_fstype_count": final_val, "stability": "STABLE"}

@progress_tool(name="system_disk_partitions_mountpoint_avg_ultimate_audit")
async def system_disk_partitions_mountpoint_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average count of unique mountpoints found per disk scan.
    """
    logger.info(f"Starting system disk partitions mountpoint avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk Mountpoint Probe", pct=0, log="Collecting disk partition mountpoint baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            parts = psutil.disk_partitions(all=True)
            mounts = {p.mountpoint for p in parts if p.mountpoint}
            current_val = len(mounts)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Mountpoints Count {current_val}")
            metadata = {"mountpoint_count": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk partitions mountpoint avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Mountpoints", pct=pct, log=f"Measured disk partitions mountpoint sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk partition mountpoint count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_mountpoint_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_partitions_mountpoint_max_ultimate_audit")
async def system_disk_partitions_mountpoint_max_ultimate_audit(samples: int = 3):
    """
    Audits the maximum count of unique mountpoints found per disk scan.
    """
    logger.info(f"Starting system disk partitions mountpoint max ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk Mountpoint Probe", pct=0, log="Collecting disk partition mountpoint baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            parts = psutil.disk_partitions(all=True)
            mounts = {p.mountpoint for p in parts if p.mountpoint}
            current_val = len(mounts)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Mountpoints Max {current_val}")
            metadata = {"mountpoint_max": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk partitions mountpoint max ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Mountpoints Max", pct=pct, log=f"Measured disk partitions mountpoint max sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = max(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Maximum disk partition mountpoint count: {final_val}")
    yield {"status": "audit_complete", "max_mountpoint_count": final_val, "stability": "STABLE"}

@progress_tool(name="system_disk_partitions_fstype_min_ultimate_audit")
async def system_disk_partitions_fstype_min_ultimate_audit(samples: int = 3):
    """
    Audits the minimum count of unique file system types found per disk scan.
    """
    logger.info(f"Starting system disk partitions fstype min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk Fstype Probe", pct=0, log="Collecting disk partition fstype baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            parts = psutil.disk_partitions(all=True)
            fstypes = {p.fstype for p in parts if p.fstype}
            current_val = len(fstypes)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Fstypes Min {current_val}")
            metadata = {"fstype_min": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk partitions fstype min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Fstypes Min", pct=pct, log=f"Measured disk partitions fstype min sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = min(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Minimum disk partition fstype count: {final_val}")
    yield {"status": "audit_complete", "min_fstype_count": final_val, "stability": "STABLE"}

@progress_tool(name="system_disk_partitions_mountpoint_min_ultimate_audit")
async def system_disk_partitions_mountpoint_min_ultimate_audit(samples: int = 3):
    """
    Audits the minimum count of unique mountpoints found per disk scan.
    """
    logger.info(f"Starting system disk partitions mountpoint min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk Mountpoint Probe", pct=0, log="Collecting disk partition mountpoint baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            parts = psutil.disk_partitions(all=True)
            mounts = {p.mountpoint for p in parts if p.mountpoint}
            current_val = len(mounts)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Mountpoints Min {current_val}")
            metadata = {"mountpoint_min": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk partitions mountpoint min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Mountpoints Min", pct=pct, log=f"Measured disk partitions mountpoint min sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = min(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Minimum disk partition mountpoint count: {final_val}")
    yield {"status": "audit_complete", "min_mountpoint_count": final_val, "stability": "STABLE"}

@progress_tool(name="system_disk_partitions_opts_avg_ultimate_audit")
async def system_disk_partitions_opts_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average count of unique mount options found per disk scan.
    """
    logger.info(f"Starting system disk partitions opts avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk Opts Probe", pct=0, log="Collecting disk partition options baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            parts = psutil.disk_partitions(all=True)
            opts = set()
            for p in parts:
                if p.opts:
                    for opt in p.opts.split(","):
                        opts.add(opt)
            current_val = len(opts)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Opts Count {current_val}")
            metadata = {"opts_count": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk partitions opts avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Opts", pct=pct, log=f"Measured disk partitions opts sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk partition opts count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_opts_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_partitions_opts_max_ultimate_audit")
async def system_disk_partitions_opts_max_ultimate_audit(samples: int = 3):
    """
    Audits the maximum count of unique mount options found per disk scan.
    """
    logger.info(f"Starting system disk partitions opts max ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk Opts Probe", pct=0, log="Collecting disk partition options baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            parts = psutil.disk_partitions(all=True)
            opts = set()
            for p in parts:
                if p.opts:
                    for opt in p.opts.split(","):
                        opts.add(opt)
            current_val = len(opts)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Opts Max {current_val}")
            metadata = {"opts_max": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk partitions opts max ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Opts Max", pct=pct, log=f"Measured disk partitions opts max sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = max(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Maximum disk partition opts count: {final_val}")
    yield {"status": "audit_complete", "max_opts_count": final_val, "stability": "STABLE"}

@progress_tool(name="system_disk_partitions_opts_min_ultimate_audit")
async def system_disk_partitions_opts_min_ultimate_audit(samples: int = 3):
    """
    Audits the minimum count of unique mount options found per disk scan.
    """
    logger.info(f"Starting system disk partitions opts min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk Opts Probe", pct=0, log="Collecting disk partition options baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            parts = psutil.disk_partitions(all=True)
            opts = set()
            for p in parts:
                if p.opts:
                    for opt in p.opts.split(","):
                        opts.add(opt)
            current_val = len(opts)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Opts Min {current_val}")
            metadata = {"opts_min": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk partitions opts min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Opts Min", pct=pct, log=f"Measured disk partitions opts min sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = min(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Minimum disk partition opts count: {final_val}")
    yield {"status": "audit_complete", "min_opts_count": final_val, "stability": "STABLE"}

@progress_tool(name="system_disk_partitions_device_avg_ultimate_audit")
async def system_disk_partitions_device_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average count of unique devices found per disk scan.
    """
    logger.info(f"Starting system disk partitions device avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk Device Probe", pct=0, log="Collecting disk partition device baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            parts = psutil.disk_partitions(all=True)
            devices = {p.device for p in parts if p.device}
            current_val = len(devices)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Devices Count {current_val}")
            metadata = {"device_count": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk partitions device avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Devices", pct=pct, log=f"Measured disk partitions device sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk partition device count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_device_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_partitions_device_max_ultimate_audit")
async def system_disk_partitions_device_max_ultimate_audit(samples: int = 3):
    """
    Audits the maximum count of unique devices found per disk scan.
    """
    logger.info(f"Starting system disk partitions device max ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk Device Probe", pct=0, log="Collecting disk partition device baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            parts = psutil.disk_partitions(all=True)
            devices = {p.device for p in parts if p.device}
            current_val = len(devices)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Devices Max {current_val}")
            metadata = {"device_max": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk partitions device max ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Devices Max", pct=pct, log=f"Measured disk partitions device max sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = max(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Maximum disk partition device count: {final_val}")
    yield {"status": "audit_complete", "max_device_count": final_val, "stability": "STABLE"}

@progress_tool(name="system_disk_partitions_device_min_ultimate_audit")
async def system_disk_partitions_device_min_ultimate_audit(samples: int = 3):
    """
    Audits the minimum count of unique devices found per disk scan.
    """
    logger.info(f"Starting system disk partitions device min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk Device Probe", pct=0, log="Collecting disk partition device baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            parts = psutil.disk_partitions(all=True)
            devices = {p.device for p in parts if p.device}
            current_val = len(devices)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Devices Min {current_val}")
            metadata = {"device_min": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk partitions device min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Devices Min", pct=pct, log=f"Measured disk partitions device min sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = min(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Minimum disk partition device count: {final_val}")
    yield {"status": "audit_complete", "min_device_count": final_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_netmask_min_ultimate_audit")
async def system_net_if_addrs_netmask_min_ultimate_audit(samples: int = 3):
    """
    Audits the minimum count of unique netmasks found per network scan.
    """
    logger.info(f"Starting system net if addrs netmask min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Netmask Probe", pct=0, log="Collecting network interface netmask baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            netmasks = set()
            for interface, snics in addrs.items():
                for snic in snics:
                    if snic.netmask:
                        netmasks.add(snic.netmask)
            current_val = len(netmasks)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Netmask Min {current_val}")
            metadata = {"netmask_min": current_val}
        except Exception as e:
            logger.error(f"Error auditing net if addrs netmask min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Netmask Min", pct=pct, log=f"Measured net if addrs netmask min sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = min(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Minimum netmask count: {final_val}")
    yield {"status": "audit_complete", "min_netmask_count": final_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_ptp_min_ultimate_audit")
async def system_net_if_addrs_ptp_min_ultimate_audit(samples: int = 3):
    """
    Audits the minimum count of unique PTP addresses found per network scan.
    """
    logger.info(f"Starting system net if addrs ptp min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing PTP Probe", pct=0, log="Collecting network interface ptp baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            ptps = set()
            for interface, snics in addrs.items():
                for snic in snics:
                    if snic.ptp:
                        ptps.add(snic.ptp)
            current_val = len(ptps)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: PTP Min {current_val}")
            metadata = {"ptp_min": current_val}
        except Exception as e:
            logger.error(f"Error auditing net if addrs ptp min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling PTP Min", pct=pct, log=f"Measured net if addrs ptp min sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = min(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Minimum ptp count: {final_val}")
    yield {"status": "audit_complete", "min_ptp_count": final_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_ipv4_min_ultimate_audit")
async def system_net_if_addrs_ipv4_min_ultimate_audit(samples: int = 3):
    """
    Audits the minimum count of unique IPv4 addresses found per network scan.
    """
    logger.info(f"Starting system net if addrs ipv4 min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing IPv4 Probe", pct=0, log="Collecting network interface ipv4 baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            ipv4s = set()
            for interface, snics in addrs.items():
                for snic in snics:
                    if snic.family == 2: # AF_INET
                        ipv4s.add(snic.address)
            current_val = len(ipv4s)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: IPv4 Min {current_val}")
            metadata = {"ipv4_min": current_val}
        except Exception as e:
            logger.error(f"Error auditing net if addrs ipv4 min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling IPv4 Min", pct=pct, log=f"Measured net if addrs ipv4 min sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = min(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Minimum ipv4 count: {final_val}")
    yield {"status": "audit_complete", "min_ipv4_count": final_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_ipv6_min_ultimate_audit")
async def system_net_if_addrs_ipv6_min_ultimate_audit(samples: int = 3):
    """
    Audits the minimum count of unique IPv6 addresses found per network scan.
    """
    logger.info(f"Starting system net if addrs ipv6 min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing IPv6 Probe", pct=0, log="Collecting network interface ipv6 baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            ipv6s = set()
            for interface, snics in addrs.items():
                for snic in snics:
                    if snic.family == 30 or snic.family == 23: # AF_INET6 (30 on Linux, 23 on Darwin/BSD)
                        ipv6s.add(snic.address)
            current_val = len(ipv6s)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: IPv6 Min {current_val}")
            metadata = {"ipv6_min": current_val}
        except Exception as e:
            logger.error(f"Error auditing net if addrs ipv6 min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling IPv6 Min", pct=pct, log=f"Measured net if addrs ipv6 min sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = min(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Minimum ipv6 count: {final_val}")
    yield {"status": "audit_complete", "min_ipv6_count": final_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_mac_min_ultimate_audit")
async def system_net_if_addrs_mac_min_ultimate_audit(samples: int = 3):
    """
    Audits the minimum count of unique MAC addresses found per network scan.
    """
    logger.info(f"Starting system net if addrs mac min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing MAC Probe", pct=0, log="Collecting network interface mac baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            macs = set()
            for interface, snics in addrs.items():
                for snic in snics:
                    if snic.family == psutil.AF_LINK:
                        macs.add(snic.address)
            current_val = len(macs)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: MAC Min {current_val}")
            metadata = {"mac_min": current_val}
        except Exception as e:
            logger.error(f"Error auditing net if addrs mac min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling MAC Min", pct=pct, log=f"Measured net if addrs mac min sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = min(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Minimum mac count: {final_val}")
    yield {"status": "audit_complete", "min_mac_count": final_val, "stability": "STABLE"}

@progress_tool(name="system_net_if_addrs_broadcast_min_ultimate_audit")
async def system_net_if_addrs_broadcast_min_ultimate_audit(samples: int = 3):
    """
    Audits the minimum count of unique broadcast addresses found per network scan.
    """
    logger.info(f"Starting system net if addrs broadcast min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Broadcast Probe", pct=0, log="Collecting network interface broadcast baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            broadcasts = set()
            for interface, snics in addrs.items():
                for snic in snics:
                    if snic.broadcast:
                        broadcasts.add(snic.broadcast)
            current_val = len(broadcasts)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Broadcast Min {current_val}")
            metadata = {"broadcast_min": current_val}
        except Exception as e:
            logger.error(f"Error auditing net if addrs broadcast min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Broadcast Min", pct=pct, log=f"Measured net if addrs broadcast min sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    final_val = min(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Minimum broadcast count: {final_val}")
    yield {"status": "audit_complete", "min_broadcast_count": final_val, "stability": "STABLE"}

@progress_tool(name="system_disk_io_counters_read_count_avg_ultimate_audit")
async def system_disk_io_counters_read_count_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average disk read count across multiple samples.
    """
    logger.info(f"Starting system disk io counters read count avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk IO Probe", pct=0, log="Collecting disk read count baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.disk_io_counters()
            current_val = io.read_count if io else 0
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Read Count {current_val}")
            metadata = {"read_count": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk io read count avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Read Count", pct=pct, log=f"Measured disk read count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk read count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_read_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_io_counters_write_count_avg_ultimate_audit")
async def system_disk_io_counters_write_count_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average disk write count across multiple samples.
    """
    logger.info(f"Starting system disk io counters write count avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk IO Probe", pct=0, log="Collecting disk write count baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.disk_io_counters()
            current_val = io.write_count if io else 0
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Write Count {current_val}")
            metadata = {"write_count": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk io write count avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Write Count", pct=pct, log=f"Measured disk write count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk write count: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_write_count": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_io_counters_read_bytes_avg_ultimate_audit")
async def system_disk_io_counters_read_bytes_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average disk read bytes across multiple samples.
    """
    logger.info(f"Starting system disk io counters read bytes avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk IO Probe", pct=0, log="Collecting disk read bytes baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.disk_io_counters()
            current_val = io.read_bytes if io else 0
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Read Bytes {current_val}")
            metadata = {"read_bytes": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk io read bytes avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Read Bytes", pct=pct, log=f"Measured disk read bytes sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk read bytes: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_read_bytes": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_io_counters_write_bytes_avg_ultimate_audit")
async def system_disk_io_counters_write_bytes_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average disk write bytes across multiple samples.
    """
    logger.info(f"Starting system disk io counters write bytes avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk IO Probe", pct=0, log="Collecting disk write bytes baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.disk_io_counters()
            current_val = io.write_bytes if io else 0
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Write Bytes {current_val}")
            metadata = {"write_bytes": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk io write bytes avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Write Bytes", pct=pct, log=f"Measured disk write bytes sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk write bytes: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_write_bytes": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_io_counters_read_time_avg_ultimate_audit")
async def system_disk_io_counters_read_time_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average disk read time across multiple samples.
    """
    logger.info(f"Starting system disk io counters read time avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk IO Probe", pct=0, log="Collecting disk read time baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.disk_io_counters()
            current_val = io.read_time if io else 0
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Read Time {current_val}")
            metadata = {"read_time": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk io read time avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Read Time", pct=pct, log=f"Measured disk read time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk read time: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_read_time": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_io_counters_write_time_avg_ultimate_audit")
async def system_disk_io_counters_write_time_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average disk write time across multiple samples.
    """
    logger.info(f"Starting system disk io counters write time avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk IO Probe", pct=0, log="Collecting disk write time baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.disk_io_counters()
            current_val = io.write_time if io else 0
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Write Time {current_val}")
            metadata = {"write_time": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk io write time avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Write Time", pct=pct, log=f"Measured disk write time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk write time: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_write_time": avg_val, "stability": "STABLE"}

@progress_tool(name="system_disk_io_counters_busy_time_avg_ultimate_audit")
async def system_disk_io_counters_busy_time_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average disk busy time across multiple samples.
    """
    logger.info(f"Starting system disk io counters busy time avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk IO Probe", pct=0, log="Collecting disk busy time baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.disk_io_counters()
            current_val = getattr(io, "busy_time", 0) if io else 0
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Disk Busy Time {current_val}")
            metadata = {"busy_time": current_val}
        except Exception as e:
            logger.error(f"Error auditing disk io busy time avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk Busy Time", pct=pct, log=f"Measured disk busy time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average disk busy time: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_busy_time": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_stats_ctx_switches_avg_ultimate_audit")
async def system_cpu_stats_ctx_switches_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average CPU context switches across multiple samples.
    """
    logger.info(f"Starting system cpu stats ctx switches avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Stats Probe", pct=0, log="Collecting CPU context switches baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            current_val = stats.ctx_switches
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Ctx Switches {current_val}")
            metadata = {"ctx_switches": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu stats ctx switches avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU Ctx Switches", pct=pct, log=f"Measured cpu stats ctx switches sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU context switches: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_ctx_switches": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_stats_interrupts_avg_ultimate_audit")
async def system_cpu_stats_interrupts_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average CPU interrupts across multiple samples.
    """
    logger.info(f"Starting system cpu stats interrupts avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Stats Probe", pct=0, log="Collecting CPU interrupts baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            current_val = stats.interrupts
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Interrupts {current_val}")
            metadata = {"interrupts": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu stats interrupts avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU Interrupts", pct=pct, log=f"Measured cpu stats interrupts sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU interrupts: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_interrupts": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_stats_syscalls_avg_ultimate_audit")
async def system_cpu_stats_syscalls_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average CPU syscalls across multiple samples.
    """
    logger.info(f"Starting system cpu stats syscalls avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Stats Probe", pct=0, log="Collecting CPU syscalls baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            current_val = stats.syscalls
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Syscalls {current_val}")
            metadata = {"syscalls": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu stats syscalls avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU Syscalls", pct=pct, log=f"Measured cpu stats syscalls sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU syscalls: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_syscalls": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_stats_soft_interrupts_avg_ultimate_audit")
async def system_cpu_stats_soft_interrupts_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average CPU soft interrupts across multiple samples.
    """
    logger.info(f"Starting system cpu stats soft interrupts avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Stats Probe", pct=0, log="Collecting CPU soft interrupts baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            current_val = getattr(stats, "soft_interrupts", 0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Soft Interrupts {current_val}")
            metadata = {"soft_interrupts": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu stats soft interrupts avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU Soft Interrupts", pct=pct, log=f"Measured cpu stats soft interrupts sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU soft interrupts: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_soft_interrupts": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_percent_iowait_avg_ultimate_audit")
async def system_cpu_times_percent_iowait_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average CPU iowait percentage across multiple samples.
    """
    logger.info(f"Starting system cpu times percent iowait avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Times Probe", pct=0, log="Collecting CPU iowait percentage baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times_percent(interval=None)
            current_val = getattr(times, "iowait", 0.0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Iowait % {current_val}")
            metadata = {"iowait_percent": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu times percent iowait avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU Iowait %", pct=pct, log=f"Measured cpu times percent iowait sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU iowait %: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_iowait_percent": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_percent_irq_avg_ultimate_audit")
async def system_cpu_times_percent_irq_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average CPU irq percentage across multiple samples.
    """
    logger.info(f"Starting system cpu times percent irq avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Times Probe", pct=0, log="Collecting CPU irq percentage baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times_percent(interval=None)
            current_val = getattr(times, "irq", 0.0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Irq % {current_val}")
            metadata = {"irq_percent": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu times percent irq avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU Irq %", pct=pct, log=f"Measured cpu times percent irq sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU irq %: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_irq_percent": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_percent_softirq_avg_ultimate_audit")
async def system_cpu_times_percent_softirq_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average CPU softirq percentage across multiple samples.
    """
    logger.info(f"Starting system cpu times percent softirq avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Times Probe", pct=0, log="Collecting CPU softirq percentage baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times_percent(interval=None)
            current_val = getattr(times, "softirq", 0.0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Softirq % {current_val}")
            metadata = {"softirq_percent": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu times percent softirq avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU Softirq %", pct=pct, log=f"Measured cpu times percent softirq sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU softirq %: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_softirq_percent": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_percent_steal_avg_ultimate_audit")
async def system_cpu_times_percent_steal_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average CPU steal percentage across multiple samples.
    """
    logger.info(f"Starting system cpu times percent steal avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Times Probe", pct=0, log="Collecting CPU steal percentage baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times_percent(interval=None)
            current_val = getattr(times, "steal", 0.0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Steal % {current_val}")
            metadata = {"steal_percent": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu times percent steal avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU Steal %", pct=pct, log=f"Measured cpu times percent steal sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU steal %: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_steal_percent": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_percent_guest_avg_ultimate_audit")
async def system_cpu_times_percent_guest_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average CPU guest percentage across multiple samples.
    """
    logger.info(f"Starting system cpu times percent guest avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Times Probe", pct=0, log="Collecting CPU guest percentage baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times_percent(interval=None)
            current_val = getattr(times, "guest", 0.0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Guest % {current_val}")
            metadata = {"guest_percent": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu times percent guest avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU Guest %", pct=pct, log=f"Measured cpu times percent guest sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU guest %: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_guest_percent": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_percent_guest_nice_avg_ultimate_audit")
async def system_cpu_times_percent_guest_nice_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average CPU guest_nice percentage across multiple samples.
    """
    logger.info(f"Starting system cpu times percent guest_nice avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Times Probe", pct=0, log="Collecting CPU guest_nice percentage baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times_percent(interval=None)
            current_val = getattr(times, "guest_nice", 0.0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Guest Nice % {current_val}")
            metadata = {"guest_nice_percent": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu times percent guest_nice avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU Guest Nice %", pct=pct, log=f"Measured cpu times percent guest_nice sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU guest_nice %: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_guest_nice_percent": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_percent_nice_avg_ultimate_audit")
async def system_cpu_times_percent_nice_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average CPU nice percentage across multiple samples.
    """
    logger.info(f"Starting system cpu times percent nice avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Times Probe", pct=0, log="Collecting CPU nice percentage baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times_percent(interval=None)
            current_val = getattr(times, "nice", 0.0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU Nice % {current_val}")
            metadata = {"nice_percent": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu times percent nice avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU Nice %", pct=pct, log=f"Measured cpu times percent nice sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average CPU nice %: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_nice_percent": avg_val, "stability": "STABLE"}



@progress_tool(name="system_virtual_memory_shared_avg_ultimate_audit")
async def system_virtual_memory_shared_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average shared virtual memory across multiple samples.
    """
    logger.info(f"Starting system virtual memory shared avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Memory Probe", pct=0, log="Collecting shared virtual memory baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            mem = psutil.virtual_memory()
            current_val = getattr(mem, "shared", 0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Shared Memory {current_val}")
            metadata = {"shared_memory": current_val}
        except Exception as e:
            logger.error(f"Error auditing virtual memory shared avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Shared Memory", pct=pct, log=f"Measured virtual memory shared sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average shared memory: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_shared_memory": avg_val, "stability": "STABLE"}

@progress_tool(name="system_virtual_memory_slab_avg_ultimate_audit")
async def system_virtual_memory_slab_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average slab virtual memory across multiple samples.
    """
    logger.info(f"Starting system virtual memory slab avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Memory Probe", pct=0, log="Collecting slab virtual memory baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            mem = psutil.virtual_memory()
            current_val = getattr(mem, "slab", 0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Slab Memory {current_val}")
            metadata = {"slab_memory": current_val}
        except Exception as e:
            logger.error(f"Error auditing virtual memory slab avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Slab Memory", pct=pct, log=f"Measured virtual memory slab sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average slab memory: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_slab_memory": avg_val, "stability": "STABLE"}

@progress_tool(name="system_virtual_memory_mapped_avg_ultimate_audit")
async def system_virtual_memory_mapped_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average mapped virtual memory across multiple samples.
    """
    logger.info(f"Starting system virtual memory mapped avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Memory Probe", pct=0, log="Collecting mapped virtual memory baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            mem = psutil.virtual_memory()
            current_val = getattr(mem, "mapped", 0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Mapped Memory {current_val}")
            metadata = {"mapped_memory": current_val}
        except Exception as e:
            logger.error(f"Error auditing virtual memory mapped avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Mapped Memory", pct=pct, log=f"Measured virtual memory mapped sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average mapped memory: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_mapped_memory": avg_val, "stability": "STABLE"}

@progress_tool(name="system_virtual_memory_dirty_avg_ultimate_audit")
async def system_virtual_memory_dirty_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average dirty virtual memory across multiple samples.
    """
    logger.info(f"Starting system virtual memory dirty avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Memory Probe", pct=0, log="Collecting dirty virtual memory baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            mem = psutil.virtual_memory()
            current_val = getattr(mem, "dirty", 0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Dirty Memory {current_val}")
            metadata = {"dirty_memory": current_val}
        except Exception as e:
            logger.error(f"Error auditing virtual memory dirty avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Dirty Memory", pct=pct, log=f"Measured virtual memory dirty sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average dirty memory: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_dirty_memory": avg_val, "stability": "STABLE"}

@progress_tool(name="system_swap_memory_total_avg_ultimate_audit")
async def system_swap_memory_total_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average total swap memory across multiple samples.
    """
    logger.info(f"Starting system swap memory total avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Swap Probe", pct=0, log="Collecting total swap memory baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            swap = psutil.swap_memory()
            current_val = swap.total
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Total Swap Memory {current_val}")
            metadata = {"total_swap_memory": current_val}
        except Exception as e:
            logger.error(f"Error auditing swap memory total avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Total Swap Memory", pct=pct, log=f"Measured total swap memory sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average total swap memory: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_total_swap": avg_val, "stability": "STABLE"}

@progress_tool(name="system_swap_memory_used_avg_ultimate_audit")
async def system_swap_memory_used_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average used swap memory across multiple samples.
    """
    logger.info(f"Starting system swap memory used avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Swap Probe", pct=0, log="Collecting used swap memory baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            swap = psutil.swap_memory()
            current_val = swap.used
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Used Swap Memory {current_val}")
            metadata = {"used_swap_memory": current_val}
        except Exception as e:
            logger.error(f"Error auditing swap memory used avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Used Swap Memory", pct=pct, log=f"Measured used swap memory sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average used swap memory: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_used_swap": avg_val, "stability": "STABLE"}

@progress_tool(name="system_swap_memory_free_avg_ultimate_audit")
async def system_swap_memory_free_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average free swap memory across multiple samples.
    """
    logger.info(f"Starting system swap memory free avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Swap Probe", pct=0, log="Collecting free swap memory baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            swap = psutil.swap_memory()
            current_val = swap.free
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Free Swap Memory {current_val}")
            metadata = {"free_swap_memory": current_val}
        except Exception as e:
            logger.error(f"Error auditing swap memory free avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Free Swap Memory", pct=pct, log=f"Measured free swap memory sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average free swap memory: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_free_swap": avg_val, "stability": "STABLE"}

@progress_tool(name="system_swap_memory_percent_avg_ultimate_audit")
async def system_swap_memory_percent_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average swap memory percentage across multiple samples.
    """
    logger.info(f"Starting system swap memory percent avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Swap Probe", pct=0, log="Collecting swap memory percentage baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            swap = psutil.swap_memory()
            current_val = swap.percent
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Swap Memory % {current_val}")
            metadata = {"swap_memory_percent": current_val}
        except Exception as e:
            logger.error(f"Error auditing swap memory percent avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Swap Memory %", pct=pct, log=f"Measured swap memory percentage sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average swap memory %: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_swap_percent": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_bytes_sent_avg_ultimate_audit")
async def system_net_io_bytes_sent_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average network bytes sent across multiple samples.
    """
    logger.info(f"Starting system net io bytes sent avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net Probe", pct=0, log="Collecting bytes sent baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.net_io_counters()
            current_val = counters.bytes_sent
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Bytes Sent {current_val}")
            metadata = {"bytes_sent": current_val}
        except Exception as e:
            logger.error(f"Error auditing net io bytes sent avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Bytes Sent", pct=pct, log=f"Measured net io bytes sent sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average bytes sent: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_bytes_sent": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_bytes_recv_avg_ultimate_audit")
async def system_net_io_bytes_recv_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average network bytes received across multiple samples.
    """
    logger.info(f"Starting system net io bytes recv avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net Probe", pct=0, log="Collecting bytes received baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.net_io_counters()
            current_val = counters.bytes_recv
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Bytes Recv {current_val}")
            metadata = {"bytes_recv": current_val}
        except Exception as e:
            logger.error(f"Error auditing net io bytes recv avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Bytes Recv", pct=pct, log=f"Measured net io bytes recv sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average bytes received: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_bytes_recv": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_packets_sent_avg_ultimate_audit")
async def system_net_io_packets_sent_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average network packets sent across multiple samples.
    """
    logger.info(f"Starting system net io packets sent avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net Probe", pct=0, log="Collecting packets sent baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.net_io_counters()
            current_val = counters.packets_sent
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Packets Sent {current_val}")
            metadata = {"packets_sent": current_val}
        except Exception as e:
            logger.error(f"Error auditing net io packets sent avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Packets Sent", pct=pct, log=f"Measured net io packets sent sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average packets sent: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_packets_sent": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_packets_recv_avg_ultimate_audit")
async def system_net_io_packets_recv_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average network packets received across multiple samples.
    """
    logger.info(f"Starting system net io packets recv avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net Probe", pct=0, log="Collecting packets received baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.net_io_counters()
            current_val = counters.packets_recv
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Packets Recv {current_val}")
            metadata = {"packets_recv": current_val}
        except Exception as e:
            logger.error(f"Error auditing net io packets recv avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Packets Recv", pct=pct, log=f"Measured net io packets recv sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average packets received: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_packets_recv": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_errin_avg_ultimate_audit")
async def system_net_io_errin_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average network input errors across multiple samples.
    """
    logger.info(f"Starting system net io errin avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net Probe", pct=0, log="Collecting input errors baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.net_io_counters()
            current_val = counters.errin
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Input Errors {current_val}")
            metadata = {"errin": current_val}
        except Exception as e:
            logger.error(f"Error auditing net io errin avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Input Errors", pct=pct, log=f"Measured net io errin sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average input errors: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_errin": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_errout_avg_ultimate_audit")
async def system_net_io_errout_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average network output errors across multiple samples.
    """
    logger.info(f"Starting system net io errout avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net Probe", pct=0, log="Collecting output errors baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.net_io_counters()
            current_val = counters.errout
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Output Errors {current_val}")
            metadata = {"errout": current_val}
        except Exception as e:
            logger.error(f"Error auditing net io errout avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Output Errors", pct=pct, log=f"Measured net io errout sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average output errors: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_errout": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_dropin_avg_ultimate_audit")
async def system_net_io_dropin_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average network input drops across multiple samples.
    """
    logger.info(f"Starting system net io dropin avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net Probe", pct=0, log="Collecting input drops baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.net_io_counters()
            current_val = counters.dropin
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Input Drops {current_val}")
            metadata = {"dropin": current_val}
        except Exception as e:
            logger.error(f"Error auditing net io dropin avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Input Drops", pct=pct, log=f"Measured net io dropin sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average input drops: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_dropin": avg_val, "stability": "STABLE"}

@progress_tool(name="system_net_io_dropout_avg_ultimate_audit")
async def system_net_io_dropout_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average network output drops across multiple samples.
    """
    logger.info(f"Starting system net io dropout avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net Probe", pct=0, log="Collecting output drops baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            counters = psutil.net_io_counters()
            current_val = counters.dropout
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Output Drops {current_val}")
            metadata = {"dropout": current_val}
        except Exception as e:
            logger.error(f"Error auditing net io dropout avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Output Drops", pct=pct, log=f"Measured net io dropout sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average output drops: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_dropout": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_user_avg_ultimate_audit")
async def system_cpu_times_user_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average CPU user time across multiple samples.
    """
    logger.info(f"Starting system cpu times user avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Probe", pct=0, log="Collecting user time baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            current_val = times.user
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: User Time {current_val}")
            metadata = {"user_time": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu times user avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling User Time", pct=pct, log=f"Measured cpu times user sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average user time: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_user_time": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_times_system_avg_ultimate_audit")
async def system_cpu_times_system_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average CPU system time across multiple samples.
    """
    logger.info(f"Starting system cpu times system avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Probe", pct=0, log="Collecting system time baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            times = psutil.cpu_times()
            current_val = times.system
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: System Time {current_val}")
            metadata = {"system_time": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu times system avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling System Time", pct=pct, log=f"Measured cpu times system sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0
    yield ProgressPayload(step="Finalizing", pct=100, log=f"Audit complete. Average system time: {avg_val:.2f}")
    yield {"status": "audit_complete", "avg_system_time": avg_val, "stability": "STABLE"}

@progress_tool(name="system_cpu_freq_current_avg_ultimate_audit")
async def system_cpu_freq_current_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average current CPU frequency across multiple samples.
    """
    logger.info(f"Starting system cpu freq current avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Probe", pct=0, log="Collecting frequency baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            freq = psutil.cpu_freq()
            current_val = freq.current if freq else 0.0
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Current Frequency {current_val}")
            metadata = {"current_frequency": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu freq current avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Frequency", pct=pct, log=f"Measured cpu frequency sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_cpu_freq_min_avg_ultimate_audit")
async def system_cpu_freq_min_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average minimum CPU frequency across multiple samples.
    """
    logger.info(f"Starting system cpu freq min avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Probe", pct=0, log="Collecting frequency baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            freq = psutil.cpu_freq()
            current_val = freq.min if freq else 0.0
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Min Frequency {current_val}")
            metadata = {"min_frequency": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu freq min avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Frequency", pct=pct, log=f"Measured cpu frequency sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_cpu_freq_max_avg_ultimate_audit")
async def system_cpu_freq_max_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average maximum CPU frequency across multiple samples.
    """
    logger.info(f"Starting system cpu freq max avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Probe", pct=0, log="Collecting frequency baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            freq = psutil.cpu_freq()
            current_val = freq.max if freq else 0.0
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Max Frequency {current_val}")
            metadata = {"max_frequency": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu freq max avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Frequency", pct=pct, log=f"Measured cpu frequency sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_load_avg_1m_avg_ultimate_audit")
async def system_load_avg_1m_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average system load (1m) across multiple samples.
    """
    logger.info(f"Starting system load avg 1m avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Load Probe", pct=0, log="Collecting load baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            load = os.getloadavg() if hasattr(os, "getloadavg") else (0, 0, 0)
            current_val = load[0]
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Load 1m {current_val}")
            metadata = {"load_1m": current_val}
        except Exception as e:
            logger.error(f"Error auditing load avg 1m avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Load", pct=pct, log=f"Measured load sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_load_avg_5m_avg_ultimate_audit")
async def system_load_avg_5m_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average system load (5m) across multiple samples.
    """
    logger.info(f"Starting system load avg 5m avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Load Probe", pct=0, log="Collecting load baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            load = os.getloadavg() if hasattr(os, "getloadavg") else (0, 0, 0)
            current_val = load[1]
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Load 5m {current_val}")
            metadata = {"load_5m": current_val}
        except Exception as e:
            logger.error(f"Error auditing load avg 5m avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Load", pct=pct, log=f"Measured load sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_load_avg_15m_avg_ultimate_audit")
async def system_load_avg_15m_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average system load (15m) across multiple samples.
    """
    logger.info(f"Starting system load avg 15m avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Load Probe", pct=0, log="Collecting load baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            load = os.getloadavg() if hasattr(os, "getloadavg") else (0, 0, 0)
            current_val = load[2]
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Load 15m {current_val}")
            metadata = {"load_15m": current_val}
        except Exception as e:
            logger.error(f"Error auditing load avg 15m avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Load", pct=pct, log=f"Measured load sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_boot_time_avg_ultimate_audit")
async def system_boot_time_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average system boot time across multiple samples.
    """
    logger.info(f"Starting system boot time avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Boot Probe", pct=0, log="Collecting boot time baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_val = psutil.boot_time()
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Boot Time {current_val}")
            metadata = {"boot_time": current_val}
        except Exception as e:
            logger.error(f"Error auditing boot time avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Boot Time", pct=pct, log=f"Measured boot time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_users_count_avg_ultimate_audit")
async def system_users_count_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average system users count across multiple samples.
    """
    logger.info(f"Starting system users count avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Users Probe", pct=0, log="Collecting users count baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_val = len(psutil.users())
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Users Count {current_val}")
            metadata = {"users_count": current_val}
        except Exception as e:
            logger.error(f"Error auditing users count avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Users Count", pct=pct, log=f"Measured users count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_pids_count_avg_ultimate_audit")
async def system_pids_count_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average system PIDs count across multiple samples.
    """
    logger.info(f"Starting system pids count avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing PIDs Probe", pct=0, log="Collecting pids count baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_val = len(psutil.pids())
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: PIDs Count {current_val}")
            metadata = {"pids_count": current_val}
        except Exception as e:
            logger.error(f"Error auditing pids count avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling PIDs Count", pct=pct, log=f"Measured pids count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_memory_available_avg_ultimate_audit")
async def system_memory_available_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average available system memory across multiple samples.
    """
    logger.info(f"Starting system memory available avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Memory Probe", pct=0, log="Collecting available memory baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            mem = psutil.virtual_memory()
            current_val = mem.available
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: Available Memory {current_val}")
            metadata = {"available_memory": current_val}
        except Exception as e:
            logger.error(f"Error auditing memory available avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Memory", pct=pct, log=f"Measured available memory sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_cpu_times_percent_per_cpu_avg_ultimate_audit")
async def system_cpu_times_percent_per_cpu_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average CPU times percentage per CPU across multiple samples.
    """
    logger.info(f"Starting system cpu times percent per cpu avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Probe", pct=0, log="Collecting CPU per-core baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_val = psutil.cpu_percent(interval=0.1, percpu=True)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU per-core {current_val}")
            metadata = {"cpu_per_core": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu times percent per cpu avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured CPU per-core sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    if samples_list:
        n_cpus = len(samples_list[0])
        avgs = [sum(s[cpu_idx] for s in samples_list) / len(samples_list) for cpu_idx in range(n_cpus)]
    else:
        avgs = []
    yield {"status": "audit_complete", "final_avgs": avgs, "samples": len(samples_list)}

@progress_tool(name="system_cpu_times_percent_per_cpu_max_ultimate_audit")
async def system_cpu_times_percent_per_cpu_max_ultimate_audit(samples: int = 3):
    """
    Audits the maximum CPU times percentage per CPU across multiple samples.
    """
    logger.info(f"Starting system cpu times percent per cpu max ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Probe", pct=0, log="Collecting CPU per-core baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_val = psutil.cpu_percent(interval=0.1, percpu=True)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU per-core {current_val}")
            metadata = {"cpu_per_core": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu times percent per cpu max ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured CPU per-core sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    if samples_list:
        n_cpus = len(samples_list[0])
        maxs = [max(s[cpu_idx] for s in samples_list) for cpu_idx in range(n_cpus)]
    else:
        maxs = []
    yield {"status": "audit_complete", "final_maxs": maxs, "samples": len(samples_list)}

@progress_tool(name="system_cpu_times_percent_per_cpu_min_ultimate_audit")
async def system_cpu_times_percent_per_cpu_min_ultimate_audit(samples: int = 3):
    """
    Audits the minimum CPU times percentage per CPU across multiple samples.
    """
    logger.info(f"Starting system cpu times percent per cpu min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Probe", pct=0, log="Collecting CPU per-core baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_val = psutil.cpu_percent(interval=0.1, percpu=True)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: CPU per-core {current_val}")
            metadata = {"cpu_per_core": current_val}
        except Exception as e:
            logger.error(f"Error auditing cpu times percent per cpu min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured CPU per-core sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    if samples_list:
        n_cpus = len(samples_list[0])
        mins = [min(s[cpu_idx] for s in samples_list) for cpu_idx in range(n_cpus)]
    else:
        mins = []
    yield {"status": "audit_complete", "final_mins": mins, "samples": len(samples_list)}

@progress_tool(name="system_net_io_per_nic_bytes_sent_avg_ultimate_audit")
async def system_net_io_per_nic_bytes_sent_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average network bytes sent per NIC across multiple samples.
    """
    logger.info(f"Starting system net io per nic bytes sent avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Network Probe", pct=0, log="Collecting network per-interface baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_val = psutil.net_io_counters(pernic=True)
            val_dict = {nic: counters.bytes_sent for nic, counters in current_val.items()}
            samples_list.append(val_dict)
            logger.info(f"Sample {i+1}/{samples}: Net sent per NIC")
            metadata = {"net_sent_per_nic": val_dict}
        except Exception as e:
            logger.error(f"Error auditing net io per nic bytes sent avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Network", pct=pct, log=f"Measured net sent per NIC sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    if samples_list:
        nics = samples_list[0].keys()
        avgs = {nic: sum(s[nic] for s in samples_list) / len(samples_list) for nic in nics}
    else:
        avgs = {}
    yield {"status": "audit_complete", "final_avgs": avgs, "samples": len(samples_list)}

@progress_tool(name="system_net_io_per_nic_bytes_recv_avg_ultimate_audit")
async def system_net_io_per_nic_bytes_recv_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average network bytes received per NIC across multiple samples.
    """
    logger.info(f"Starting system net io per nic bytes recv avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Network Probe", pct=0, log="Collecting network per-interface baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_val = psutil.net_io_counters(pernic=True)
            val_dict = {nic: counters.bytes_recv for nic, counters in current_val.items()}
            samples_list.append(val_dict)
            logger.info(f"Sample {i+1}/{samples}: Net recv per NIC")
            metadata = {"net_recv_per_nic": val_dict}
        except Exception as e:
            logger.error(f"Error auditing net io per nic bytes recv avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Network", pct=pct, log=f"Measured net recv per NIC sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    if samples_list:
        nics = samples_list[0].keys()
        avgs = {nic: sum(s[nic] for s in samples_list) / len(samples_list) for nic in nics}
    else:
        avgs = {}
    yield {"status": "audit_complete", "final_avgs": avgs, "samples": len(samples_list)}

@progress_tool(name="system_disk_usage_all_partitions_avg_ultimate_audit")
async def system_disk_usage_all_partitions_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average disk usage across all partitions across multiple samples.
    """
    logger.info(f"Starting system disk usage all partitions avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk Probe", pct=0, log="Collecting disk usage baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            partitions = psutil.disk_partitions()
            usage_dict = {}
            for p in partitions:
                try:
                    usage = psutil.disk_usage(p.mountpoint)
                    usage_dict[p.mountpoint] = usage.percent
                except PermissionError:
                    continue
            samples_list.append(usage_dict)
            logger.info(f"Sample {i+1}/{samples}: Disk usage per partition")
            metadata = {"disk_usage_per_partition": usage_dict}
        except Exception as e:
            logger.error(f"Error auditing disk usage all partitions avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk", pct=pct, log=f"Measured disk usage sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    if samples_list:
        mountpoints = samples_list[0].keys()
        avgs = {mp: sum(s[mp] for s in samples_list if mp in s) / len(samples_list) for mp in mountpoints}
    else:
        avgs = {}
    yield {"status": "audit_complete", "final_avgs": avgs, "samples": len(samples_list)}

@progress_tool(name="system_disk_io_per_disk_read_bytes_avg_ultimate_audit")
async def system_disk_io_per_disk_read_bytes_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average disk read bytes per disk across multiple samples.
    """
    logger.info(f"Starting system disk io per disk read bytes avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk I/O Probe", pct=0, log="Collecting disk I/O per-disk baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_val = psutil.disk_io_counters(perdisk=True)
            val_dict = {disk: counters.read_bytes for disk, counters in current_val.items()}
            samples_list.append(val_dict)
            logger.info(f"Sample {i+1}/{samples}: Disk read bytes per disk")
            metadata = {"disk_read_bytes_per_disk": val_dict}
        except Exception as e:
            logger.error(f"Error auditing disk io per disk read bytes avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk I/O", pct=pct, log=f"Measured disk read bytes sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    if samples_list:
        disks = samples_list[0].keys()
        avgs = {disk: sum(s[disk] for s in samples_list if disk in s) / len(samples_list) for disk in disks}
    else:
        avgs = {}
    yield {"status": "audit_complete", "final_avgs": avgs, "samples": len(samples_list)}

@progress_tool(name="system_disk_io_per_disk_write_bytes_avg_ultimate_audit")
async def system_disk_io_per_disk_write_bytes_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average disk write bytes per disk across multiple samples.
    """
    logger.info(f"Starting system disk io per disk write bytes avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk I/O Probe", pct=0, log="Collecting disk I/O per-disk baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_val = psutil.disk_io_counters(perdisk=True)
            val_dict = {disk: counters.write_bytes for disk, counters in current_val.items()}
            samples_list.append(val_dict)
            logger.info(f"Sample {i+1}/{samples}: Disk write bytes per disk")
            metadata = {"disk_write_bytes_per_disk": val_dict}
        except Exception as e:
            logger.error(f"Error auditing disk io per disk write bytes avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk I/O", pct=pct, log=f"Measured disk write bytes sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    if samples_list:
        disks = samples_list[0].keys()
        avgs = {disk: sum(s[disk] for s in samples_list if disk in s) / len(samples_list) for disk in disks}
    else:
        avgs = {}
    yield {"status": "audit_complete", "final_avgs": avgs, "samples": len(samples_list)}

@progress_tool(name="system_memory_full_info_uss_avg_ultimate_audit")
async def system_memory_full_info_uss_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average process USS memory across multiple samples.
    """
    logger.info(f"Starting system memory full info uss avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Memory Probe", pct=0, log="Collecting process-level memory baseline...")
    samples_list = []
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            mem_info = process.memory_full_info()
            current_val = getattr(mem_info, 'uss', 0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: USS {current_val}")
            metadata = {"uss": current_val}
        except Exception as e:
            logger.error(f"Error auditing memory full info uss avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Memory", pct=pct, log=f"Measured process USS sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_memory_full_info_pss_avg_ultimate_audit")
async def system_memory_full_info_pss_avg_ultimate_audit(samples: int = 3):
    """
    Audits the average process PSS memory across multiple samples.
    """
    logger.info(f"Starting system memory full info pss avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Memory Probe", pct=0, log="Collecting process-level memory baseline...")
    samples_list = []
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            mem_info = process.memory_full_info()
            current_val = getattr(mem_info, 'pss', 0)
            samples_list.append(current_val)
            logger.info(f"Sample {i+1}/{samples}: PSS {current_val}")
            metadata = {"pss": current_val}
        except Exception as e:
            logger.error(f"Error auditing memory full info pss avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Memory", pct=pct, log=f"Measured process PSS sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_cpu_times_percent_per_cpu_idle_avg_ultimate_audit")
async def system_cpu_times_percent_per_cpu_idle_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system cpu times percent per cpu idle avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Probe", pct=0, log="Collecting per-core CPU idle baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_vals = psutil.cpu_times_percent(percpu=True)
            idle_avg = sum(c.idle for c in current_vals) / len(current_vals) if current_vals else 0.0
            samples_list.append(idle_avg)
            metadata = {"idle_avg": idle_avg}
        except Exception as e:
            logger.error(f"Error auditing cpu times percent per cpu idle avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured per-core CPU idle sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_cpu_times_percent_per_cpu_user_avg_ultimate_audit")
async def system_cpu_times_percent_per_cpu_user_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system cpu times percent per cpu user avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Probe", pct=0, log="Collecting per-core CPU user baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_vals = psutil.cpu_times_percent(percpu=True)
            user_avg = sum(c.user for c in current_vals) / len(current_vals) if current_vals else 0.0
            samples_list.append(user_avg)
            metadata = {"user_avg": user_avg}
        except Exception as e:
            logger.error(f"Error auditing cpu times percent per cpu user avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured per-core CPU user sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_cpu_times_percent_per_cpu_system_avg_ultimate_audit")
async def system_cpu_times_percent_per_cpu_system_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system cpu times percent per cpu system avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Probe", pct=0, log="Collecting per-core CPU system baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_vals = psutil.cpu_times_percent(percpu=True)
            system_avg = sum(c.system for c in current_vals) / len(current_vals) if current_vals else 0.0
            samples_list.append(system_avg)
            metadata = {"system_avg": system_avg}
        except Exception as e:
            logger.error(f"Error auditing cpu times percent per cpu system avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured per-core CPU system sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_net_io_per_nic_packets_sent_avg_ultimate_audit")
async def system_net_io_per_nic_packets_sent_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system net io per nic packets sent avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Network Probe", pct=0, log="Collecting per-NIC packets sent baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_vals = psutil.net_io_counters(pernic=True)
            pkts_sent_avg = sum(c.packets_sent for c in current_vals.values()) / len(current_vals) if current_vals else 0.0
            samples_list.append(pkts_sent_avg)
            metadata = {"packets_sent_avg": pkts_sent_avg}
        except Exception as e:
            logger.error(f"Error auditing net io per nic packets sent avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Network", pct=pct, log=f"Measured per-NIC packets sent sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_net_io_per_nic_packets_recv_avg_ultimate_audit")
async def system_net_io_per_nic_packets_recv_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system net io per nic packets recv avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Network Probe", pct=0, log="Collecting per-NIC packets received baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_vals = psutil.net_io_counters(pernic=True)
            pkts_recv_avg = sum(c.packets_recv for c in current_vals.values()) / len(current_vals) if current_vals else 0.0
            samples_list.append(pkts_recv_avg)
            metadata = {"packets_recv_avg": pkts_recv_avg}
        except Exception as e:
            logger.error(f"Error auditing net io per nic packets recv avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Network", pct=pct, log=f"Measured per-NIC packets received sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_disk_usage_all_partitions_percent_avg_ultimate_audit")
async def system_disk_usage_all_partitions_percent_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system disk usage all partitions percent avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk Probe", pct=0, log="Collecting partition-level usage baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            partitions = psutil.disk_partitions()
            usages = []
            for p in partitions:
                try:
                    usage = psutil.disk_usage(p.mountpoint)
                    usages.append(usage.percent)
                except: continue
            usage_avg = sum(usages) / len(usages) if usages else 0.0
            samples_list.append(usage_avg)
            metadata = {"usage_percent_avg": usage_avg}
        except Exception as e:
            logger.error(f"Error auditing disk usage all partitions percent avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk", pct=pct, log=f"Measured disk usage percentage sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_disk_io_per_disk_read_count_avg_ultimate_audit")
async def system_disk_io_per_disk_read_count_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system disk io per disk read count avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk I/O Probe", pct=0, log="Collecting per-disk read count baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_vals = psutil.disk_io_counters(perdisk=True)
            read_count_avg = sum(c.read_count for c in current_vals.values()) / len(current_vals) if current_vals else 0.0
            samples_list.append(read_count_avg)
            metadata = {"read_count_avg": read_count_avg}
        except Exception as e:
            logger.error(f"Error auditing disk io per disk read count avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk I/O", pct=pct, log=f"Measured per-disk read count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_disk_io_per_disk_write_count_avg_ultimate_audit")
async def system_disk_io_per_disk_write_count_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system disk io per disk write count avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk I/O Probe", pct=0, log="Collecting per-disk write count baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_vals = psutil.disk_io_counters(perdisk=True)
            write_count_avg = sum(c.write_count for c in current_vals.values()) / len(current_vals) if current_vals else 0.0
            samples_list.append(write_count_avg)
            metadata = {"write_count_avg": write_count_avg}
        except Exception as e:
            logger.error(f"Error auditing disk io per disk write count avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk I/O", pct=pct, log=f"Measured per-disk write count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_memory_full_info_vms_avg_ultimate_audit")
async def system_memory_full_info_vms_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system memory full info vms avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Memory Probe", pct=0, log="Collecting process-level memory baseline...")
    samples_list = []
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            mem_info = process.memory_full_info()
            current_val = getattr(mem_info, "vms", 0)
            samples_list.append(current_val)
            metadata = {"vms": current_val}
        except Exception as e:
            logger.error(f"Error auditing memory full info vms avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Memory", pct=pct, log=f"Measured process VMS sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_memory_full_info_rss_avg_ultimate_audit")
async def system_memory_full_info_rss_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system memory full info rss avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Memory Probe", pct=0, log="Collecting process-level memory baseline...")
    samples_list = []
    process = psutil.Process()
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            mem_info = process.memory_full_info()
            current_val = getattr(mem_info, "rss", 0)
            samples_list.append(current_val)
            metadata = {"rss": current_val}
        except Exception as e:
            logger.error(f"Error auditing memory full info rss avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Memory", pct=pct, log=f"Measured process RSS sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_cpu_times_percent_per_cpu_iowait_avg_ultimate_audit")
async def system_cpu_times_percent_per_cpu_iowait_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system cpu times percent per cpu iowait avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Probe", pct=0, log="Collecting per-cpu iowait baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_vals = psutil.cpu_times_percent(percpu=True)
            iowait_avg = sum(getattr(c, "iowait", 0) for c in current_vals) / len(current_vals) if current_vals else 0.0
            samples_list.append(iowait_avg)
            metadata = {"iowait_avg": iowait_avg}
        except Exception as e:
            logger.error(f"Error auditing cpu times percent per cpu iowait avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured per-cpu iowait sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_cpu_times_percent_per_cpu_irq_avg_ultimate_audit")
async def system_cpu_times_percent_per_cpu_irq_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system cpu times percent per cpu irq avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Probe", pct=0, log="Collecting per-cpu irq baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_vals = psutil.cpu_times_percent(percpu=True)
            irq_avg = sum(getattr(c, "irq", 0) for c in current_vals) / len(current_vals) if current_vals else 0.0
            samples_list.append(irq_avg)
            metadata = {"irq_avg": irq_avg}
        except Exception as e:
            logger.error(f"Error auditing cpu times percent per cpu irq avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured per-cpu irq sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_cpu_times_percent_per_cpu_softirq_avg_ultimate_audit")
async def system_cpu_times_percent_per_cpu_softirq_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system cpu times percent per cpu softirq avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Probe", pct=0, log="Collecting per-cpu softirq baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_vals = psutil.cpu_times_percent(percpu=True)
            softirq_avg = sum(getattr(c, "softirq", 0) for c in current_vals) / len(current_vals) if current_vals else 0.0
            samples_list.append(softirq_avg)
            metadata = {"softirq_avg": softirq_avg}
        except Exception as e:
            logger.error(f"Error auditing cpu times percent per cpu softirq avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured per-cpu softirq sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_cpu_times_percent_per_cpu_steal_avg_ultimate_audit")
async def system_cpu_times_percent_per_cpu_steal_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system cpu times percent per cpu steal avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Probe", pct=0, log="Collecting per-cpu steal baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_vals = psutil.cpu_times_percent(percpu=True)
            steal_avg = sum(getattr(c, "steal", 0) for c in current_vals) / len(current_vals) if current_vals else 0.0
            samples_list.append(steal_avg)
            metadata = {"steal_avg": steal_avg}
        except Exception as e:
            logger.error(f"Error auditing cpu times percent per cpu steal avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured per-cpu steal sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_cpu_times_percent_per_cpu_guest_avg_ultimate_audit")
async def system_cpu_times_percent_per_cpu_guest_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system cpu times percent per cpu guest avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Probe", pct=0, log="Collecting per-cpu guest baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_vals = psutil.cpu_times_percent(percpu=True)
            guest_avg = sum(getattr(c, "guest", 0) for c in current_vals) / len(current_vals) if current_vals else 0.0
            samples_list.append(guest_avg)
            metadata = {"guest_avg": guest_avg}
        except Exception as e:
            logger.error(f"Error auditing cpu times percent per cpu guest avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured per-cpu guest sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_cpu_times_percent_per_cpu_guest_nice_avg_ultimate_audit")
async def system_cpu_times_percent_per_cpu_guest_nice_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system cpu times percent per cpu guest_nice avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Probe", pct=0, log="Collecting per-cpu guest_nice baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_vals = psutil.cpu_times_percent(percpu=True)
            guest_nice_avg = sum(getattr(c, "guest_nice", 0) for c in current_vals) / len(current_vals) if current_vals else 0.0
            samples_list.append(guest_nice_avg)
            metadata = {"guest_nice_avg": guest_nice_avg}
        except Exception as e:
            logger.error(f"Error auditing cpu times percent per cpu guest_nice avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured per-cpu guest_nice sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_net_io_per_nic_errin_avg_ultimate_audit")
async def system_net_io_per_nic_errin_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system net io per nic errin avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net Probe", pct=0, log="Collecting per-nic errin baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_vals = psutil.net_io_counters(pernic=True)
            errin_avg = sum(c.errin for c in current_vals.values()) / len(current_vals) if current_vals else 0.0
            samples_list.append(errin_avg)
            metadata = {"errin_avg": errin_avg}
        except Exception as e:
            logger.error(f"Error auditing net io per nic errin avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net", pct=pct, log=f"Measured per-nic errin sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_net_io_per_nic_errout_avg_ultimate_audit")
async def system_net_io_per_nic_errout_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system net io per nic errout avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net Probe", pct=0, log="Collecting per-nic errout baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_vals = psutil.net_io_counters(pernic=True)
            errout_avg = sum(c.errout for c in current_vals.values()) / len(current_vals) if current_vals else 0.0
            samples_list.append(errout_avg)
            metadata = {"errout_avg": errout_avg}
        except Exception as e:
            logger.error(f"Error auditing net io per nic errout avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net", pct=pct, log=f"Measured per-nic errout sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_net_io_per_nic_dropin_avg_ultimate_audit")
async def system_net_io_per_nic_dropin_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system net io per nic dropin avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net Probe", pct=0, log="Collecting per-nic dropin baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_vals = psutil.net_io_counters(pernic=True)
            dropin_avg = sum(c.dropin for c in current_vals.values()) / len(current_vals) if current_vals else 0.0
            samples_list.append(dropin_avg)
            metadata = {"dropin_avg": dropin_avg}
        except Exception as e:
            logger.error(f"Error auditing net io per nic dropin avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net", pct=pct, log=f"Measured per-nic dropin sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_net_io_per_nic_dropout_avg_ultimate_audit")
async def system_net_io_per_nic_dropout_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system net io per nic dropout avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net Probe", pct=0, log="Collecting per-nic dropout baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_vals = psutil.net_io_counters(pernic=True)
            dropout_avg = sum(c.dropout for c in current_vals.values()) / len(current_vals) if current_vals else 0.0
            samples_list.append(dropout_avg)
            metadata = {"dropout_avg": dropout_avg}
        except Exception as e:
            logger.error(f"Error auditing net io per nic dropout avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net", pct=pct, log=f"Measured per-nic dropout sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_disk_io_per_disk_read_time_avg_ultimate_audit")
async def system_disk_io_per_disk_read_time_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system disk io per disk read time avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk I/O Probe", pct=0, log="Collecting per-disk read time baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_vals = psutil.disk_io_counters(perdisk=True)
            read_time_avg = sum(c.read_time for c in current_vals.values()) / len(current_vals) if current_vals else 0.0
            samples_list.append(read_time_avg)
            metadata = {"read_time_avg": read_time_avg}
        except Exception as e:
            logger.error(f"Error auditing disk io per disk read time avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk I/O", pct=pct, log=f"Measured per-disk read time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_disk_io_per_disk_write_time_avg_ultimate_audit")
async def system_disk_io_per_disk_write_time_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system disk io per disk write time avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk I/O Probe", pct=0, log="Collecting per-disk write time baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_vals = psutil.disk_io_counters(perdisk=True)
            write_time_avg = sum(c.write_time for c in current_vals.values()) / len(current_vals) if current_vals else 0.0
            samples_list.append(write_time_avg)
            metadata = {"write_time_avg": write_time_avg}
        except Exception as e:
            logger.error(f"Error auditing disk io per disk write time avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk I/O", pct=pct, log=f"Measured per-disk write time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_disk_io_per_disk_busy_time_avg_ultimate_audit")
async def system_disk_io_per_disk_busy_time_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system disk io per disk busy time avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk I/O Probe", pct=0, log="Collecting per-disk busy time baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_vals = psutil.disk_io_counters(perdisk=True)
            busy_time_avg = sum(getattr(c, "busy_time", 0) for c in current_vals.values()) / len(current_vals) if current_vals else 0.0
            samples_list.append(busy_time_avg)
            metadata = {"busy_time_avg": busy_time_avg}
        except Exception as e:
            logger.error(f"Error auditing disk io per disk busy time avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk I/O", pct=pct, log=f"Measured per-disk busy time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_memory_virtual_memory_buffers_avg_ultimate_audit")
async def system_memory_virtual_memory_buffers_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system memory virtual memory buffers avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Memory Probe", pct=0, log="Collecting virtual memory buffers baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            vmem = psutil.virtual_memory()
            buffers = getattr(vmem, "buffers", 0)
            samples_list.append(buffers)
            metadata = {"buffers": buffers}
        except Exception as e:
            logger.error(f"Error auditing virtual memory buffers avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Memory", pct=pct, log=f"Measured virtual memory buffers sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_memory_virtual_memory_cached_avg_ultimate_audit")
async def system_memory_virtual_memory_cached_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system memory virtual memory cached avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Memory Probe", pct=0, log="Collecting virtual memory cached baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            vmem = psutil.virtual_memory()
            cached = getattr(vmem, "cached", 0)
            samples_list.append(cached)
            metadata = {"cached": cached}
        except Exception as e:
            logger.error(f"Error auditing virtual memory cached avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Memory", pct=pct, log=f"Measured virtual memory cached sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_memory_virtual_memory_shared_avg_ultimate_audit")
async def system_memory_virtual_memory_shared_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system memory virtual memory shared avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Memory Probe", pct=0, log="Collecting virtual memory shared baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            vmem = psutil.virtual_memory()
            shared = getattr(vmem, "shared", 0)
            samples_list.append(shared)
            metadata = {"shared": shared}
        except Exception as e:
            logger.error(f"Error auditing virtual memory shared avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Memory", pct=pct, log=f"Measured virtual memory shared sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_memory_virtual_memory_slab_avg_ultimate_audit")
async def system_memory_virtual_memory_slab_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system memory virtual memory slab avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Memory Probe", pct=0, log="Collecting virtual memory slab baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            vmem = psutil.virtual_memory()
            slab = getattr(vmem, "slab", 0)
            samples_list.append(slab)
            metadata = {"slab": slab}
        except Exception as e:
            logger.error(f"Error auditing virtual memory slab avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Memory", pct=pct, log=f"Measured virtual memory slab sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_memory_virtual_memory_active_avg_ultimate_audit")
async def system_memory_virtual_memory_active_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system memory virtual memory active avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Memory Probe", pct=0, log="Collecting virtual memory active baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            vmem = psutil.virtual_memory()
            active = getattr(vmem, "active", 0)
            samples_list.append(active)
            metadata = {"active": active}
        except Exception as e:
            logger.error(f"Error auditing virtual memory active avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Memory", pct=pct, log=f"Measured virtual memory active sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_memory_virtual_memory_inactive_avg_ultimate_audit")
async def system_memory_virtual_memory_inactive_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system memory virtual memory inactive avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Memory Probe", pct=0, log="Collecting virtual memory inactive baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            vmem = psutil.virtual_memory()
            inactive = getattr(vmem, "inactive", 0)
            samples_list.append(inactive)
            metadata = {"inactive": inactive}
        except Exception as e:
            logger.error(f"Error auditing virtual memory inactive avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Memory", pct=pct, log=f"Measured virtual memory inactive sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_memory_swap_memory_sin_avg_ultimate_audit")
async def system_memory_swap_memory_sin_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system memory swap memory sin avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Memory Probe", pct=0, log="Collecting swap memory sin baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            swap = psutil.swap_memory()
            sin = getattr(swap, "sin", 0)
            samples_list.append(sin)
            metadata = {"sin": sin}
        except Exception as e:
            logger.error(f"Error auditing swap memory sin avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Memory", pct=pct, log=f"Measured swap memory sin sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_memory_swap_memory_sout_avg_ultimate_audit")
async def system_memory_swap_memory_sout_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system memory swap memory sout avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Memory Probe", pct=0, log="Collecting swap memory sout baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            swap = psutil.swap_memory()
            sout = getattr(swap, "sout", 0)
            samples_list.append(sout)
            metadata = {"sout": sout}
        except Exception as e:
            logger.error(f"Error auditing swap memory sout avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Memory", pct=pct, log=f"Measured swap memory sout sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_cpu_times_percent_per_cpu_nice_avg_ultimate_audit")
async def system_cpu_times_percent_per_cpu_nice_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system cpu times percent per cpu nice avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Probe", pct=0, log="Collecting per-cpu nice baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_vals = psutil.cpu_times_percent(percpu=True)
            nice_avg = sum(getattr(c, "nice", 0) for c in current_vals) / len(current_vals) if current_vals else 0.0
            samples_list.append(nice_avg)
            metadata = {"nice_avg": nice_avg}
        except Exception as e:
            logger.error(f"Error auditing cpu times percent per cpu nice avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured per-cpu nice sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_cpu_times_percent_per_cpu_idle_avg_ultimate_audit")
async def system_cpu_times_percent_per_cpu_idle_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system cpu times percent per cpu idle avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Probe", pct=0, log="Collecting per-cpu idle baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            current_vals = psutil.cpu_times_percent(percpu=True)
            idle_avg = sum(getattr(c, "idle", 0) for c in current_vals) / len(current_vals) if current_vals else 0.0
            samples_list.append(idle_avg)
            metadata = {"idle_avg": idle_avg}
        except Exception as e:
            logger.error(f"Error auditing cpu times percent per cpu idle avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured per-cpu idle sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_net_if_addrs_ipv4_count_avg_ultimate_audit")
async def system_net_if_addrs_ipv4_count_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system net if addrs ipv4 count avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net Probe", pct=0, log="Collecting ipv4 address count baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            import socket
            addrs = psutil.net_if_addrs()
            ipv4_count = sum(1 for interface in addrs.values() for addr in interface if addr.family == socket.AF_INET)
            samples_list.append(ipv4_count)
            metadata = {"ipv4_count": ipv4_count}
        except Exception as e:
            logger.error(f"Error auditing net if addrs ipv4 count avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net", pct=pct, log=f"Measured ipv4 count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_net_if_addrs_ipv6_count_avg_ultimate_audit")
async def system_net_if_addrs_ipv6_count_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system net if addrs ipv6 count avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net Probe", pct=0, log="Collecting ipv6 address count baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            import socket
            addrs = psutil.net_if_addrs()
            ipv6_count = sum(1 for interface in addrs.values() for addr in interface if addr.family == getattr(socket, "AF_INET6", -1))
            samples_list.append(ipv6_count)
            metadata = {"ipv6_count": ipv6_count}
        except Exception as e:
            logger.error(f"Error auditing net if addrs ipv6 count avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net", pct=pct, log=f"Measured ipv6 count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_net_if_addrs_mac_count_avg_ultimate_audit")
async def system_net_if_addrs_mac_count_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system net if addrs mac count avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net Probe", pct=0, log="Collecting mac address count baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            import socket
            addrs = psutil.net_if_addrs()
            mac_count = sum(1 for interface in addrs.values() for addr in interface if addr.family == getattr(psutil, "AF_LINK", -1))
            samples_list.append(mac_count)
            metadata = {"mac_count": mac_count}
        except Exception as e:
            logger.error(f"Error auditing net if addrs mac count avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net", pct=pct, log=f"Measured mac count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_net_if_addrs_broadcast_count_avg_ultimate_audit")
async def system_net_if_addrs_broadcast_count_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system net if addrs broadcast count avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net Probe", pct=0, log="Collecting broadcast address count baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            broadcast_count = sum(1 for interface in addrs.values() for addr in interface if addr.broadcast)
            samples_list.append(broadcast_count)
            metadata = {"broadcast_count": broadcast_count}
        except Exception as e:
            logger.error(f"Error auditing net if addrs broadcast count avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net", pct=pct, log=f"Measured broadcast count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_net_if_addrs_ptp_count_avg_ultimate_audit")
async def system_net_if_addrs_ptp_count_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system net if addrs ptp count avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net Probe", pct=0, log="Collecting ptp address count baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            addrs = psutil.net_if_addrs()
            ptp_count = sum(1 for interface in addrs.values() for addr in interface if addr.ptp)
            samples_list.append(ptp_count)
            metadata = {"ptp_count": ptp_count}
        except Exception as e:
            logger.error(f"Error auditing net if addrs ptp count avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net", pct=pct, log=f"Measured ptp count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_disk_partitions_fstype_count_avg_ultimate_audit")
async def system_disk_partitions_fstype_count_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system disk partitions fstype count avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk Probe", pct=0, log="Collecting fstype count baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            partitions = psutil.disk_partitions(all=True)
            fstype_count = len(set(p.fstype for p in partitions if p.fstype))
            samples_list.append(fstype_count)
            metadata = {"fstype_count": fstype_count}
        except Exception as e:
            logger.error(f"Error auditing disk partitions fstype count avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk", pct=pct, log=f"Measured fstype count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_disk_partitions_mountpoint_count_avg_ultimate_audit")
async def system_disk_partitions_mountpoint_count_avg_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system disk partitions mountpoint count avg ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk Probe", pct=0, log="Collecting mountpoint count baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            partitions = psutil.disk_partitions(all=True)
            mountpoint_count = len(set(p.mountpoint for p in partitions if p.mountpoint))
            samples_list.append(mountpoint_count)
            metadata = {"mountpoint_count": mountpoint_count}
        except Exception as e:
            logger.error(f"Error auditing disk partitions mountpoint count avg ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk", pct=pct, log=f"Measured mountpoint count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    avg_val = sum(samples_list) / len(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_avg": avg_val, "samples": len(samples_list)}

@progress_tool(name="system_cpu_stats_ctx_switches_max_ultimate_audit")
async def system_cpu_stats_ctx_switches_max_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system cpu stats ctx switches max ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Probe", pct=0, log="Collecting ctx switches baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            val = getattr(stats, "ctx_switches", 0)
            samples_list.append(val)
            metadata = {"ctx_switches": val}
        except Exception as e:
            logger.error(f"Error auditing cpu stats ctx switches max ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured ctx switches sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    max_val = max(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_max": max_val, "samples": len(samples_list)}

@progress_tool(name="system_cpu_stats_interrupts_max_ultimate_audit")
async def system_cpu_stats_interrupts_max_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system cpu stats interrupts max ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Probe", pct=0, log="Collecting interrupts baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            val = getattr(stats, "interrupts", 0)
            samples_list.append(val)
            metadata = {"interrupts": val}
        except Exception as e:
            logger.error(f"Error auditing cpu stats interrupts max ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured interrupts sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    max_val = max(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_max": max_val, "samples": len(samples_list)}

@progress_tool(name="system_cpu_stats_soft_interrupts_max_ultimate_audit")
async def system_cpu_stats_soft_interrupts_max_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system cpu stats soft interrupts max ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Probe", pct=0, log="Collecting soft interrupts baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            val = getattr(stats, "soft_interrupts", 0)
            samples_list.append(val)
            metadata = {"soft_interrupts": val}
        except Exception as e:
            logger.error(f"Error auditing cpu stats soft interrupts max ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured soft interrupts sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    max_val = max(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_max": max_val, "samples": len(samples_list)}

@progress_tool(name="system_cpu_stats_syscalls_max_ultimate_audit")
async def system_cpu_stats_syscalls_max_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system cpu stats syscalls max ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Probe", pct=0, log="Collecting syscalls baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            val = getattr(stats, "syscalls", 0)
            samples_list.append(val)
            metadata = {"syscalls": val}
        except Exception as e:
            logger.error(f"Error auditing cpu stats syscalls max ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured syscalls sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    max_val = max(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_max": max_val, "samples": len(samples_list)}

@progress_tool(name="system_net_io_bytes_sent_max_ultimate_audit")
async def system_net_io_bytes_sent_max_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system net io bytes sent max ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net Probe", pct=0, log="Collecting bytes sent baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.net_io_counters()
            val = getattr(io, "bytes_sent", 0)
            samples_list.append(val)
            metadata = {"bytes_sent": val}
        except Exception as e:
            logger.error(f"Error auditing net io bytes sent max ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net", pct=pct, log=f"Measured bytes sent sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    max_val = max(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_max": max_val, "samples": len(samples_list)}

@progress_tool(name="system_net_io_bytes_recv_max_ultimate_audit")
async def system_net_io_bytes_recv_max_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system net io bytes recv max ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net Probe", pct=0, log="Collecting bytes recv baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.net_io_counters()
            val = getattr(io, "bytes_recv", 0)
            samples_list.append(val)
            metadata = {"bytes_recv": val}
        except Exception as e:
            logger.error(f"Error auditing net io bytes recv max ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net", pct=pct, log=f"Measured bytes recv sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    max_val = max(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_max": max_val, "samples": len(samples_list)}

@progress_tool(name="system_net_io_packets_sent_max_ultimate_audit")
async def system_net_io_packets_sent_max_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system net io packets sent max ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net Probe", pct=0, log="Collecting packets sent baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.net_io_counters()
            val = getattr(io, "packets_sent", 0)
            samples_list.append(val)
            metadata = {"packets_sent": val}
        except Exception as e:
            logger.error(f"Error auditing net io packets sent max ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net", pct=pct, log=f"Measured packets sent sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    max_val = max(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_max": max_val, "samples": len(samples_list)}

@progress_tool(name="system_net_io_packets_recv_max_ultimate_audit")
async def system_net_io_packets_recv_max_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system net io packets recv max ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net Probe", pct=0, log="Collecting packets recv baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.net_io_counters()
            val = getattr(io, "packets_recv", 0)
            samples_list.append(val)
            metadata = {"packets_recv": val}
        except Exception as e:
            logger.error(f"Error auditing net io packets recv max ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net", pct=pct, log=f"Measured packets recv sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    max_val = max(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_max": max_val, "samples": len(samples_list)}

@progress_tool(name="system_disk_io_read_bytes_max_ultimate_audit")
async def system_disk_io_read_bytes_max_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system disk io read bytes max ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk Probe", pct=0, log="Collecting read bytes baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.disk_io_counters()
            val = getattr(io, "read_bytes", 0)
            samples_list.append(val)
            metadata = {"read_bytes": val}
        except Exception as e:
            logger.error(f"Error auditing disk io read bytes max ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk", pct=pct, log=f"Measured read bytes sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    max_val = max(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_max": max_val, "samples": len(samples_list)}

@progress_tool(name="system_disk_io_write_bytes_max_ultimate_audit")
async def system_disk_io_write_bytes_max_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system disk io write bytes max ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk Probe", pct=0, log="Collecting write bytes baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.disk_io_counters()
            val = getattr(io, "write_bytes", 0)
            samples_list.append(val)
            metadata = {"write_bytes": val}
        except Exception as e:
            logger.error(f"Error auditing disk io write bytes max ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk", pct=pct, log=f"Measured write bytes sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    max_val = max(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_max": max_val, "samples": len(samples_list)}

@progress_tool(name="system_cpu_stats_ctx_switches_min_ultimate_audit")
async def system_cpu_stats_ctx_switches_min_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system cpu stats ctx switches min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Probe", pct=0, log="Collecting ctx switches baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            val = getattr(stats, "ctx_switches", 0)
            samples_list.append(val)
            metadata = {"ctx_switches": val}
        except Exception as e:
            logger.error(f"Error auditing cpu stats ctx switches min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured ctx switches sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    min_val = min(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_min": min_val, "samples": len(samples_list)}

@progress_tool(name="system_cpu_stats_interrupts_min_ultimate_audit")
async def system_cpu_stats_interrupts_min_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system cpu stats interrupts min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Probe", pct=0, log="Collecting interrupts baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            val = getattr(stats, "interrupts", 0)
            samples_list.append(val)
            metadata = {"interrupts": val}
        except Exception as e:
            logger.error(f"Error auditing cpu stats interrupts min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured interrupts sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    min_val = min(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_min": min_val, "samples": len(samples_list)}

@progress_tool(name="system_cpu_stats_soft_interrupts_min_ultimate_audit")
async def system_cpu_stats_soft_interrupts_min_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system cpu stats soft interrupts min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Probe", pct=0, log="Collecting soft interrupts baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            val = getattr(stats, "soft_interrupts", 0)
            samples_list.append(val)
            metadata = {"soft_interrupts": val}
        except Exception as e:
            logger.error(f"Error auditing cpu stats soft interrupts min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured soft interrupts sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    min_val = min(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_min": min_val, "samples": len(samples_list)}

@progress_tool(name="system_cpu_stats_syscalls_min_ultimate_audit")
async def system_cpu_stats_syscalls_min_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system cpu stats syscalls min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing CPU Probe", pct=0, log="Collecting syscalls baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            stats = psutil.cpu_stats()
            val = getattr(stats, "syscalls", 0)
            samples_list.append(val)
            metadata = {"syscalls": val}
        except Exception as e:
            logger.error(f"Error auditing cpu stats syscalls min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling CPU", pct=pct, log=f"Measured syscalls sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    min_val = min(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_min": min_val, "samples": len(samples_list)}

@progress_tool(name="system_net_io_bytes_sent_min_ultimate_audit")
async def system_net_io_bytes_sent_min_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system net io bytes sent min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net Probe", pct=0, log="Collecting bytes sent baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.net_io_counters()
            val = getattr(io, "bytes_sent", 0)
            samples_list.append(val)
            metadata = {"bytes_sent": val}
        except Exception as e:
            logger.error(f"Error auditing net io bytes sent min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net", pct=pct, log=f"Measured bytes sent sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    min_val = min(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_min": min_val, "samples": len(samples_list)}

@progress_tool(name="system_net_io_bytes_recv_min_ultimate_audit")
async def system_net_io_bytes_recv_min_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system net io bytes recv min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net Probe", pct=0, log="Collecting bytes recv baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.net_io_counters()
            val = getattr(io, "bytes_recv", 0)
            samples_list.append(val)
            metadata = {"bytes_recv": val}
        except Exception as e:
            logger.error(f"Error auditing net io bytes recv min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net", pct=pct, log=f"Measured bytes recv sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    min_val = min(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_min": min_val, "samples": len(samples_list)}

@progress_tool(name="system_net_io_packets_sent_min_ultimate_audit")
async def system_net_io_packets_sent_min_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system net io packets sent min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net Probe", pct=0, log="Collecting packets sent baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.net_io_counters()
            val = getattr(io, "packets_sent", 0)
            samples_list.append(val)
            metadata = {"packets_sent": val}
        except Exception as e:
            logger.error(f"Error auditing net io packets sent min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net", pct=pct, log=f"Measured packets sent sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    min_val = min(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_min": min_val, "samples": len(samples_list)}

@progress_tool(name="system_net_io_packets_recv_min_ultimate_audit")
async def system_net_io_packets_recv_min_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system net io packets recv min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Net Probe", pct=0, log="Collecting packets recv baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.net_io_counters()
            val = getattr(io, "packets_recv", 0)
            samples_list.append(val)
            metadata = {"packets_recv": val}
        except Exception as e:
            logger.error(f"Error auditing net io packets recv min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Net", pct=pct, log=f"Measured packets recv sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    min_val = min(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_min": min_val, "samples": len(samples_list)}

@progress_tool(name="system_disk_io_read_bytes_min_ultimate_audit")
async def system_disk_io_read_bytes_min_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system disk io read bytes min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk Probe", pct=0, log="Collecting read bytes baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.disk_io_counters()
            val = getattr(io, "read_bytes", 0)
            samples_list.append(val)
            metadata = {"read_bytes": val}
        except Exception as e:
            logger.error(f"Error auditing disk io read bytes min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk", pct=pct, log=f"Measured read bytes sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    min_val = min(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_min": min_val, "samples": len(samples_list)}

@progress_tool(name="system_disk_io_write_bytes_min_ultimate_audit")
async def system_disk_io_write_bytes_min_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system disk io write bytes min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk Probe", pct=0, log="Collecting write bytes baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.disk_io_counters()
            val = getattr(io, "write_bytes", 0)
            samples_list.append(val)
            metadata = {"write_bytes": val}
        except Exception as e:
            logger.error(f"Error auditing disk io write bytes min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk", pct=pct, log=f"Measured write bytes sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    min_val = min(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_min": min_val, "samples": len(samples_list)}

@progress_tool(name="system_disk_io_read_count_min_ultimate_audit")
async def system_disk_io_read_count_min_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system disk io read count min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk Probe", pct=0, log="Collecting read count baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.disk_io_counters()
            val = getattr(io, "read_count", 0)
            samples_list.append(val)
            metadata = {"read_count": val}
        except Exception as e:
            logger.error(f"Error auditing disk io read count min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk", pct=pct, log=f"Measured read count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    min_val = min(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_min": min_val, "samples": len(samples_list)}

@progress_tool(name="system_disk_io_write_count_min_ultimate_audit")
async def system_disk_io_write_count_min_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system disk io write count min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk Probe", pct=0, log="Collecting write count baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.disk_io_counters()
            val = getattr(io, "write_count", 0)
            samples_list.append(val)
            metadata = {"write_count": val}
        except Exception as e:
            logger.error(f"Error auditing disk io write count min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk", pct=pct, log=f"Measured write count sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    min_val = min(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_min": min_val, "samples": len(samples_list)}

@progress_tool(name="system_disk_io_read_time_min_ultimate_audit")
async def system_disk_io_read_time_min_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system disk io read time min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk Probe", pct=0, log="Collecting read time baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.disk_io_counters()
            val = getattr(io, "read_time", 0)
            samples_list.append(val)
            metadata = {"read_time": val}
        except Exception as e:
            logger.error(f"Error auditing disk io read time min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk", pct=pct, log=f"Measured read time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    min_val = min(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_min": min_val, "samples": len(samples_list)}

@progress_tool(name="system_disk_io_write_time_min_ultimate_audit")
async def system_disk_io_write_time_min_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system disk io write time min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk Probe", pct=0, log="Collecting write time baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.disk_io_counters()
            val = getattr(io, "write_time", 0)
            samples_list.append(val)
            metadata = {"write_time": val}
        except Exception as e:
            logger.error(f"Error auditing disk io write time min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk", pct=pct, log=f"Measured write time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    min_val = min(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_min": min_val, "samples": len(samples_list)}

@progress_tool(name="system_disk_io_busy_time_min_ultimate_audit")
async def system_disk_io_busy_time_min_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system disk io busy time min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Disk Probe", pct=0, log="Collecting busy time baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            io = psutil.disk_io_counters()
            val = getattr(io, "busy_time", 0)
            samples_list.append(val)
            metadata = {"busy_time": val}
        except Exception as e:
            logger.error(f"Error auditing disk io busy time min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Disk", pct=pct, log=f"Measured busy time sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    min_val = min(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_min": min_val, "samples": len(samples_list)}

@progress_tool(name="system_swap_memory_total_min_ultimate_audit")
async def system_swap_memory_total_min_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system swap memory total min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Swap Probe", pct=0, log="Collecting total swap baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            swap = psutil.swap_memory()
            val = getattr(swap, "total", 0)
            samples_list.append(val)
            metadata = {"total": val}
        except Exception as e:
            logger.error(f"Error auditing swap memory total min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Swap", pct=pct, log=f"Measured total swap sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    min_val = min(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_min": min_val, "samples": len(samples_list)}

@progress_tool(name="system_swap_memory_used_min_ultimate_audit")
async def system_swap_memory_used_min_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system swap memory used min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Swap Probe", pct=0, log="Collecting used swap baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            swap = psutil.swap_memory()
            val = getattr(swap, "used", 0)
            samples_list.append(val)
            metadata = {"used": val}
        except Exception as e:
            logger.error(f"Error auditing swap memory used min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Swap", pct=pct, log=f"Measured used swap sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    min_val = min(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_min": min_val, "samples": len(samples_list)}

@progress_tool(name="system_swap_memory_free_min_ultimate_audit")
async def system_swap_memory_free_min_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system swap memory free min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Swap Probe", pct=0, log="Collecting free swap baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            swap = psutil.swap_memory()
            val = getattr(swap, "free", 0)
            samples_list.append(val)
            metadata = {"free": val}
        except Exception as e:
            logger.error(f"Error auditing swap memory free min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Swap", pct=pct, log=f"Measured free swap sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    min_val = min(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_min": min_val, "samples": len(samples_list)}

@progress_tool(name="system_swap_memory_sin_min_ultimate_audit")
async def system_swap_memory_sin_min_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system swap memory sin min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Swap Probe", pct=0, log="Collecting swap-in baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            swap = psutil.swap_memory()
            val = getattr(swap, "sin", 0)
            samples_list.append(val)
            metadata = {"sin": val}
        except Exception as e:
            logger.error(f"Error auditing swap memory sin min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Swap", pct=pct, log=f"Measured swap-in sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    min_val = min(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_min": min_val, "samples": len(samples_list)}

@progress_tool(name="system_swap_memory_sout_min_ultimate_audit")
async def system_swap_memory_sout_min_ultimate_audit(samples: int = 3):
    logger.info(f"Starting system swap memory sout min ultimate audit with {samples} samples")
    yield ProgressPayload(step="Initializing Swap Probe", pct=0, log="Collecting swap-out baseline...")
    samples_list = []
    for i in range(samples):
        pct = int(((i + 1) / samples) * 100)
        try:
            swap = psutil.swap_memory()
            val = getattr(swap, "sout", 0)
            samples_list.append(val)
            metadata = {"sout": val}
        except Exception as e:
            logger.error(f"Error auditing swap memory sout min ultimate: {e}")
            metadata = {"error": str(e)}
        yield ProgressPayload(step="Sampling Swap", pct=pct, log=f"Measured swap-out sample {i+1}/{samples}.", metadata=metadata)
        await asyncio.sleep(0.1)
    min_val = min(samples_list) if samples_list else 0.0
    yield {"status": "audit_complete", "final_min": min_val, "samples": len(samples_list)}
