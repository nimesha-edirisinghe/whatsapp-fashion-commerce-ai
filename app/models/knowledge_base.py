"""Knowledge base models."""

from datetime import datetime
from pydantic import BaseModel, Field


class KnowledgeBaseEntry(BaseModel):
    """Knowledge base entry for RAG."""
    id: str
    content: str
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    embedding: list[float] | None = None
    created_at: datetime
    updated_at: datetime


class KnowledgeBaseCreate(BaseModel):
    """Input model for creating knowledge base entry."""
    content: str
    category: str | None = None
    tags: list[str] = Field(default_factory=list)


class KnowledgeBaseSearchResult(BaseModel):
    """Search result from knowledge base."""
    id: str
    content: str
    category: str | None = None
    similarity: float
