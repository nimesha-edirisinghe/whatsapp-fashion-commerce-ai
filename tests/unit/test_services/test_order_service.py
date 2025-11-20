"""Unit tests for order service."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.order_service import OrderService


class TestOrderService:
    """Tests for order service methods."""

    @pytest.fixture
    def order_service(self) -> OrderService:
        """Create order service instance."""
        return OrderService()

    @pytest.mark.asyncio
    async def test_get_order_by_id_found(self, order_service: OrderService):
        """Test retrieving existing order."""
        with patch("app.services.order_service.supabase") as mock_db:
            mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
                data={
                    "id": "ORD-2024-001234",
                    "customer_phone": "15559876543",
                    "status": "shipped",
                    "tracking_number": "TRK123456789",
                    "estimated_delivery": "2024-11-25",
                    "total_amount": 59.99,
                    "items": [
                        {"product_id": "prod-1", "name": "Floral Dress", "quantity": 1, "price": 59.99}
                    ],
                }
            )

            result = await order_service.get_order_by_id("ORD-2024-001234")

            assert result is not None
            assert result["id"] == "ORD-2024-001234"
            assert result["status"] == "shipped"
            assert result["tracking_number"] == "TRK123456789"

    @pytest.mark.asyncio
    async def test_get_order_by_id_not_found(self, order_service: OrderService):
        """Test retrieving non-existent order."""
        with patch("app.services.order_service.supabase") as mock_db:
            mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = Exception("No rows")

            result = await order_service.get_order_by_id("ORD-NONEXISTENT")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_orders_by_phone(self, order_service: OrderService):
        """Test retrieving all orders for a customer."""
        with patch("app.services.order_service.supabase") as mock_db:
            mock_db.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[
                    {"id": "ORD-001", "status": "delivered"},
                    {"id": "ORD-002", "status": "shipped"},
                ]
            )

            results = await order_service.get_orders_by_phone("15559876543")

            assert len(results) == 2

    @pytest.mark.asyncio
    async def test_is_valid_order_id_format(self, order_service: OrderService):
        """Test order ID format validation."""
        # Valid formats
        assert order_service.is_valid_order_id("ORD-2024-001234") is True
        assert order_service.is_valid_order_id("ORD-2024-000001") is True

        # Invalid formats
        assert order_service.is_valid_order_id("INVALID") is False
        assert order_service.is_valid_order_id("ORD-") is False
        assert order_service.is_valid_order_id("123456") is False
        assert order_service.is_valid_order_id("") is False

    @pytest.mark.asyncio
    async def test_extract_order_id_from_message(self, order_service: OrderService):
        """Test extracting order ID from message text."""
        # Direct order ID
        assert order_service.extract_order_id("ORD-2024-001234") == "ORD-2024-001234"

        # Order ID in sentence
        assert order_service.extract_order_id("My order is ORD-2024-001234") == "ORD-2024-001234"
        assert order_service.extract_order_id("Track ORD-2024-001234 please") == "ORD-2024-001234"

        # No order ID
        assert order_service.extract_order_id("Where is my order?") is None
        assert order_service.extract_order_id("Hello") is None

    @pytest.mark.asyncio
    async def test_get_order_handles_database_error(self, order_service: OrderService):
        """Test graceful handling of database errors."""
        with patch("app.services.order_service.supabase") as mock_db:
            mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = Exception("DB error")

            result = await order_service.get_order_by_id("ORD-2024-001234")

            assert result is None


class TestOrderStatusFormatting:
    """Tests for order status formatting."""

    @pytest.fixture
    def order_service(self) -> OrderService:
        """Create order service instance."""
        return OrderService()

    def test_format_order_status_shipped(self, order_service: OrderService):
        """Test formatting shipped order status."""
        order = {
            "id": "ORD-2024-001234",
            "status": "shipped",
            "tracking_number": "TRK123456789",
            "carrier": "FedEx",
            "estimated_delivery": "2024-11-25",
            "items": [
                {"name": "Floral Dress", "quantity": 1, "price": 59.99}
            ],
        }

        formatted = order_service.format_order_status(order)

        assert "ORD-2024-001234" in formatted
        assert "shipped" in formatted.lower()
        assert "TRK123456789" in formatted
        assert "FedEx" in formatted or "tracking" in formatted.lower()

    def test_format_order_status_pending(self, order_service: OrderService):
        """Test formatting pending order status."""
        order = {
            "id": "ORD-2024-001234",
            "status": "pending",
            "items": [],
        }

        formatted = order_service.format_order_status(order)

        assert "ORD-2024-001234" in formatted
        assert "pending" in formatted.lower()

    def test_format_order_status_delivered(self, order_service: OrderService):
        """Test formatting delivered order status."""
        order = {
            "id": "ORD-2024-001234",
            "status": "delivered",
            "delivered_at": "2024-11-20",
            "items": [],
        }

        formatted = order_service.format_order_status(order)

        assert "delivered" in formatted.lower()

    def test_format_order_not_found(self, order_service: OrderService):
        """Test formatting for order not found."""
        formatted = order_service.format_order_not_found("ORD-2024-999999")

        assert "ORD-2024-999999" in formatted
        assert "not found" in formatted.lower() or "couldn't find" in formatted.lower()

    def test_format_invalid_order_id(self, order_service: OrderService):
        """Test formatting for invalid order ID."""
        formatted = order_service.format_invalid_order_id()

        assert "ORD-" in formatted
        assert "format" in formatted.lower()


class TestOrderServiceEdgeCases:
    """Edge case tests for order service."""

    @pytest.fixture
    def order_service(self) -> OrderService:
        """Create order service instance."""
        return OrderService()

    @pytest.mark.asyncio
    async def test_order_with_multiple_items(self, order_service: OrderService):
        """Test order with multiple items."""
        with patch("app.services.order_service.supabase") as mock_db:
            mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
                data={
                    "id": "ORD-2024-001234",
                    "status": "processing",
                    "items": [
                        {"name": "Dress", "quantity": 2, "price": 59.99},
                        {"name": "Shirt", "quantity": 1, "price": 29.99},
                    ],
                }
            )

            result = await order_service.get_order_by_id("ORD-2024-001234")

            assert len(result["items"]) == 2

    def test_extract_order_id_case_insensitive(self, order_service: OrderService):
        """Test order ID extraction is case-insensitive."""
        # Should handle different cases
        assert order_service.extract_order_id("ord-2024-001234") == "ORD-2024-001234"
        assert order_service.extract_order_id("Ord-2024-001234") == "ORD-2024-001234"

    @pytest.mark.asyncio
    async def test_empty_orders_list(self, order_service: OrderService):
        """Test handling empty orders list."""
        with patch("app.services.order_service.supabase") as mock_db:
            mock_db.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[]
            )

            results = await order_service.get_orders_by_phone("15559876543")

            assert results == []
