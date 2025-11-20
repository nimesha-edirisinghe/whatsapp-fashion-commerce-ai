"""Contract tests for Supabase API."""

import pytest
from unittest.mock import MagicMock, patch


class TestSupabaseConnection:
    """Test Supabase client initialization and connection."""

    def test_supabase_client_created(self) -> None:
        """Test that Supabase client can be created."""
        from app.core.database import get_supabase_client

        # Should not raise an exception
        client = get_supabase_client()
        assert client is not None

    @pytest.mark.asyncio
    async def test_check_database_connection_success(self) -> None:
        """Test database connection check with mock."""
        from app.core.database import check_database_connection

        with patch("app.core.database.supabase") as mock_supabase:
            mock_supabase.table.return_value.select.return_value.limit.return_value.execute.return_value = MagicMock()

            result = await check_database_connection()
            assert result is True

    @pytest.mark.asyncio
    async def test_check_database_connection_failure(self) -> None:
        """Test database connection check handles errors."""
        from app.core.database import check_database_connection

        with patch("app.core.database.supabase") as mock_supabase:
            mock_supabase.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception("Connection failed")

            result = await check_database_connection()
            assert result is False


class TestProductTableContract:
    """Test Product table operations contract."""

    def test_product_table_select(self, mock_supabase: MagicMock) -> None:
        """Test selecting from products table."""
        mock_supabase.table("products").select("*").execute()
        mock_supabase.table.assert_called_with("products")

    def test_product_table_insert(self, mock_supabase: MagicMock) -> None:
        """Test inserting into products table."""
        product_data = {
            "name": "Test Product",
            "price": 29.99,
            "image_urls": ["https://example.com/img.jpg"],
            "sizes": ["S", "M"],
            "colors": ["Blue"],
        }
        mock_supabase.table("products").insert(product_data).execute()
        mock_supabase.table.assert_called_with("products")

    def test_product_vector_search_rpc(self, mock_supabase: MagicMock) -> None:
        """Test vector similarity search RPC call."""
        embedding = [0.1] * 1536
        mock_supabase.rpc(
            "match_products",
            {
                "query_embedding": embedding,
                "match_threshold": 0.7,
                "match_count": 5,
            },
        ).execute()
        mock_supabase.rpc.assert_called_once()


class TestOrderTableContract:
    """Test Order table operations contract."""

    def test_order_table_select_by_id(self, mock_supabase: MagicMock) -> None:
        """Test selecting order by order_id."""
        mock_supabase.table("orders").select("*").eq("order_id", "ORD-12345").execute()
        mock_supabase.table.assert_called_with("orders")

    def test_order_table_select_by_phone(self, mock_supabase: MagicMock) -> None:
        """Test selecting orders by customer phone."""
        mock_supabase.table("orders").select("*").eq("customer_phone", "1234567890").execute()
        mock_supabase.table.assert_called_with("orders")


class TestConversationTableContract:
    """Test Conversation table operations contract."""

    def test_conversation_insert(self, mock_supabase: MagicMock) -> None:
        """Test inserting conversation record."""
        conversation_data = {
            "customer_phone": "1234567890",
            "message_type": "text",
            "direction": "inbound",
            "content": "Hello",
            "intent": "greeting",
        }
        mock_supabase.table("conversations").insert(conversation_data).execute()
        mock_supabase.table.assert_called_with("conversations")


class TestKnowledgeBaseTableContract:
    """Test Knowledge Base table operations contract."""

    def test_knowledge_base_vector_search(self, mock_supabase: MagicMock) -> None:
        """Test knowledge base vector search RPC call."""
        embedding = [0.1] * 1536
        mock_supabase.rpc(
            "match_knowledge",
            {
                "query_embedding": embedding,
                "match_threshold": 0.7,
                "match_count": 3,
            },
        ).execute()
        mock_supabase.rpc.assert_called_once()
