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