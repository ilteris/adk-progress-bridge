import asyncio
import websockets
import json
import os
import sys
import time

async def verify_v818():
    api_key = os.getenv("BRIDGE_API_KEY", "")
    url = "ws://localhost:8000/ws"
    if api_key:
        url += f"?api_key={api_key}"
        print(f"Using API Key in WS URL")

    new_tools = [
        "system_process_memory_info_ex_uss_avg_v8",
        "system_process_memory_info_ex_pss_max_v8",
        "system_process_io_counters_read_chars_sum_v8"
    ]

    try:
        async with websockets.connect(url) as websocket:
            print("\n--- Verifying v818 tools and Unsubscribe over WebSocket ---")
            
            # Wait for connected message
            msg = await websocket.recv()
            print(f"WS Event: {json.loads(msg)['type']}")

            # 1. Check tool count
            list_msg = {
                "type": "list_tools",
                "request_id": "count-check-v818"
            }
            await websocket.send(json.dumps(list_msg))
            msg = await websocket.recv()
            data = json.loads(msg)
            if data['type'] == 'tools_list':
                count = len(data['tools'])
                print(f"Tools count: {count}")
                if count >= 1800:
                    print("SUCCESS: 1800 tools milestone reached.")
                else:
                    print(f"FAILURE: Expected at least 1800 tools, got {count}")
                    sys.exit(1)

            # 2. Test a new tool
            tool = new_tools[0]
            print(f"\nTesting {tool}...")
            start_msg = {
                "type": "start",
                "tool_name": tool,
                "args": {"samples": 2},
                "request_id": f"test-{tool}"
            }
            await websocket.send(json.dumps(start_msg))
            
            async for message in websocket:
                data = json.loads(message)
                if data['type'] == 'progress':
                    pct = data['payload'].get('pct')
                    print(f"  Progress: {pct}%")
                if data['type'] == 'result':
                    print(f"  RESULT: {data['payload']}")
                    break
            
            # 3. Test Unsubscribe
            print(f"\nTesting Unsubscribe flow...")
            tool = new_tools[1]
            start_msg = {
                "type": "start",
                "tool_name": tool,
                "args": {"samples": 10},
                "request_id": "test-unsubscribe-start"
            }
            await websocket.send(json.dumps(start_msg))
            
            call_id = None
            received_after_unsubscribe = []
            
            async def read_until_unsubscribe():
                nonlocal call_id
                async for message in websocket:
                    data = json.loads(message)
                    if data['type'] == 'task_started':
                        call_id = data['call_id']
                    if data['type'] == 'progress':
                        pct = data['payload'].get('pct')
                        print(f"  Received progress for {call_id}: {pct}%")
                        if pct >= 20:
                            unsub_msg = {
                                "type": "unsubscribe",
                                "call_id": call_id,
                                "request_id": "test-unsubscribe-action"
                            }
                            await websocket.send(json.dumps(unsub_msg))
                            print(f"  Sent unsubscribe for {call_id}")
                    if data['type'] == 'unsubscribe_success':
                        print(f"  Received unsubscribe_success for {call_id}")
                        break

            await read_until_unsubscribe()
            
            print("  Waiting 2 seconds to see if more progress messages arrive...")
            try:
                while True:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(msg)
                    if data['type'] == 'system_metrics':
                        continue
                    if data.get('call_id') == call_id:
                        print(f"  ERROR: Received unexpected message for {call_id} after unsubscribe: {data['type']}")
                        received_after_unsubscribe.append(data)
            except asyncio.TimeoutError:
                print("  No more messages received for unsubscribed task. SUCCESS.")

            if received_after_unsubscribe:
                print("FAILURE: Received messages after unsubscribe.")
                sys.exit(1)
            
            print("\nAll v818 verifications passed.")

    except Exception as e:
        print(f"WS Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(verify_v818())