import asyncio
import websockets
import json
import os
import sys

async def verify_v830_ws():
    api_key = os.getenv("BRIDGE_API_KEY", "test-key")
    url = "ws://localhost:8000/ws"
    if api_key:
        url += f"?api_key={api_key}"
        print(f"Using API Key in WS URL")

    new_tools = [
        "system_sensors_battery_percent_avg_v20",
        "system_sensors_battery_secsleft_avg_v20",
        "system_sensors_temperatures_avg_v20",
        "system_sensors_fans_avg_v20",
        "system_boot_time_v20",
        "system_users_count_v20",
        "system_cpu_count_logical_v20",
        "system_cpu_freq_current_avg_v20",
        "system_disk_usage_percent_v20",
        "system_cpu_stats_ctx_switches_v20"
    ]

    try:
        async with websockets.connect(url) as websocket:
            print("\n--- Verifying v830 tools over WebSocket ---")
            
            # Wait for connected message
            msg = await websocket.recv()
            print(f"WS Event: {json.loads(msg)['type']}")

            for tool in new_tools:
                print(f"\nTesting {tool}...")
                start_msg = {
                    "type": "start",
                    "tool_name": tool,
                    "args": {"samples": 2},
                    "request_id": f"test-{tool}"
                }
                await websocket.send(json.dumps(start_msg))
                
                success = False
                async for message in websocket:
                    data = json.loads(message)
                    mtype = data['type']
                    
                    if mtype == 'progress':
                        payload = data.get('payload', {})
                        print(f"  Progress: {payload.get('pct')}% - {payload.get('step')}")
                    
                    if mtype == 'result':
                        print(f"  RESULT: {data.get('payload')}")
                        if data.get('payload', {}).get('status') == 'audit_complete':
                            success = True
                        break
                    
                    if mtype == 'error':
                        print(f"  ERROR: {data.get('payload')}")
                        break
                
                if not success:
                    print(f"FAILURE: {tool} failed verification.")
                    sys.exit(1)
                else:
                    print(f"SUCCESS: {tool} verified.")

            print("\nAll v830 tools verified successfully over WebSocket.")

            # Check total tool count
            list_msg = {
                "type": "list_tools",
                "request_id": "final-count-check"
            }
            await websocket.send(json.dumps(list_msg))
            
            msg = await websocket.recv()
            data = json.loads(msg)
            if data['type'] == 'tools_list':
                tools_count = len(data['tools'])
                print(f"\nFinal Tools Count: {tools_count}")
                if tools_count >= 2320:
                    print("Milestone 2320 reached!")
                else:
                    print(f"Milestone 2320 NOT reached. Current count: {tools_count}")
                    sys.exit(1)

    except Exception as e:
        print(f"WS Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(verify_v830_ws())
