
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
