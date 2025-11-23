import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class DummyAuthMiddleware(BaseHTTPMiddleware):
    """
    Dummy authentication middleware that checks for optional API key header.
    """
    async def dispatch(self, request: Request, call_next):
        # Skip auth for health check endpoint
        if request.url.path == "/health":
            return await call_next(request)
        
        # Check for dummy API key header (optional - doesn't block if missing)
        api_key = request.headers.get("X-API-Key")
        
        if api_key:
            # In a real implementation, validate the API key
            logger.info(f"API Key provided: {api_key[:8]}...")
        else:
            logger.debug("No API key provided (optional)")
        
        return await call_next(request)

