import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.bridge import registry
import app.dummy_tool # Ensure tools are registered

def check():
    tools = registry.list_tools()
    print(f"Total tools registered: {len(tools)}")
    unique_tools = set(tools)
    print(f"Unique tools registered: {len(unique_tools)}")
    
if __name__ == "__main__":
    check()
