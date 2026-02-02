import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.dummy_tool import (
    system_cpu_freq_current_avg_ultimate_audit,
    system_cpu_freq_min_avg_ultimate_audit,
    system_cpu_freq_max_avg_ultimate_audit,
    system_load_avg_1m_avg_ultimate_audit,
    system_load_avg_5m_avg_ultimate_audit,
    system_load_avg_15m_avg_ultimate_audit,
    system_boot_time_avg_ultimate_audit,
    system_users_count_avg_ultimate_audit,
    system_pids_count_avg_ultimate_audit,
    system_memory_available_avg_ultimate_audit
)

async def verify():
    print("Starting v750 verification...")
    
    tools = [
        (system_cpu_freq_current_avg_ultimate_audit, "system_cpu_freq_current_avg_ultimate_audit"),
        (system_cpu_freq_min_avg_ultimate_audit, "system_cpu_freq_min_avg_ultimate_audit"),
        (system_cpu_freq_max_avg_ultimate_audit, "system_cpu_freq_max_avg_ultimate_audit"),
        (system_load_avg_1m_avg_ultimate_audit, "system_load_avg_1m_avg_ultimate_audit"),
        (system_load_avg_5m_avg_ultimate_audit, "system_load_avg_5m_avg_ultimate_audit"),
        (system_load_avg_15m_avg_ultimate_audit, "system_load_avg_15m_avg_ultimate_audit"),
        (system_boot_time_avg_ultimate_audit, "system_boot_time_avg_ultimate_audit"),
        (system_users_count_avg_ultimate_audit, "system_users_count_avg_ultimate_audit"),
        (system_pids_count_avg_ultimate_audit, "system_pids_count_avg_ultimate_audit"),
        (system_memory_available_avg_ultimate_audit, "system_memory_available_avg_ultimate_audit")
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

    print("All v750 tools verified successfully.")

if __name__ == "__main__":
    asyncio.run(verify())
