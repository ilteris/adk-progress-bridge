import asyncio
import sys
from backend.app.dummy_tool import system_disk_io_write_bytes_ultimate_audit, system_disk_io_read_time_ultimate_audit, system_disk_io_write_time_ultimate_audit

async def test_tool(name, tool_func):
    print(f"Testing {name}...")
    try:
        gen = tool_func(samples=1)
        async for p in gen:
            if isinstance(p, dict):
                print(f"  Result: {p}")
            else:
                print(f"  Progress: {p.pct}% - {p.step}")
        print(f"✅ {name} passed.")
        return True
    except Exception as e:
        print(f"❌ {name} failed: {e}")
        return False

async def main():
    tools = [
        ("system_disk_io_write_bytes_ultimate_audit", system_disk_io_write_bytes_ultimate_audit),
        ("system_disk_io_read_time_ultimate_audit", system_disk_io_read_time_ultimate_audit),
        ("system_disk_io_write_time_ultimate_audit", system_disk_io_write_time_ultimate_audit),
    ]
    
    results = []
    for name, func in tools:
        results.append(await test_tool(name, func))
    
    if all(results):
        print("\nAll v707 tools verified successfully.")
        sys.exit(0)
    else:
        print("\nSome v707 tools failed verification.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

