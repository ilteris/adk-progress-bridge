import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.dummy_tool import (
    system_cpu_times_percent_per_cpu_avg_ultimate_audit,
    system_cpu_times_percent_per_cpu_max_ultimate_audit,
    system_cpu_times_percent_per_cpu_min_ultimate_audit,
    system_net_io_per_nic_bytes_sent_avg_ultimate_audit,
    system_net_io_per_nic_bytes_recv_avg_ultimate_audit,
    system_disk_usage_all_partitions_avg_ultimate_audit,
    system_disk_io_per_disk_read_bytes_avg_ultimate_audit,
    system_disk_io_per_disk_write_bytes_avg_ultimate_audit,
    system_memory_full_info_uss_avg_ultimate_audit,
    system_memory_full_info_pss_avg_ultimate_audit
)

async def verify():
    print("Starting v751 verification...")
    
    tools = [
        (system_cpu_times_percent_per_cpu_avg_ultimate_audit, "system_cpu_times_percent_per_cpu_avg_ultimate_audit"),
        (system_cpu_times_percent_per_cpu_max_ultimate_audit, "system_cpu_times_percent_per_cpu_max_ultimate_audit"),
        (system_cpu_times_percent_per_cpu_min_ultimate_audit, "system_cpu_times_percent_per_cpu_min_ultimate_audit"),
        (system_net_io_per_nic_bytes_sent_avg_ultimate_audit, "system_net_io_per_nic_bytes_sent_avg_ultimate_audit"),
        (system_net_io_per_nic_bytes_recv_avg_ultimate_audit, "system_net_io_per_nic_bytes_recv_avg_ultimate_audit"),
        (system_disk_usage_all_partitions_avg_ultimate_audit, "system_disk_usage_all_partitions_avg_ultimate_audit"),
        (system_disk_io_per_disk_read_bytes_avg_ultimate_audit, "system_disk_io_per_disk_read_bytes_avg_ultimate_audit"),
        (system_disk_io_per_disk_write_bytes_avg_ultimate_audit, "system_disk_io_per_disk_write_bytes_avg_ultimate_audit"),
        (system_memory_full_info_uss_avg_ultimate_audit, "system_memory_full_info_uss_avg_ultimate_audit"),
        (system_memory_full_info_pss_avg_ultimate_audit, "system_memory_full_info_pss_avg_ultimate_audit")
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

    print("All v751 tools verified successfully.")

if __name__ == "__main__":
    asyncio.run(verify())
