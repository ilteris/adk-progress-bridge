
import asyncio
import websockets
import json
import sys

async def verify():
    url = "ws://localhost:8000/ws"
    try:
        async with websockets.connect(url) as websocket:
            print("Connected to WebSocket")
            
            # 1. List tools and verify count
            await websocket.send(json.dumps({"type": "list_tools", "request_id": "v825-list"}))
            
            tools = []
            async for message in websocket:
                data = json.loads(message)
                if data.get("type") == "tools_list" and data.get("request_id") == "v825-list":
                    tools = data.get("tools", [])
                    break
                else:
                    pass
            
            print(f"Total tools: {len(tools)}")
            
            if not tools:
                print("Error: No tools returned")
                sys.exit(1)

            # Support both list of strings and list of dicts
            if tools and isinstance(tools[0], dict):
                v15_tools = [t for t in tools if "_v15" in t["name"]]
            else:
                v15_tools = [t for t in tools if "_v15" in t]
            
            print(f"V15 tools found: {len(v15_tools)}")
            
            if len(v15_tools) < 40:
                print("Error: Missing V15 tools")
                sys.exit(1)
            
            # 2. Test execution of one new tool
            test_tool = "system_cpu_stats_ctx_switches_avg_v15"
            print(f"Testing tool: {test_tool}")
            await websocket.send(json.dumps({
                "type": "start",
                "tool_name": test_tool,
                "args": {"samples": 2},
                "request_id": "v825-test"
            }))
            
            async for message in websocket:
                msg = json.loads(message)
                if msg.get("type") == "result" and msg.get("request_id") == "v825-test":
                    print(f"Tool Result: {msg.get('payload')}")
                    break
                elif msg.get("type") == "error" and msg.get("request_id") == "v825-test":
                    print(f"Error: {msg.get('payload', {}).get('detail')}")
                    sys.exit(1)
            
            print("Verification successful!")
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(verify())
