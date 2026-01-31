import requests
import json
import time
import os

def test_stream():
    api_key = os.getenv("BRIDGE_API_KEY", "")
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key
        print(f"Using API Key: {api_key[:4]}...")

    # 1. Start Task
    print("Starting task...")
    resp = requests.post("http://localhost:8000/start_task/long_audit", json={"args": {"duration": 2}}, headers=headers)
    if resp.status_code != 200:
        print(f"Failed to start task: {resp.status_code} {resp.text}")
        return
    
    call_id = resp.json()["call_id"]
    print(f"Task started. Call ID: {call_id}")
    
    # 2. Stream
    print("Streaming events...")
    params = {}
    if api_key:
        params["api_key"] = api_key
        
    stream_resp = requests.get(f"http://localhost:8000/stream/{call_id}", params=params, stream=True)
    
    if stream_resp.status_code != 200:
        print(f"Failed to connect to stream: {stream_resp.status_code} {stream_resp.text}")
        return

    for line in stream_resp.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith("data: "):
                data = json.loads(decoded_line[6:])
                print(f"Event: {data['type']} | {data['payload']}")

if __name__ == "__main__":
    test_stream()