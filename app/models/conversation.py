"""Conversation and session models."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class MessageRecord(BaseModel):
    """Individual message in conversation history."""
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime
    products_mentioned: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionContext(BaseModel):
    """Current session context for a customer."""
    last_product_id: str | None = None
    last_intent: str | None = None
    language: str = "en"
    metadata: dict[str, Any] = Field(default_factory=dict)


class Conversation(BaseModel):
    """Conversation record for analytics."""
    id: str | None = None
    customer_phone: str
    message_type: Literal["text", "image", "interactive"]
    direction: Literal["inbound", "outbound"]
    content: str | None = None
    intent: str | None = None
    confidence_score: float | None = Field(default=None, ge=0, le=1)
    response_time_ms: int | None = None
    escalated: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    """Input for creating a conversation record."""
    customer_phone: str
    message_type: Literal["text", "image", "interactive"]
    direction: Literal["inbound", "outbound"]
    content: str | None = None
    intent: str | None = None
    confidence_score: float | None = Field(default=None, ge=0, le=1)
    response_time_ms: int | None = None
    escalated: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
