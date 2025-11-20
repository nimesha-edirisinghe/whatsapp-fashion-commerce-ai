"""Async Supabase client initialization."""

from functools import lru_cache

from supabase import Client, create_client

from app.config import settings
from app.core.logging import logger


@lru_cache
def get_supabase_client() -> Client:
    """Get cached Supabase client instance using service role key."""
    logger.info("Initializing Supabase client")
    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )


# Convenience instance
supabase = get_supabase_client()


async def check_database_connection() -> bool:
    """Check if database connection is healthy."""
    try:
        # Simple query to verify connection
        supabase.table("products").select("id").limit(1).execute()
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False
