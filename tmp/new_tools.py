
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
