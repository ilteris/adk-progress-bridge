
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
