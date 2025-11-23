import os
from typing import Optional
from supabase import create_client, Client
from supabase.client import ClientOptions
import logging
import httpx

logger = logging.getLogger(__name__)

# Singleton instances
_supabase_client: Optional[Client] = None
_supabase_storage: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get or create a singleton Supabase client with service role key.
    This client has admin privileges and bypasses RLS.
    Configured with increased timeouts for file uploads.
    """
    global _supabase_client
    
    if _supabase_client is None:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_service_role_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment variables"
            )
        
        # Create custom httpx client with increased timeouts for file uploads
        # Default timeout is 5 seconds, which is too short for file uploads
        # Set to 60 seconds for connect, 300 seconds (5 minutes) for read/write operations
        timeout = httpx.Timeout(
            connect=60.0,  # Time to establish connection
            read=300.0,    # Time to read response (for uploads)
            write=300.0,   # Time to write request (for uploads)
            pool=60.0      # Time to get connection from pool
        )
        
        http_client = httpx.Client(timeout=timeout)
        
        # Try to create client with custom http_client, fallback to default if not supported
        try:
            _supabase_client = create_client(
                supabase_url,
                supabase_service_role_key,
                options=ClientOptions(
                    auto_refresh_token=False,
                    persist_session=False,
                    http_client=http_client
                )
            )
            logger.info("Supabase client initialized with extended timeouts")
        except TypeError:
            # If http_client parameter is not supported, use default client
            # Timeouts will be handled by asyncio.wait_for in the upload function
            logger.warning("Custom http_client not supported, using default client. Timeouts handled by asyncio.")
            _supabase_client = create_client(
                supabase_url,
                supabase_service_role_key,
                options=ClientOptions(
                    auto_refresh_token=False,
                    persist_session=False
                )
            )
            logger.info("Supabase client initialized with default settings")
    
    return _supabase_client


def get_supabase_storage() -> Client:
    """
    Get Supabase storage client (same as main client but for clarity).
    """
    return get_supabase_client()

