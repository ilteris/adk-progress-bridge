import asyncio
import websockets
import json
import os
import subprocess
import time

async def verify_v831():
    # Start the server in the background
    print("Starting server...")
    server_process = subprocess.Popen(
        ["python3", "-m", "backend.app.main"],
        env={**os.environ, "PYTHONPATH": "."}
    )
    time.sleep(5)  # Give it more time to start

    url = "ws://localhost:8000/ws"
    
    print(f"Connecting to {url}...")
    success = False
    try:
        async with websockets.connect(url) as websocket:
            # 0. Wait for connected message
            msg = await websocket.recv()
            print(f"Initial message: {msg}")

            # 1. List tools and verify count
            await websocket.send(json.dumps({"type": "list_tools", "request_id": "v831-list"}))
            resp = await websocket.recv()
            data = json.loads(resp)
            tools = data.get("tools", [])
            print(f"Total tools found: {len(tools)}")
            
            # Milestone for v831 is 2360 unique tools
            if len(tools) >= 2360:
                print(f"SUCCESS: {len(tools)} tools reached milestone (2360+).")
            else:
                print(f"FAILURE: Only {len(tools)} tools found. Expected 2360.")
                return

            # 2. Test one of the new V21 tools
            test_tool = "system_cpu_percent_percpu_avg_v21"
            print(f"Testing tool: {test_tool}")
            await websocket.send(json.dumps({
                "type": "start",
                "tool_name": test_tool,
                "request_id": "v831-test-tool"
            }))

            async for message in websocket:
                msg = json.loads(message)
                if msg["type"] == "progress":
                    print(f"Progress: {msg['payload']['step']} {msg['payload']['pct']}%")
                elif msg["type"] == "result":
                    print(f"RESULT: {msg['payload']}")
                    if msg['payload'].get("status") == "audit_complete":
                        print(f"V21 Tool {test_tool} VERIFIED.")
                        success = True
                    break
                elif msg["type"] == "error":
                    print(f"ERROR: {msg['payload']}")
                    break
    except Exception as e:
        print(f"Verification failed: {e}")
    finally:
        server_process.terminate()
        server_process.wait()
    
    if success:
        print("V831 SUPREME APEX VERIFICATION SUCCESSFUL")
    else:
        print("V831 SUPREME APEX VERIFICATION FAILED")
        exit(1)

if __name__ == "__main__":
    asyncio.run(verify_v831())
