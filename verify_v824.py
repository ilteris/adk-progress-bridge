
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
            await websocket.send(json.dumps({"type": "list_tools", "request_id": "v824-list"}))
            
            tools = []
            async for message in websocket:
                data = json.loads(message)
                if data.get("type") == "tools_list" and data.get("request_id") == "v824-list":
                    tools = data.get("tools", [])
                    break
                else:
                    # Skip other messages like connected or system_metrics
                    pass
            
            print(f"Total tools: {len(tools)}")
            
            if not tools:
                print("Error: No tools returned")
                sys.exit(1)

            # Support both list of strings and list of dicts (if it changes)
            if tools and isinstance(tools[0], dict):
                v14_tools = [t for t in tools if "_v14" in t["name"]]
            else:
                v14_tools = [t for t in tools if "_v14" in t]
            
            print(f"V14 tools found: {len(v14_tools)}")
            
            if len(v14_tools) < 40:
                print("Error: Missing V14 tools")
                sys.exit(1)
            
            # 2. Test execution of one new tool
            test_tool = "system_process_count_avg_v14"
            print(f"Testing tool: {test_tool}")
            await websocket.send(json.dumps({
                "type": "start",
                "tool_name": test_tool,
                "args": {"samples": 2},
                "request_id": "v824-test"
            }))
            
            async for message in websocket:
                msg = json.loads(message)
                if msg.get("type") == "result" and msg.get("request_id") == "v824-test":
                    print(f"Tool Result: {msg.get('payload')}")
                    break
                elif msg.get("type") == "error" and msg.get("request_id") == "v824-test":
                    print(f"Error: {msg.get('payload', {}).get('detail')}")
                    sys.exit(1)
            
            print("Verification successful!")
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(verify())
