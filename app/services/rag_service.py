"""RAG service for knowledge base search."""

from typing import Any

from app.core.database import supabase
from app.core.exceptions import DatabaseError
from app.core.logging import logger
from app.core.openai_client import create_embedding
from app.utils.retry import async_retry


class RAGService:
    """Service for RAG-based knowledge retrieval."""

    @async_retry(attempts=1, timeout=3.0)
    async def create_query_embedding(self, query: str) -> list[float]:
        """
        Create embedding for a search query.

        Args:
            query: Search query text

        Returns:
            Embedding vector (1536 dimensions)
        """
        return await create_embedding(query)

    @async_retry(attempts=1, timeout=3.0)
    async def search_knowledge_base(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        """
        Search knowledge base using vector similarity.

        Args:
            query: Search query
            limit: Maximum results to return
            threshold: Minimum similarity threshold

        Returns:
            List of matching documents with similarity scores
        """
        try:
            # Create embedding for query
            embedding = await self.create_query_embedding(query)

            # Search using Supabase RPC function
            result = supabase.rpc(
                "match_knowledge_base",
                {
                    "query_embedding": embedding,
                    "match_threshold": threshold,
                    "match_count": limit,
                },
            ).execute()

            return result.data or []
        except Exception as e:
            logger.error(f"Knowledge base search failed: {e}")
            raise DatabaseError(f"Knowledge base search failed: {e}") from e

    def format_context(self, documents: list[dict[str, Any]]) -> str:
        """
        Format retrieved documents for LLM context.

        Args:
            documents: List of retrieved documents

        Returns:
            Formatted context string
        """
        if not documents:
            return ""

        context_parts = []
        for doc in documents:
            content = doc.get("content", "")
            if content:
                context_parts.append(content)

        return "\n\n".join(context_parts)

    async def get_relevant_context(
        self,
        query: str,
        limit: int = 3,
    ) -> str:
        """
        Get formatted relevant context for a query.

        Convenience method that searches and formats in one call.

        Args:
            query: User query
            limit: Max documents to retrieve

        Returns:
            Formatted context string
        """
        try:
            documents = await self.search_knowledge_base(query, limit=limit)
            return self.format_context(documents)
        except Exception as e:
            logger.error(f"Failed to get relevant context: {e}")
            return ""


# Singleton instance
rag_service = RAGService()
