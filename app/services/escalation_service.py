"""Escalation service for human handoff via n8n webhook."""

from datetime import datetime
from typing import Any

import httpx

from app.config import settings
from app.core.logging import logger
from app.models.catalog import EscalationPayload
from app.utils.retry import async_retry


class EscalationService:
    """Service for escalating conversations to human agents."""

    CONFIDENCE_THRESHOLD = 0.7  # 70% threshold for auto-escalation

    @async_retry(attempts=1, timeout=5.0)
    async def escalate_to_human(
        self,
        customer_phone: str,
        reason: str,
        confidence_score: float | None = None,
        last_message: str | None = None,
        conversation_history: list[dict] | None = None,
        metadata: dict | None = None,
    ) -> bool:
        """
        Escalate conversation to human agent via n8n webhook.

        Args:
            customer_phone: Customer phone number
            reason: Reason for escalation
            confidence_score: AI confidence score (0-1)
            last_message: Last message from customer
            conversation_history: Recent conversation messages
            metadata: Additional context

        Returns:
            True if escalation successful
        """
        if not settings.n8n_webhook_url:
            logger.warning("n8n webhook URL not configured, skipping escalation")
            return False

        payload = EscalationPayload(
            customer_phone=customer_phone,
            reason=reason,
            confidence_score=confidence_score,
            last_message=last_message,
            conversation_history=conversation_history or [],
            metadata=metadata or {},
            timestamp=datetime.utcnow(),
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.n8n_webhook_url,
                    json=payload.model_dump(mode="json"),
                    headers={
                        "Content-Type": "application/json",
                        "X-Webhook-Secret": settings.n8n_webhook_secret or "",
                    },
                    timeout=5.0,
                )

                if response.status_code == 200:
                    logger.info(
                        f"Escalation successful for {customer_phone}: {reason}"
                    )
                    return True
                else:
                    logger.error(
                        f"Escalation webhook failed: {response.status_code} - {response.text}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Escalation failed: {e}")
            return False

    def should_escalate(
        self,
        confidence_score: float | None,
        explicit_request: bool = False,
    ) -> tuple[bool, str]:
        """
        Determine if conversation should be escalated.

        Args:
            confidence_score: AI confidence score (0-1)
            explicit_request: User explicitly asked for human

        Returns:
            Tuple of (should_escalate, reason)
        """
        if explicit_request:
            return True, "Customer requested human assistance"

        if confidence_score is not None and confidence_score < self.CONFIDENCE_THRESHOLD:
            return True, f"Low confidence score: {confidence_score:.2f}"

        return False, ""

    def detect_escalation_request(self, message: str) -> bool:
        """
        Detect if user is requesting human assistance.

        Args:
            message: User message

        Returns:
            True if user wants to talk to human
        """
        message_lower = message.lower()

        escalation_phrases = [
            "talk to human",
            "speak to human",
            "human agent",
            "real person",
            "customer service",
            "support agent",
            "talk to someone",
            "speak to someone",
            "representative",
            "help me please",
            "need help",
            "agent please",
        ]

        return any(phrase in message_lower for phrase in escalation_phrases)

    def get_escalation_message(self) -> str:
        """Get message to send when escalating to human."""
        return (
            "🙋 I'm connecting you with a human agent who can better assist you.\n\n"
            "A team member will respond shortly during business hours "
            "(Mon-Fri 9AM-6PM EST).\n\n"
            "In the meantime, you can continue to send messages and I'll "
            "make sure they see your full conversation."
        )


# Singleton instance
escalation_service = EscalationService()
