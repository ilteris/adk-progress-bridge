import sys
import os
sys.path.append(os.path.join(os.getcwd(), "backend"))
from app.bridge import registry
import app.dummy_tool # Ensure they are registered

tools = registry.list_tools()
print(f"Total tools registered: {len(tools)}")
