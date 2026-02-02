import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.dummy_tool import (
    system_cpu_stats_ctx_switches_max_ultimate_audit,
    system_cpu_stats_interrupts_max_ultimate_audit,
    system_cpu_stats_soft_interrupts_max_ultimate_audit,
    system_cpu_stats_syscalls_max_ultimate_audit,
    system_net_io_bytes_sent_max_ultimate_audit,
    system_net_io_bytes_recv_max_ultimate_audit,
    system_net_io_packets_sent_max_ultimate_audit,
    system_net_io_packets_recv_max_ultimate_audit,
    system_disk_io_read_bytes_max_ultimate_audit,
    system_disk_io_write_bytes_max_ultimate_audit
)

async def verify():
    print("Starting v756 verification...")
    
    tools = [
        (system_cpu_stats_ctx_switches_max_ultimate_audit, "system_cpu_stats_ctx_switches_max_ultimate_audit"),
        (system_cpu_stats_interrupts_max_ultimate_audit, "system_cpu_stats_interrupts_max_ultimate_audit"),
        (system_cpu_stats_soft_interrupts_max_ultimate_audit, "system_cpu_stats_soft_interrupts_max_ultimate_audit"),
        (system_cpu_stats_syscalls_max_ultimate_audit, "system_cpu_stats_syscalls_max_ultimate_audit"),
        (system_net_io_bytes_sent_max_ultimate_audit, "system_net_io_bytes_sent_max_ultimate_audit"),
        (system_net_io_bytes_recv_max_ultimate_audit, "system_net_io_bytes_recv_max_ultimate_audit"),
        (system_net_io_packets_sent_max_ultimate_audit, "system_net_io_packets_sent_max_ultimate_audit"),
        (system_net_io_packets_recv_max_ultimate_audit, "system_net_io_packets_recv_max_ultimate_audit"),
        (system_disk_io_read_bytes_max_ultimate_audit, "system_disk_io_read_bytes_max_ultimate_audit"),
        (system_disk_io_write_bytes_max_ultimate_audit, "system_disk_io_write_bytes_max_ultimate_audit")
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

    print("All v756 tools verified successfully.")

if __name__ == "__main__":
    asyncio.run(verify())
