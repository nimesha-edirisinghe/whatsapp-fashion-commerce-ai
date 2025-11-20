"""Session service for conversation history management."""

import json

from app.core.logging import logger
from app.core.redis import redis_client


class SessionService:
    """Service for managing conversation history in Redis."""

    SESSION_PREFIX = "session:"
    MAX_MESSAGES = 10
    TTL_SECONDS = 86400  # 24 hours

    async def get_context(self, customer_phone: str) -> list[dict[str, str]]:
        """
        Get conversation history for a customer.

        Args:
            customer_phone: Customer WhatsApp number

        Returns:
            List of message dicts with role and content (last 10 messages)
        """
        try:
            key = f"{self.SESSION_PREFIX}{customer_phone}"
            messages = await redis_client.lrange(key, -self.MAX_MESSAGES, -1)

            context = []
            for msg in messages:
                try:
                    parsed = json.loads(msg)
                    context.append(parsed)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in session history: {msg[:100]}")
                    continue

            return context
        except Exception as e:
            logger.error(f"Failed to get session context: {e}")
            return []

    async def add_message(
        self,
        customer_phone: str,
        role: str,
        content: str,
    ) -> None:
        """
        Add a message to conversation history.

        Args:
            customer_phone: Customer WhatsApp number
            role: Message role (user or assistant)
            content: Message content
        """
        try:
            key = f"{self.SESSION_PREFIX}{customer_phone}"
            message = json.dumps({"role": role, "content": content})

            # Add message to list
            await redis_client.rpush(key, message)

            # Trim to keep only last N messages
            await redis_client.ltrim(key, -self.MAX_MESSAGES, -1)

            # Set/refresh TTL
            await redis_client.expire(key, self.TTL_SECONDS)

        except Exception as e:
            logger.error(f"Failed to add message to session: {e}")

    async def clear_context(self, customer_phone: str) -> None:
        """
        Clear conversation history for a customer.

        Args:
            customer_phone: Customer WhatsApp number
        """
        try:
            key = f"{self.SESSION_PREFIX}{customer_phone}"
            await redis_client.delete(key)
        except Exception as e:
            logger.error(f"Failed to clear session context: {e}")

    def format_for_llm(self, context: list[dict[str, str]]) -> list[dict[str, str]]:
        """
        Format context for LLM consumption.

        Args:
            context: List of message dicts

        Returns:
            Formatted messages for OpenAI chat completion
        """
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in context
        ]


# Singleton instance
session_service = SessionService()
