import logging
import json
from datetime import datetime
from typing import Any

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
        }
        
        if hasattr(record, "call_id"):
            log_record["call_id"] = record.call_id
        if hasattr(record, "tool_name"):
            log_record["tool_name"] = record.tool_name
        
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
        logger.setLevel(logging.DEBUG)
    return logger

logger = setup_logging()