"""Conversation logging service for analytics."""

from datetime import datetime
from typing import Any

from app.core.database import supabase
from app.core.logging import logger
from app.models.conversation import ConversationCreate


class ConversationService:
    """Service for logging conversations for analytics."""

    async def log_message(
        self,
        customer_phone: str,
        message_type: str,
        direction: str,
        content: str | None = None,
        intent: str | None = None,
        confidence_score: float | None = None,
        response_time_ms: int | None = None,
        escalated: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> str | None:
        """
        Log a conversation message for analytics.

        Args:
            customer_phone: Customer WhatsApp number
            message_type: text, image, interactive
            direction: inbound or outbound
            content: Message content
            intent: Detected intent
            confidence_score: AI confidence (0-1)
            response_time_ms: Processing time
            escalated: Whether escalated to human
            metadata: Additional context

        Returns:
            Created conversation ID or None on error
        """
        try:
            data = {
                "customer_phone": customer_phone,
                "message_type": message_type,
                "direction": direction,
                "content": content,
                "intent": intent,
                "confidence_score": confidence_score,
                "response_time_ms": response_time_ms,
                "escalated": escalated,
                "metadata": metadata or {},
            }

            result = supabase.table("conversations").insert(data).execute()

            if result.data:
                return result.data[0].get("id")
            return None
        except Exception as e:
            logger.error(f"Failed to log conversation: {e}")
            return None

    async def log_visual_search(
        self,
        customer_phone: str,
        attributes: dict[str, Any],
        products_found: int,
        response_time_ms: int,
    ) -> str | None:
        """Log a visual search interaction."""
        return await self.log_message(
            customer_phone=customer_phone,
            message_type="image",
            direction="inbound",
            intent="visual_search",
            response_time_ms=response_time_ms,
            metadata={
                "attributes": attributes,
                "products_found": products_found,
            },
        )


# Singleton instance
conversation_service = ConversationService()
