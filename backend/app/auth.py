import os
from typing import Optional, Union
from fastapi import Request, HTTPException, Security, status, WebSocket
from fastapi.security import APIKeyHeader
from .logger import logger

# Configuration
API_KEY_NAME = "X-API-Key"
BRIDGE_API_KEY = os.getenv("BRIDGE_API_KEY")

api_key_header_scheme = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(
    request: Request,
    api_key_header: Optional[str] = Security(api_key_header_scheme),
):
    """
    Validates the API Key from either the header or a query parameter.
    """
    if not BRIDGE_API_KEY:
        return True

    # 1. Check header
    if api_key_header == BRIDGE_API_KEY:
        return True
    
    # 2. Check query param (fallback for SSE)
    api_key_query = request.query_params.get("api_key")
    if api_key_query == BRIDGE_API_KEY:
        return True

    logger.warning("Invalid API Key provided")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
        headers={"WWW-Authenticate": API_KEY_NAME},
    )

async def verify_api_key_ws(websocket: WebSocket):
    """
    Validates API key for WebSocket connections.
    """
    if not BRIDGE_API_KEY:
        return
    
    api_key = websocket.query_params.get("api_key")
    if api_key == BRIDGE_API_KEY:
        return
    
    logger.warning("Invalid API Key provided for WebSocket")
    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")