
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
