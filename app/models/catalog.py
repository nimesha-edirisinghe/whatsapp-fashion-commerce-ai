"""Catalog sync models for n8n integration."""

from datetime import datetime
from pydantic import BaseModel, Field


class CatalogProduct(BaseModel):
    """Product data for catalog sync."""
    id: str
    name: str
    description: str | None = None
    price: float
    currency: str = "USD"
    category: str | None = None
    sizes: list[str] = Field(default_factory=list)
    colors: list[str] = Field(default_factory=list)
    image_urls: list[str] = Field(default_factory=list)
    supplier_url: str | None = None
    inventory_count: int = 0
    tags: list[str] = Field(default_factory=list)
    is_active: bool = True
    on_sale: bool = False
    original_price: float | None = None


class CatalogSyncPayload(BaseModel):
    """Payload for catalog sync from n8n."""
    products: list[CatalogProduct]
    source: str = "n8n"
    sync_mode: str = "upsert"  # upsert, replace, append


class CatalogSyncResponse(BaseModel):
    """Response for catalog sync operation."""
    success: bool
    message: str
    products_processed: int
    products_created: int
    products_updated: int
    products_failed: int
    errors: list[str] = Field(default_factory=list)
    sync_id: str | None = None
    completed_at: datetime


class EscalationPayload(BaseModel):
    """Payload for human escalation webhook."""
    customer_phone: str
    conversation_id: str | None = None
    reason: str
    confidence_score: float | None = None
    last_message: str | None = None
    conversation_history: list[dict] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    timestamp: datetime
