import logging
import json
from datetime import datetime
from typing import Any
from .context import call_id_var, tool_name_var

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
        }
        
        # Get context from extra or contextvars
        call_id = getattr(record, "call_id", call_id_var.get())
        tool_name = getattr(record, "tool_name", tool_name_var.get())
        
        if call_id:
            log_record["call_id"] = call_id
        if tool_name:
            log_record["tool_name"] = tool_name
        
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        for key, value in record.__dict__.items():
            if key not in ["args", "asctime", "created", "exc_info", "exc_text", "filename", "funcName", "levelname", "levelno", "lineno", "module", "msecs", "message", "msg", "name", "pathname", "process", "processName", "relativeCreated", "stack_info", "thread", "threadName", "call_id", "tool_name"]:
                log_record[key] = value

        return json.dumps(log_record)

def setup_logging():
    # Get the logger
    logger = logging.getLogger("adk-bridge")
    logger.propagate = False # Don't pass to root to avoid double logging with uvicorn
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

logger = setup_logging()