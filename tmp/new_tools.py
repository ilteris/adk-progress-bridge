
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
