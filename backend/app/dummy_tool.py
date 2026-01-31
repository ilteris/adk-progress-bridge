import asyncio
import random
from .bridge import progress_tool, ProgressPayload, input_manager
from .logger import logger
from .context import call_id_var

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

    # Yield final result
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

@progress_tool(name="god_tier_simulation")
async def god_tier_simulation():
    """
    The Ultimate God-Tier Simulation: Sub-tasks, Parallelism, and Interactivity.
    """
    call_id = call_id_var.get()
    
    yield ProgressPayload(step="Initializing God Mode", pct=10, log="Calibrating hyper-parameters...")
    await asyncio.sleep(0.5)

    # Sub-task Phase
    for i in range(3):
        logger.info(f"God-Tier: Processing sub-module {i+1}")
        yield ProgressPayload(
            step=f"Module {i+1}", 
            pct=10 + (i*10), 
            log=f"Analyzing Module {i+1} structure...",
            metadata={"module": i+1}
        )
        await asyncio.sleep(0.3)

    # Interactivity Phase
    prompt = "Found a spatial anomaly. Should I stabilize it? (yes/no)"
    yield {
        "type": "input_request",
        "payload": {"prompt": prompt}
    }
    
    user_response = await input_manager.wait_for_input(call_id, prompt)
    
    if user_response.lower() != "yes":
        yield ProgressPayload(step="Aborting", pct=100, log="User declined stabilization. Universe collapsing.")
        yield {"status": "collapsed"}
        return

    yield ProgressPayload(step="Stabilizing", pct=50, log="Anomaly stabilized. Initiating parallel synthesis...")
    await asyncio.sleep(0.5)

    # Parallel Phase
    queue = asyncio.Queue()
    async def synth_worker(id: int):
        await asyncio.sleep(random.uniform(0.5, 1.0))
        await queue.put(id)
    
    workers = [asyncio.create_task(synth_worker(i)) for i in range(5)]
    for i in range(5):
        worker_id = await queue.get()
        pct = 50 + (i+1)*10
        yield ProgressPayload(step="Synthesis", pct=pct, log=f"Synthesis component {worker_id+1} complete.")
    
    yield ProgressPayload(step="Finalizing", pct=100, log="God-Tier Simulation successful.")
    yield {"status": "god_tier_success", "universe_state": "stabilized"}
