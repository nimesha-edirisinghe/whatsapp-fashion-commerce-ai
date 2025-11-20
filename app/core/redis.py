"""Async Upstash Redis client."""

import json
from typing import Any

from redis.asyncio import Redis

from app.config import settings
from app.core.logging import logger


def get_redis_client() -> Redis[bytes]:
    """Get Redis client instance."""
    return Redis.from_url(
        settings.upstash_redis_url,
        encoding="utf-8",
        decode_responses=True,
    )


# Convenience instance
redis_client = get_redis_client()


async def check_redis_connection() -> bool:
    """Check if Redis connection is healthy."""
    try:
        await redis_client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis connection check failed: {e}")
        return False


async def get_session_messages(phone: str) -> list[dict[str, Any]]:
    """Get last 10 messages for a customer session."""
    key = f"session:{phone}:messages"
    messages = await redis_client.lrange(key, -10, -1)
    return [json.loads(m) for m in messages]


async def add_session_message(phone: str, message: dict[str, Any]) -> None:
    """Add message to customer session history."""
    key = f"session:{phone}:messages"
    await redis_client.rpush(key, json.dumps(message))
    await redis_client.ltrim(key, -10, -1)  # Keep only last 10
    await redis_client.expire(key, 86400)  # 24h TTL


async def get_session_context(phone: str) -> dict[str, Any]:
    """Get current session context for a customer."""
    key = f"session:{phone}:context"
    context = await redis_client.hgetall(key)
    return context or {}


async def set_session_context(phone: str, context: dict[str, Any]) -> None:
    """Set session context for a customer."""
    key = f"session:{phone}:context"
    await redis_client.hset(key, mapping=context)
    await redis_client.expire(key, 86400)  # 24h TTL


async def clear_session(phone: str) -> None:
    """Clear all session data for a customer."""
    await redis_client.delete(f"session:{phone}:messages", f"session:{phone}:context")
