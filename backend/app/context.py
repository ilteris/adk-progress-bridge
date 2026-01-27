from contextvars import ContextVar
from typing import Optional

# Context variables for structured logging
call_id_var: ContextVar[Optional[str]] = ContextVar("call_id", default=None)
tool_name_var: ContextVar[Optional[str]] = ContextVar("tool_name", default=None)
