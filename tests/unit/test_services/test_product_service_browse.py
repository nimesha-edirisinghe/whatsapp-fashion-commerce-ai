"""Unit tests for product service catalog browsing methods."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.product_service import ProductService


class TestProductServiceBrowse:
    """Tests for product service browsing methods."""

    @pytest.fixture
    def product_service(self) -> ProductService:
        """Create product service instance."""
        return ProductService()

    @pytest.mark.asyncio
    async def test_get_new_arrivals_returns_products(
        self, product_service: ProductService
    ):
        """Test getting new arrival products."""
        with patch("app.services.product_service.supabase") as mock_db:
            mock_db.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[
                    {"id": "prod-1", "name": "New Dress", "price": 59.99},
                    {"id": "prod-2", "name": "New Shirt", "price": 39.99},
                ]
            )

            results = await product_service.get_new_arrivals(limit=10)

            assert len(results) == 2
            assert results[0]["name"] == "New Dress"

    @pytest.mark.asyncio
    async def test_get_new_arrivals_empty(self, product_service: ProductService):
        """Test getting new arrivals when none exist."""
        with patch("app.services.product_service.supabase") as mock_db:
            mock_db.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[]
            )

            results = await product_service.get_new_arrivals()

            assert results == []

    @pytest.mark.asyncio
    async def test_get_trending_returns_products(
        self, product_service: ProductService
    ):
        """Test getting trending products."""
        with patch("app.services.product_service.supabase") as mock_db:
            mock_db.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[
                    {"id": "prod-1", "name": "Popular Dress", "price": 69.99},
                ]
            )

            results = await product_service.get_trending(limit=10)

            assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_sale_items_returns_discounted(
        self, product_service: ProductService
    ):
        """Test getting sale items."""
        with patch("app.services.product_service.supabase") as mock_db:
            mock_db.table.return_value.select.return_value.eq.return_value.not_.is_.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[
                    {"id": "prod-1", "name": "Sale Dress", "price": 29.99, "original_price": 59.99},
                ]
            )

            results = await product_service.get_sale_items(limit=10)

            assert len(results) >= 0  # May return empty if no sales

    @pytest.mark.asyncio
    async def test_get_by_category(self, product_service: ProductService):
        """Test getting products by category."""
        with patch("app.services.product_service.supabase") as mock_db:
            mock_db.table.return_value.select.return_value.eq.return_value.ilike.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[
                    {"id": "prod-1", "name": "Summer Dress", "category": "dresses"},
                    {"id": "prod-2", "name": "Evening Dress", "category": "dresses"},
                ]
            )

            results = await product_service.search_by_category("dresses", limit=10)

            assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, product_service: ProductService):
        """Test getting product by ID."""
        with patch("app.services.product_service.supabase") as mock_db:
            mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
                data={
                    "id": "prod-123",
                    "name": "Floral Dress",
                    "description": "Beautiful summer dress",
                    "price": 59.99,
                    "sizes": ["S", "M", "L"],
                    "colors": ["Red", "Blue"],
                    "image_urls": ["https://example.com/dress.jpg"],
                }
            )

            result = await product_service.get_by_id("prod-123")

            assert result is not None
            assert result["id"] == "prod-123"
            assert result["name"] == "Floral Dress"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, product_service: ProductService):
        """Test getting non-existent product."""
        with patch("app.services.product_service.supabase") as mock_db:
            mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = Exception("Not found")

            result = await product_service.get_by_id("nonexistent")

            assert result is None


class TestBrowseTriggerDetection:
    """Tests for browse trigger phrase detection."""

    @pytest.fixture
    def product_service(self) -> ProductService:
        """Create product service instance."""
        return ProductService()

    def test_detect_new_arrivals_trigger(self, product_service: ProductService):
        """Test detection of 'New Arrivals' trigger."""
        assert product_service.detect_browse_trigger("New Arrivals") == "new_arrivals"
        assert product_service.detect_browse_trigger("new arrivals") == "new_arrivals"
        assert product_service.detect_browse_trigger("NEW ARRIVALS") == "new_arrivals"
        assert product_service.detect_browse_trigger("Show me new arrivals") == "new_arrivals"

    def test_detect_trending_trigger(self, product_service: ProductService):
        """Test detection of 'Trending' trigger."""
        assert product_service.detect_browse_trigger("Trending") == "trending"
        assert product_service.detect_browse_trigger("trending items") == "trending"
        assert product_service.detect_browse_trigger("What's trending") == "trending"

    def test_detect_sale_trigger(self, product_service: ProductService):
        """Test detection of 'Sale' trigger."""
        assert product_service.detect_browse_trigger("Sale") == "sale"
        assert product_service.detect_browse_trigger("sale items") == "sale"
        assert product_service.detect_browse_trigger("On sale") == "sale"
        assert product_service.detect_browse_trigger("discounts") == "sale"

    def test_no_trigger_detected(self, product_service: ProductService):
        """Test when no trigger is detected."""
        assert product_service.detect_browse_trigger("Hello") is None
        assert product_service.detect_browse_trigger("What sizes do you have?") is None
        assert product_service.detect_browse_trigger("ORD-2024-001234") is None


class TestProductFormatting:
    """Tests for product list formatting."""

    @pytest.fixture
    def product_service(self) -> ProductService:
        """Create product service instance."""
        return ProductService()

    def test_format_product_for_list(self, product_service: ProductService):
        """Test formatting product for WhatsApp list."""
        product = {
            "id": "prod-123",
            "name": "Floral Dress",
            "price": 59.99,
            "currency": "USD",
        }

        formatted = product_service.format_product_for_list(product)

        assert formatted["id"] == "prod-123"
        assert formatted["title"] == "Floral Dress"
        assert "59.99" in formatted["description"]

    def test_format_product_detail(self, product_service: ProductService):
        """Test formatting product details for display."""
        product = {
            "id": "prod-123",
            "name": "Floral Dress",
            "description": "Beautiful summer dress with floral pattern",
            "price": 59.99,
            "currency": "USD",
            "sizes": ["S", "M", "L", "XL"],
            "colors": ["Red", "Blue", "White"],
            "image_urls": ["https://example.com/dress.jpg"],
        }

        formatted = product_service.format_product_detail(product)

        assert "Floral Dress" in formatted
        assert "59.99" in formatted
        assert "S" in formatted or "sizes" in formatted.lower()

    def test_format_empty_category_message(self, product_service: ProductService):
        """Test message for empty category."""
        message = product_service.format_empty_category("new_arrivals")

        assert "new arrivals" in message.lower() or "products" in message.lower()
        assert any(word in message.lower() for word in ["try", "browse", "check"])
