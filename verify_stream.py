import requests
import json
import time
import threading
import os

def test_stream_stop():
    base_url = "http://localhost:8000"
    api_key = os.getenv("BRIDGE_API_KEY", "")
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key

    print("\n--- Testing SSE Stop Flow ---")
    
    # 1. Start task
    print("Starting task...")
    start_resp = requests.post(f"{base_url}/start_task/long_audit", json={"args": {"duration": 10}}, headers=headers)
    if start_resp.status_code != 200:
        print(f"Failed to start task: {start_resp.status_code} {start_resp.text}")
        return
    
    data = start_resp.json()
    call_id = data['call_id']
    print(f"Task started. Call ID: {call_id}")

    # 2. Function to stop task after a delay
    def stop_later():
        time.sleep(2)
        print(f"Sending stop request for {call_id}...")
        stop_resp = requests.post(f"{base_url}/stop_task/{call_id}", headers=headers)
        print(f"Stop request response: {stop_resp.status_code} | {stop_resp.json()}")

    threading.Thread(target=stop_later).start()

    # 3. Stream events
    print("Streaming events...")
    params = {}
    if api_key:
        params["api_key"] = api_key
        
    stream_resp = requests.get(f"{base_url}/stream/{call_id}", stream=True, headers=headers, params=params)
    
    for line in stream_resp.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith('data: '):
                event_data = json.loads(decoded_line[6:])
                mtype = event_data['type']
                payload = event_data['payload']
                print(f"Event: {mtype} | {payload.get('step') if isinstance(payload, dict) else payload}")
                
                if mtype == 'progress' and isinstance(payload, dict) and payload.get('step') == 'Cancelled':
                    print("SUCCESS: Received Cancelled event via SSE")
                
                if mtype == 'result' or mtype == 'error':
                    break

def run_normal_stream():
    base_url = "http://localhost:8000"
    api_key = os.getenv("BRIDGE_API_KEY", "")
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key

    print("\n--- Testing Normal SSE Flow ---")
    start_resp = requests.post(f"{base_url}/start_task/long_audit", json={"args": {"duration": 2}}, headers=headers)
    if start_resp.status_code != 200:
        print(f"Failed to start task: {start_resp.status_code} {start_resp.text}")
        return
        
    call_id = start_resp.json()['call_id']
    print(f"Task started. Call ID: {call_id}")
    
    params = {}
    if api_key:
        params["api_key"] = api_key
        
    stream_resp = requests.get(f"{base_url}/stream/{call_id}", stream=True, headers=headers, params=params)
    for line in stream_resp.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith('data: '):
                event_data = json.loads(decoded_line[6:])
                print(f"Event: {event_data['type']} | {event_data['payload']}")

if __name__ == "__main__":
    run_normal_stream()
    test_stream_stop()