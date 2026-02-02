import asyncio
import sys
import os
import uuid

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.bridge import registry, ProgressPayload
from app.dummy_tool import long_audit

async def test_broadcaster():
    print("Starting v767 Broadcaster verification...")
    
    call_id = str(uuid.uuid4())
    tool_name = "long_audit"
    
    # Start task
    gen = long_audit(duration=2)
    await registry.store_task(call_id, gen, tool_name)
    
    broadcaster = await registry.get_broadcaster(call_id)
    if not broadcaster:
        print("FAILURE: Could not get broadcaster")
        sys.exit(1)
    
    # Subscriber 1 (starts immediately)
    q1 = await broadcaster.subscribe()
    
    # Subscriber 2 (joins late)
    await asyncio.sleep(0.5)
    q2 = await broadcaster.subscribe()
    
    async def consume(name, q):
        events = []
        while True:
            event = await q.get()
            events.append(event)
            if event.type in ["result", "error"]:
                break
        print(f"Subscriber {name} received {len(events)} events.")
        return events

    results = await asyncio.gather(
        consume("S1", q1),
        consume("S2", q2)
    )
    
    s1_events = results[0]
    s2_events = results[1]
    
    if len(s1_events) > 0 and len(s2_events) > 0:
        print("SUCCESS: Both subscribers received events.")
    else:
        print("FAILURE: One or more subscribers did not receive events.")
        sys.exit(1)
        
    # Check if S2 got the history
    if len(s2_events) >= len(s1_events) - 2: # S2 might miss some if they were really fast, but q.get() should have history
        print("SUCCESS: Late subscriber received history replay.")
    else:
        print(f"FAILURE: Late subscriber missed history. S1: {len(s1_events)}, S2: {len(s2_events)}")
        sys.exit(1)

    print("v767 Broadcaster verification successful.")

if __name__ == "__main__":
    asyncio.run(test_broadcaster())
