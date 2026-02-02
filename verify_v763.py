import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.dummy_tool import (
    system_cpu_times_percent_user_min_ultimate_audit,
    system_cpu_times_percent_nice_min_ultimate_audit,
    system_cpu_times_percent_system_min_ultimate_audit,
    system_cpu_times_percent_idle_min_ultimate_audit,
    system_cpu_times_percent_iowait_min_ultimate_audit,
    system_cpu_times_percent_irq_min_ultimate_audit,
    system_cpu_times_percent_softirq_min_ultimate_audit,
    system_cpu_times_percent_guest_nice_min_ultimate_audit,
    system_net_io_errin_min_ultimate_audit,
    system_net_io_errout_min_ultimate_audit
)

async def verify():
    print("Starting v763 verification...")
    
    tools = [
        (system_cpu_times_percent_user_min_ultimate_audit, "system_cpu_times_percent_user_min_ultimate_audit"),
        (system_cpu_times_percent_nice_min_ultimate_audit, "system_cpu_times_percent_nice_min_ultimate_audit"),
        (system_cpu_times_percent_system_min_ultimate_audit, "system_cpu_times_percent_system_min_ultimate_audit"),
        (system_cpu_times_percent_idle_min_ultimate_audit, "system_cpu_times_percent_idle_min_ultimate_audit"),
        (system_cpu_times_percent_iowait_min_ultimate_audit, "system_cpu_times_percent_iowait_min_ultimate_audit"),
        (system_cpu_times_percent_irq_min_ultimate_audit, "system_cpu_times_percent_irq_min_ultimate_audit"),
        (system_cpu_times_percent_softirq_min_ultimate_audit, "system_cpu_times_percent_softirq_min_ultimate_audit"),
        (system_cpu_times_percent_guest_nice_min_ultimate_audit, "system_cpu_times_percent_guest_nice_min_ultimate_audit"),
        (system_net_io_errin_min_ultimate_audit, "system_net_io_errin_min_ultimate_audit"),
        (system_net_io_errout_min_ultimate_audit, "system_net_io_errout_min_ultimate_audit")
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

    print("All v763 tools verified successfully.")

if __name__ == "__main__":
    asyncio.run(verify())
