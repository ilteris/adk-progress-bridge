import asyncio
import websockets
import json
import os
import sys
import time

async def verify_v801():
    print("Starting Supreme Apex Milestone 1070 Verification (v801)")
    api_key = os.getenv("BRIDGE_API_KEY", "")
    url = "ws://localhost:8000/ws"
    if api_key:
        url += f"?api_key={api_key}"
    
    try:
        async with websockets.connect(url) as websocket:
            # 1. Verify connection and initial message
            msg = await websocket.recv()
            data = json.loads(msg)
            print(f"Connected: {data.get('type')} | Status: {data.get('status')}")
            
            # 2. Verify Version and Metadata via get_health
            print("\n--- Verifying Version and Metadata ---")
            health_msg = {
                "type": "get_health",
                "request_id": "v801-health"
            }
            await websocket.send(json.dumps(health_msg))
            
            msg = await websocket.recv()
            data = json.loads(msg)
            if data['type'] == 'health_data':
                health = data['data']
                version = health.get('version')
                commit = health.get('git_commit')
                apex = health.get('operational_apex')
                print(f"Version: {version}")
                print(f"Commit: {commit}")
                print(f"Operational Apex: {apex}")
                
                if version == "2.12.24" and "v801-supreme-apex-1070-v1" in commit:
                    print("✅ Version and Metadata verification SUCCESS")
                else:
                    print("❌ Version and Metadata verification FAILED")
            
            # 3. Verify Tool Count
            print("\n--- Verifying Tool Count ---")
            list_msg = {
                "type": "list_tools",
                "request_id": "v801-list"
            }
            await websocket.send(json.dumps(list_msg))
            
            msg = await websocket.recv()
            data = json.loads(msg)
            tools = data.get('tools', [])
            print(f"Total tools registered: {len(tools)}")
            if len(tools) >= 1070:
                print(f"✅ Tool count milestone reached (>= 1070): SUCCESS")
            else:
                print(f"❌ Tool count milestone NOT reached (< 1070): FAILED")

            # 4. Verify New v4 Audit Tools
            print("\n--- Verifying New v4 Audit Tools ---")
            test_tools = [
                "system_process_num_threads_avg_ultimate_audit_v4",
                "system_process_ctx_switches_voluntary_max_ultimate_audit_v4",
                "system_process_cpu_affinity_count_min_ultimate_audit_v4",
                "system_process_memory_full_info_uss_avg_ultimate_audit_v4"
            ]
            
            for tool_name in test_tools:
                if tool_name in tools:
                    print(f"Tool {tool_name} is registered. Testing execution...")
                    start_msg = {
                        "type": "start",
                        "tool_name": tool_name,
                        "args": {"samples": 2},
                        "request_id": f"test-{tool_name}"
                    }
                    await websocket.send(json.dumps(start_msg))
                    
                    async for message in websocket:
                        event = json.loads(message)
                        if event['type'] == 'result':
                            print(f"✅ {tool_name} result: {event.get('payload')}")
                            break
                        elif event['type'] == 'error':
                            print(f"❌ {tool_name} failed: {event.get('payload')}")
                            break
                else:
                    print(f"❌ Tool {tool_name} NOT FOUND in registry")

            print("\n--- Verification Complete ---")

    except Exception as e:
        print(f"❌ WebSocket error: {e}")

if __name__ == "__main__":
    asyncio.run(verify_v801())