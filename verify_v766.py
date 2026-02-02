import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.dummy_tool import (
    system_sensors_temperatures_core_avg_ultimate_audit,
    system_sensors_temperatures_core_max_ultimate_audit,
    system_sensors_temperatures_core_min_ultimate_audit,
    system_sensors_temperatures_package_avg_ultimate_audit,
    system_sensors_temperatures_package_max_ultimate_audit,
    system_sensors_fans_cpu_avg_ultimate_audit,
    system_sensors_fans_cpu_max_ultimate_audit,
    system_sensors_fans_cpu_min_ultimate_audit,
    system_sensors_fans_case_avg_ultimate_audit,
    system_sensors_fans_case_max_ultimate_audit
)

async def verify():
    print("Starting v766 verification...")
    
    tools = [
        (system_sensors_temperatures_core_avg_ultimate_audit, "system_sensors_temperatures_core_avg_ultimate_audit"),
        (system_sensors_temperatures_core_max_ultimate_audit, "system_sensors_temperatures_core_max_ultimate_audit"),
        (system_sensors_temperatures_core_min_ultimate_audit, "system_sensors_temperatures_core_min_ultimate_audit"),
        (system_sensors_temperatures_package_avg_ultimate_audit, "system_sensors_temperatures_package_avg_ultimate_audit"),
        (system_sensors_temperatures_package_max_ultimate_audit, "system_sensors_temperatures_package_max_ultimate_audit"),
        (system_sensors_fans_cpu_avg_ultimate_audit, "system_sensors_fans_cpu_avg_ultimate_audit"),
        (system_sensors_fans_cpu_max_ultimate_audit, "system_sensors_fans_cpu_max_ultimate_audit"),
        (system_sensors_fans_cpu_min_ultimate_audit, "system_sensors_fans_cpu_min_ultimate_audit"),
        (system_sensors_fans_case_avg_ultimate_audit, "system_sensors_fans_case_avg_ultimate_audit"),
        (system_sensors_fans_case_max_ultimate_audit, "system_sensors_fans_case_max_ultimate_audit")
    ]
    
    for tool_func, name in tools:
        print(f"Verifying {name}...")
        results = []
        async for item in tool_func(samples=2):
            results.append(item)
        
        # Last item should be a dict with status: audit_complete
        final_result = results[-1]
        if isinstance(final_result, dict) and final_result.get("status") == "audit_complete":
            print(f"SUCCESS: {name} verified.")
        else:
            print(f"FAILURE: {name} failed verification. Last item: {final_result}")
            sys.exit(1)

    print("All v766 tools verified successfully.")

if __name__ == "__main__":
    asyncio.run(verify())
