"""Integration tests for admin catalog sync."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


class TestCatalogSyncFlow:
    """Test complete catalog sync from n8n webhook."""

    @pytest.fixture
    def sync_payload(self) -> dict:
        """Sample catalog sync payload."""
        return {
            "products": [
                {
                    "id": "prod-001",
                    "name": "Summer Dress",
                    "description": "Light cotton summer dress",
                    "price": 59.99,
                    "currency": "USD",
                    "category": "dresses",
                    "sizes": ["S", "M", "L"],
                    "colors": ["Blue", "White"],
                    "image_urls": ["https://example.com/dress.jpg"],
                    "inventory_count": 50,
                    "is_active": True,
                },
                {
                    "id": "prod-002",
                    "name": "Cotton Shirt",
                    "description": "Classic cotton button-up",
                    "price": 39.99,
                    "currency": "USD",
                    "category": "shirts",
                    "sizes": ["S", "M", "L", "XL"],
                    "colors": ["White", "Blue", "Pink"],
                    "image_urls": ["https://example.com/shirt.jpg"],
                    "inventory_count": 100,
                    "is_active": True,
                },
            ],
            "source": "n8n",
            "sync_mode": "upsert",
        }

    @pytest.mark.asyncio
    async def test_sync_catalog_success(
        self,
        test_client: TestClient,
        sync_payload: dict,
    ):
        """Test successful catalog sync."""
        with patch("app.api.admin.product_service") as mock_product, \
             patch("app.api.admin.settings") as mock_settings:

            mock_settings.admin_api_key = "test-api-key"
            mock_product.upsert_product = AsyncMock(return_value={"created": True, "id": "prod-001"})

            response = test_client.post(
                "/admin/sync-catalog",
                json=sync_payload,
                headers={"X-API-Key": "test-api-key"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["products_processed"] == 2

    @pytest.mark.asyncio
    async def test_sync_catalog_unauthorized(
        self,
        test_client: TestClient,
        sync_payload: dict,
    ):
        """Test sync with invalid API key."""
        with patch("app.api.admin.settings") as mock_settings:
            mock_settings.admin_api_key = "correct-key"

            response = test_client.post(
                "/admin/sync-catalog",
                json=sync_payload,
                headers={"X-API-Key": "wrong-key"},
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_sync_catalog_partial_failure(
        self,
        test_client: TestClient,
        sync_payload: dict,
    ):
        """Test sync with some products failing."""
        with patch("app.api.admin.product_service") as mock_product, \
             patch("app.api.admin.settings") as mock_settings:

            mock_settings.admin_api_key = "test-api-key"
            # First succeeds, second fails
            mock_product.upsert_product = AsyncMock(
                side_effect=[
                    {"created": True, "id": "prod-001"},
                    Exception("Database error"),
                ]
            )

            response = test_client.post(
                "/admin/sync-catalog",
                json=sync_payload,
                headers={"X-API-Key": "test-api-key"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert data["products_created"] == 1
            assert data["products_failed"] == 1

    @pytest.mark.asyncio
    async def test_sync_catalog_creates_embeddings(
        self,
        test_client: TestClient,
        sync_payload: dict,
    ):
        """Test that sync creates embeddings for products."""
        with patch("app.api.admin.product_service") as mock_product, \
             patch("app.api.admin.settings") as mock_settings:

            mock_settings.admin_api_key = "test-api-key"
            mock_product.upsert_product = AsyncMock(return_value={"created": True, "id": "prod-001"})

            response = test_client.post(
                "/admin/sync-catalog",
                json=sync_payload,
                headers={"X-API-Key": "test-api-key"},
            )

            assert response.status_code == 200
            # upsert_product should be called for each product
            assert mock_product.upsert_product.call_count == 2

    @pytest.mark.asyncio
    async def test_get_catalog_stats(
        self,
        test_client: TestClient,
    ):
        """Test getting catalog statistics."""
        with patch("app.api.admin.product_service") as mock_product, \
             patch("app.api.admin.settings") as mock_settings:

            mock_settings.admin_api_key = "test-api-key"
            mock_product.get_catalog_stats = AsyncMock(return_value={
                "total_products": 100,
                "active_products": 95,
                "sale_products": 10,
            })

            response = test_client.get(
                "/admin/catalog/stats",
                headers={"X-API-Key": "test-api-key"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total_products"] == 100

    @pytest.mark.asyncio
    async def test_sync_updates_existing_products(
        self,
        test_client: TestClient,
    ):
        """Test that sync updates existing products."""
        payload = {
            "products": [
                {
                    "id": "existing-prod",
                    "name": "Updated Dress",
                    "price": 69.99,
                    "sizes": ["S", "M"],
                    "colors": ["Red"],
                    "image_urls": [],
                },
            ],
            "source": "n8n",
            "sync_mode": "upsert",
        }

        with patch("app.api.admin.product_service") as mock_product, \
             patch("app.api.admin.settings") as mock_settings:

            mock_settings.admin_api_key = "test-api-key"
            mock_product.upsert_product = AsyncMock(
                return_value={"created": False, "id": "existing-prod"}
            )

            response = test_client.post(
                "/admin/sync-catalog",
                json=payload,
                headers={"X-API-Key": "test-api-key"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["products_updated"] == 1
            assert data["products_created"] == 0
