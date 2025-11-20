"""Product entity models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    """Base product fields."""
    name: str = Field(max_length=255)
    description: str | None = None
    price: float = Field(gt=0)
    currency: str = Field(default="USD", max_length=3)
    supplier_url: str | None = None
    image_urls: list[str] = Field(min_length=1)
    sizes: list[str] = Field(min_length=1)
    colors: list[str] = Field(min_length=1)
    inventory_count: int = Field(default=0, ge=0)
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class ProductInput(ProductBase):
    """Product input for creation/update."""
    id: str | None = None  # Optional for updates


class Product(ProductBase):
    """Complete product entity from database."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductSearchResult(BaseModel):
    """Product search result with similarity score."""
    product: Product
    similarity: float = Field(ge=0, le=1)


class ProductListResponse(BaseModel):
    """Response containing list of products."""
    products: list[Product]
    total: int
    page: int = 1
    page_size: int = 10
