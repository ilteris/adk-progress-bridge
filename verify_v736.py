import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.dummy_tool import (
    system_net_if_stats_duplex_max_ultimate_audit,
    system_net_if_stats_duplex_avg_ultimate_audit,
    system_net_if_stats_flags_avg_ultimate_audit,
    system_net_if_stats_flags_min_ultimate_audit
)

async def verify():
    print("Starting v736 verification...")
    
    tools = [
        (system_net_if_stats_duplex_max_ultimate_audit, "system_net_if_stats_duplex_max_ultimate_audit"),
        (system_net_if_stats_duplex_avg_ultimate_audit, "system_net_if_stats_duplex_avg_ultimate_audit"),
        (system_net_if_stats_flags_avg_ultimate_audit, "system_net_if_stats_flags_avg_ultimate_audit"),
        (system_net_if_stats_flags_min_ultimate_audit, "system_net_if_stats_flags_min_ultimate_audit")
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

    print("All v736 tools verified successfully.")

if __name__ == "__main__":
    asyncio.run(verify())
