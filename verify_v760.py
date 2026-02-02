import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.dummy_tool import (
    system_virtual_memory_total_max_ultimate_audit,
    system_virtual_memory_available_max_ultimate_audit,
    system_virtual_memory_percent_max_ultimate_audit,
    system_virtual_memory_used_max_ultimate_audit,
    system_virtual_memory_free_max_ultimate_audit,
    system_virtual_memory_active_max_ultimate_audit,
    system_virtual_memory_inactive_max_ultimate_audit,
    system_virtual_memory_buffers_max_ultimate_audit,
    system_virtual_memory_cached_max_ultimate_audit,
    system_virtual_memory_shared_max_ultimate_audit
)

async def verify():
    print("Starting v760 verification...")
    
    tools = [
        (system_virtual_memory_total_max_ultimate_audit, "system_virtual_memory_total_max_ultimate_audit"),
        (system_virtual_memory_available_max_ultimate_audit, "system_virtual_memory_available_max_ultimate_audit"),
        (system_virtual_memory_percent_max_ultimate_audit, "system_virtual_memory_percent_max_ultimate_audit"),
        (system_virtual_memory_used_max_ultimate_audit, "system_virtual_memory_used_max_ultimate_audit"),
        (system_virtual_memory_free_max_ultimate_audit, "system_virtual_memory_free_max_ultimate_audit"),
        (system_virtual_memory_active_max_ultimate_audit, "system_virtual_memory_active_max_ultimate_audit"),
        (system_virtual_memory_inactive_max_ultimate_audit, "system_virtual_memory_inactive_max_ultimate_audit"),
        (system_virtual_memory_buffers_max_ultimate_audit, "system_virtual_memory_buffers_max_ultimate_audit"),
        (system_virtual_memory_cached_max_ultimate_audit, "system_virtual_memory_cached_max_ultimate_audit"),
        (system_virtual_memory_shared_max_ultimate_audit, "system_virtual_memory_shared_max_ultimate_audit")
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

    print("All v760 tools verified successfully.")

if __name__ == "__main__":
    asyncio.run(verify())
