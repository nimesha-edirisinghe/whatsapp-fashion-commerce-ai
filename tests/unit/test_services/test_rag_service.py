"""Unit tests for RAG service."""

from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import DatabaseError
from app.services.rag_service import RAGService


class TestRAGService:
    """Tests for RAG service methods."""

    @pytest.fixture
    def rag_service(self) -> RAGService:
        """Create RAG service instance."""
        return RAGService()

    @pytest.mark.asyncio
    async def test_create_embedding_success(self, rag_service: RAGService):
        """Test successful embedding creation."""
        with patch("app.services.rag_service.create_embedding") as mock_embed:
            mock_embed.return_value = [0.1] * 1536  # OpenAI embedding dimension

            result = await rag_service.create_query_embedding("test query")

            assert len(result) == 1536
            mock_embed.assert_called_once_with("test query")

    @pytest.mark.asyncio
    async def test_create_embedding_failure_raises(self, rag_service: RAGService):
        """Test embedding creation failure handling."""
        with patch("app.services.rag_service.create_embedding") as mock_embed:
            mock_embed.side_effect = Exception("API error")

            with pytest.raises(Exception, match="API error"):
                await rag_service.create_query_embedding("test query")

    @pytest.mark.asyncio
    async def test_search_knowledge_base_with_results(self, rag_service: RAGService):
        """Test knowledge base search returns matching documents."""
        with patch("app.services.rag_service.create_embedding") as mock_embed, \
             patch("app.services.rag_service.supabase") as mock_db:

            mock_embed.return_value = [0.1] * 1536
            mock_db.rpc.return_value.execute.return_value = MagicMock(
                data=[
                    {
                        "id": "kb-1",
                        "content": "Dress sizes run from XS to XXL",
                        "similarity": 0.92,
                    },
                    {
                        "id": "kb-2",
                        "content": "Returns accepted within 30 days",
                        "similarity": 0.85,
                    },
                ]
            )

            results = await rag_service.search_knowledge_base(
                "What sizes are available?",
                limit=5,
            )

            assert len(results) == 2
            assert results[0]["similarity"] == 0.92
            assert "sizes" in results[0]["content"].lower()

    @pytest.mark.asyncio
    async def test_search_knowledge_base_empty_results(self, rag_service: RAGService):
        """Test knowledge base search with no matches."""
        with patch("app.services.rag_service.create_embedding") as mock_embed, \
             patch("app.services.rag_service.supabase") as mock_db:

            mock_embed.return_value = [0.1] * 1536
            mock_db.rpc.return_value.execute.return_value = MagicMock(data=[])

            results = await rag_service.search_knowledge_base(
                "Something completely unrelated",
                limit=5,
            )

            assert results == []

    @pytest.mark.asyncio
    async def test_search_knowledge_base_respects_threshold(
        self, rag_service: RAGService
    ):
        """Test that similarity threshold filters results."""
        with patch("app.services.rag_service.create_embedding") as mock_embed, \
             patch("app.services.rag_service.supabase") as mock_db:

            mock_embed.return_value = [0.1] * 1536
            # Only high similarity results returned by RPC
            mock_db.rpc.return_value.execute.return_value = MagicMock(
                data=[
                    {"id": "kb-1", "content": "High match", "similarity": 0.9},
                ]
            )

            await rag_service.search_knowledge_base(
                "test query",
                limit=5,
                threshold=0.8,
            )

            # Verify RPC was called with threshold
            mock_db.rpc.assert_called_once()
            call_args = mock_db.rpc.call_args
            # RPC is called with positional args: rpc("match_knowledge_base", {...})
            assert call_args[0][1]["match_threshold"] == 0.8

    @pytest.mark.asyncio
    async def test_search_knowledge_base_respects_limit(self, rag_service: RAGService):
        """Test that result limit is enforced."""
        with patch("app.services.rag_service.create_embedding") as mock_embed, \
             patch("app.services.rag_service.supabase") as mock_db:

            mock_embed.return_value = [0.1] * 1536
            mock_db.rpc.return_value.execute.return_value = MagicMock(
                data=[
                    {"id": f"kb-{i}", "content": f"Result {i}", "similarity": 0.9 - i * 0.01}
                    for i in range(3)
                ]
            )

            results = await rag_service.search_knowledge_base(
                "test query",
                limit=3,
            )

            assert len(results) <= 3
            # Verify limit was passed to RPC
            call_args = mock_db.rpc.call_args
            # RPC is called with positional args: rpc("match_knowledge_base", {...})
            assert call_args[0][1]["match_count"] == 3

    @pytest.mark.asyncio
    async def test_search_handles_database_error(self, rag_service: RAGService):
        """Test graceful handling of database errors."""
        with patch("app.services.rag_service.create_embedding") as mock_embed, \
             patch("app.services.rag_service.supabase") as mock_db:

            mock_embed.return_value = [0.1] * 1536
            mock_db.rpc.return_value.execute.side_effect = Exception("DB error")

            with pytest.raises(DatabaseError):
                await rag_service.search_knowledge_base("test query")

    @pytest.mark.asyncio
    async def test_format_context_for_prompt(self, rag_service: RAGService):
        """Test formatting of retrieved documents for prompt context."""
        documents = [
            {"content": "Document 1 content", "similarity": 0.95},
            {"content": "Document 2 content", "similarity": 0.85},
        ]

        context = rag_service.format_context(documents)

        assert "Document 1 content" in context
        assert "Document 2 content" in context
        assert isinstance(context, str)

    def test_format_context_empty_documents(self, rag_service: RAGService):
        """Test formatting with no documents."""
        context = rag_service.format_context([])

        assert context == ""

    @pytest.mark.asyncio
    async def test_search_with_retry_on_timeout(self, rag_service: RAGService):
        """Test that search raises on persistent failure."""
        with patch("app.services.rag_service.create_embedding") as mock_embed, \
             patch("app.services.rag_service.supabase") as mock_db:

            mock_embed.return_value = [0.1] * 1536
            # Both attempts fail
            mock_db.rpc.return_value.execute.side_effect = Exception("Timeout")

            # Should raise DatabaseError after all retries exhausted
            with pytest.raises(DatabaseError):
                await rag_service.search_knowledge_base("test query")


class TestRAGServiceEdgeCases:
    """Edge case tests for RAG service."""

    @pytest.fixture
    def rag_service(self) -> RAGService:
        """Create RAG service instance."""
        return RAGService()

    @pytest.mark.asyncio
    async def test_empty_query_handling(self, rag_service: RAGService):
        """Test handling of empty query string."""
        with patch("app.services.rag_service.create_embedding") as mock_embed:
            mock_embed.return_value = [0.1] * 1536

            # Should still process empty query
            with patch("app.services.rag_service.supabase") as mock_db:
                mock_db.rpc.return_value.execute.return_value = MagicMock(data=[])

                results = await rag_service.search_knowledge_base("")
                assert results == []

    @pytest.mark.asyncio
    async def test_special_characters_in_query(self, rag_service: RAGService):
        """Test handling of special characters in query."""
        with patch("app.services.rag_service.create_embedding") as mock_embed, \
             patch("app.services.rag_service.supabase") as mock_db:

            mock_embed.return_value = [0.1] * 1536
            mock_db.rpc.return_value.execute.return_value = MagicMock(data=[])

            # Should handle special chars without error
            results = await rag_service.search_knowledge_base(
                "What's the price? 100% cotton!"
            )
            assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_unicode_query_handling(self, rag_service: RAGService):
        """Test handling of unicode/emoji in queries."""
        with patch("app.services.rag_service.create_embedding") as mock_embed, \
             patch("app.services.rag_service.supabase") as mock_db:

            mock_embed.return_value = [0.1] * 1536
            mock_db.rpc.return_value.execute.return_value = MagicMock(data=[])

            results = await rag_service.search_knowledge_base(
                "¿Tienen vestidos? 👗"
            )
            assert isinstance(results, list)
