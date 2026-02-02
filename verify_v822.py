
import asyncio
import websockets
import json
import os

async def verify_v822():
    url = "ws://localhost:8000/ws"
    # Try to get API key from environment or default (usually "test-api-key" in these tests)
    api_key = os.getenv("BRIDGE_API_KEY", "test-api-key")
    if api_key:
        url += f"?api_key={api_key}"

    print(f"Connecting to {url}...")
    try:
        async with websockets.connect(url) as websocket:
            # 0. Wait for connected message
            msg = await websocket.recv()
            print(f"Initial message: {msg}")

            # 1. List tools and verify count
            await websocket.send(json.dumps({"type": "list_tools", "request_id": "v822-list"}))
            resp = await websocket.recv()
            data = json.loads(resp)
            tools = data.get("tools", [])
            print(f"Total tools found: {len(tools)}")
            
            if len(tools) >= 1960:
                print(f"SUCCESS: {len(tools)} tools reached milestone (1960+).")
            else:
                print(f"FAILURE: Only {len(tools)} found. Expected 1960+.")

            # 2. Test one of the new V12 tools
            test_tool = "system_net_io_bytes_sent_avg_v12"
            print(f"Testing tool: {test_tool}")
            await websocket.send(json.dumps({
                "type": "start",
                "tool_name": test_tool,
                "request_id": "v822-test-tool"
            }))

            async for message in websocket:
                msg = json.loads(message)
                if msg["type"] == "progress":
                    print(f"Progress: {msg['payload']['step']} {msg['payload']['pct']}%")
                elif msg["type"] == "result":
                    print(f"RESULT: {msg['payload']}")
                    if msg['payload'].get("status") == "audit_complete":
                        print(f"V12 Tool {test_tool} VERIFIED.")
                    break
                elif msg["type"] == "error":
                    print(f"ERROR: {msg['payload']}")
                    break

    except Exception as e:
        print(f"Verification failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_v822())
