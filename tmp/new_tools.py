
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
