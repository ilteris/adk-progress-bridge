import os
from typing import Optional, Union
from fastapi import Request, HTTPException, Security, status, WebSocket
from fastapi.security import APIKeyHeader
from .logger import logger

# Configuration
API_KEY_NAME = "X-API-Key"
BRIDGE_API_KEY = os.getenv("BRIDGE_API_KEY")

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(
    api_key_or_header: Union[str, Request, None] = Security(api_key_header),
):
    """
    Universal dependency that validates the API Key.
    Can be used as a Depends() or called directly.
    """
    if not BRIDGE_API_KEY:
        return True

    # Case 1: Called from Depends(verify_api_key) with header
    if isinstance(api_key_or_header, str):
        if api_key_or_header == BRIDGE_API_KEY:
            return True
    
    # Case 2: Called from within a function with a direct string
    # (e.g. await verify_api_key(api_key_from_query))
    if isinstance(api_key_or_header, str) and api_key_or_header == BRIDGE_API_KEY:
        return True

    # Case 3: If called with a Request object (unlikely here but for robustness)
    if isinstance(api_key_or_header, Request):
        api_key = api_key_or_header.query_params.get("api_key") or api_key_or_header.headers.get(API_KEY_NAME)
        if api_key == BRIDGE_API_KEY:
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
