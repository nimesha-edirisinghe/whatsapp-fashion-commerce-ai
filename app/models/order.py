"""Order models."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    """Order status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderItem(BaseModel):
    """Individual item in an order."""
    product_id: str
    name: str
    quantity: int
    price: float
    size: str | None = None
    color: str | None = None


class Order(BaseModel):
    """Order entity."""
    id: str
    customer_phone: str
    status: OrderStatus
    total_amount: float
    currency: str = "USD"
    items: list[OrderItem] = Field(default_factory=list)
    tracking_number: str | None = None
    carrier: str | None = None
    estimated_delivery: str | None = None
    delivered_at: str | None = None
    shipping_address: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class OrderCreate(BaseModel):
    """Input model for creating an order."""
    customer_phone: str
    items: list[OrderItem]
    shipping_address: str
    notes: str | None = None


class OrderUpdate(BaseModel):
    """Input model for updating an order."""
    status: OrderStatus | None = None
    tracking_number: str | None = None
    carrier: str | None = None
    estimated_delivery: str | None = None
    delivered_at: str | None = None
    notes: str | None = None
