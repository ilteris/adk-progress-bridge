import os
from typing import Optional
from fastapi import Request, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from .logger import logger

# Configuration
API_KEY_NAME = "X-API-Key"
# For demo purposes, we allow configuring a static API key via env var.
# In a real app, this might involve database lookups or JWT validation.
BRIDGE_API_KEY = os.getenv("BRIDGE_API_KEY")

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(
    api_key_header: str = Security(api_key_header),
):
    """
    Dependency that validates the API Key.
    If BRIDGE_API_KEY is not set, authentication is bypassed (disabled).
    """
    if not BRIDGE_API_KEY:
        return None

    if api_key_header == BRIDGE_API_KEY:
        return api_key_header
    
    logger.warning("Invalid API Key provided")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
        headers={"WWW-Authenticate": API_KEY_NAME},
    )

async def verify_api_key_sse(request: Request):
    """
    Validates API key for SSE requests.
    Since EventSource doesn't support custom headers easily, 
    we allow the key to be passed via a query parameter 'api_key'.
    """
    if not BRIDGE_API_KEY:
        return
    
    api_key = request.query_params.get("api_key")
    if not api_key:
        # Fallback to header if user is using a custom SSE client that supports headers
        api_key = request.headers.get(API_KEY_NAME)
        
    if api_key == BRIDGE_API_KEY:
        return
    
    logger.warning("Invalid API Key provided for stream")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )
