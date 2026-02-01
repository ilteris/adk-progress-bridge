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
    data = await health_engine.get_health_data(dummy_state, "2.1.5", "v589-supreme-apex", "SUPREME APEX VERIFICATION")
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