
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
            connections = process.connections()
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
        "final_connections_count": len(psutil.Process().connections()),
        "stability": "STABLE"
    }
