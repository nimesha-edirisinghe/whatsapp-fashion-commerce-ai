"""Integration tests for catalog browsing flow."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


class TestCatalogBrowseFlow:
    """Test complete catalog browsing from trigger to product list."""

    @pytest.fixture
    def browse_webhook_payload(self) -> dict:
        """Sample browse trigger webhook payload."""
        return {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "123456789",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "15551234567",
                                    "phone_number_id": "987654321",
                                },
                                "contacts": [
                                    {
                                        "profile": {"name": "Test User"},
                                        "wa_id": "15559876543",
                                    }
                                ],
                                "messages": [
                                    {
                                        "from": "15559876543",
                                        "id": "wamid.test123",
                                        "timestamp": "1699999999",
                                        "type": "text",
                                        "text": {"body": "New Arrivals"},
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

    @pytest.fixture
    def interactive_reply_payload(self) -> dict:
        """Sample interactive list reply payload."""
        return {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "123456789",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "15551234567",
                                    "phone_number_id": "987654321",
                                },
                                "contacts": [
                                    {
                                        "profile": {"name": "Test User"},
                                        "wa_id": "15559876543",
                                    }
                                ],
                                "messages": [
                                    {
                                        "from": "15559876543",
                                        "id": "wamid.test456",
                                        "timestamp": "1700000000",
                                        "type": "interactive",
                                        "interactive": {
                                            "type": "list_reply",
                                            "list_reply": {
                                                "id": "prod-123",
                                                "title": "Floral Dress",
                                            },
                                        },
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

    @pytest.mark.asyncio
    async def test_new_arrivals_returns_product_list(
        self,
        test_client: TestClient,
        browse_webhook_payload: dict,
    ):
        """Test that 'New Arrivals' trigger returns product list."""
        with patch("app.api.webhook.product_service") as mock_product, \
             patch("app.api.webhook.order_service") as mock_order, \
             patch("app.api.webhook.whatsapp_service") as mock_whatsapp, \
             patch("app.api.webhook.conversation_service") as mock_conv:

            # Mock detection methods
            mock_order.extract_order_id.return_value = None  # Not an order ID
            mock_product.detect_browse_trigger.return_value = "new_arrivals"

            mock_product.get_new_arrivals = AsyncMock(return_value=[
                {"id": "prod-1", "name": "Floral Dress", "price": 59.99},
                {"id": "prod-2", "name": "Cotton Shirt", "price": 39.99},
                {"id": "prod-3", "name": "Denim Jeans", "price": 49.99},
            ])
            mock_whatsapp.send_message = AsyncMock(return_value=True)
            mock_conv.log_message = AsyncMock()

            response = test_client.post("/webhook", json=browse_webhook_payload)

            assert response.status_code == 200
            mock_product.get_new_arrivals.assert_called_once()

    @pytest.mark.asyncio
    async def test_trending_trigger_works(
        self,
        test_client: TestClient,
    ):
        """Test that 'Trending' trigger returns products."""
        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "123456789",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "15551234567",
                                    "phone_number_id": "987654321",
                                },
                                "contacts": [
                                    {
                                        "profile": {"name": "Test User"},
                                        "wa_id": "15559876543",
                                    }
                                ],
                                "messages": [
                                    {
                                        "from": "15559876543",
                                        "id": "wamid.test789",
                                        "timestamp": "1700000001",
                                        "type": "text",
                                        "text": {"body": "Trending"},
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        with patch("app.api.webhook.product_service") as mock_product, \
             patch("app.api.webhook.whatsapp_service") as mock_whatsapp, \
             patch("app.api.webhook.conversation_service") as mock_conv:

            mock_product.get_trending = AsyncMock(return_value=[
                {"id": "prod-1", "name": "Summer Dress", "price": 69.99},
            ])
            mock_whatsapp.send_message = AsyncMock(return_value=True)
            mock_conv.log_message = AsyncMock()

            response = test_client.post("/webhook", json=payload)
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_sale_trigger_works(
        self,
        test_client: TestClient,
    ):
        """Test that 'Sale' trigger returns discounted products."""
        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "123456789",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "15551234567",
                                    "phone_number_id": "987654321",
                                },
                                "contacts": [
                                    {
                                        "profile": {"name": "Test User"},
                                        "wa_id": "15559876543",
                                    }
                                ],
                                "messages": [
                                    {
                                        "from": "15559876543",
                                        "id": "wamid.test_sale",
                                        "timestamp": "1700000002",
                                        "type": "text",
                                        "text": {"body": "Sale items"},
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        with patch("app.api.webhook.product_service") as mock_product, \
             patch("app.api.webhook.whatsapp_service") as mock_whatsapp, \
             patch("app.api.webhook.conversation_service") as mock_conv:

            mock_product.get_sale_items = AsyncMock(return_value=[])
            mock_whatsapp.send_message = AsyncMock(return_value=True)
            mock_whatsapp.send_text = AsyncMock(return_value=True)
            mock_conv.log_message = AsyncMock()

            response = test_client.post("/webhook", json=payload)
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_interactive_reply_shows_product_details(
        self,
        test_client: TestClient,
        interactive_reply_payload: dict,
    ):
        """Test that tapping list item shows product details."""
        with patch("app.api.webhook.product_service") as mock_product, \
             patch("app.api.webhook.whatsapp_service") as mock_whatsapp, \
             patch("app.api.webhook.conversation_service") as mock_conv:

            mock_product.get_by_id = AsyncMock(return_value={
                "id": "prod-123",
                "name": "Floral Dress",
                "description": "Beautiful summer dress",
                "price": 59.99,
                "sizes": ["S", "M", "L"],
                "colors": ["Red", "Blue"],
                "image_urls": ["https://example.com/dress.jpg"],
            })
            mock_whatsapp.send_text = AsyncMock(return_value=True)
            mock_conv.log_message = AsyncMock()

            response = test_client.post("/webhook", json=interactive_reply_payload)

            assert response.status_code == 200
            mock_product.get_by_id.assert_called_once_with("prod-123")

    @pytest.mark.asyncio
    async def test_empty_category_shows_alternatives(
        self,
        test_client: TestClient,
        browse_webhook_payload: dict,
    ):
        """Test that empty category suggests alternatives."""
        with patch("app.api.webhook.product_service") as mock_product, \
             patch("app.api.webhook.whatsapp_service") as mock_whatsapp:

            mock_product.get_new_arrivals = AsyncMock(return_value=[])
            mock_whatsapp.send_text = AsyncMock(return_value=True)

            response = test_client.post("/webhook", json=browse_webhook_payload)

            assert response.status_code == 200
            mock_whatsapp.send_text.assert_called()

    @pytest.mark.asyncio
    async def test_conversation_logged_for_browse(
        self,
        test_client: TestClient,
        browse_webhook_payload: dict,
    ):
        """Test that browse interactions are logged."""
        with patch("app.api.webhook.product_service") as mock_product, \
             patch("app.api.webhook.order_service") as mock_order, \
             patch("app.api.webhook.whatsapp_service") as mock_whatsapp, \
             patch("app.api.webhook.conversation_service") as mock_conv:

            # Mock detection methods
            mock_order.extract_order_id.return_value = None
            mock_product.detect_browse_trigger.return_value = "new_arrivals"

            mock_product.get_new_arrivals = AsyncMock(return_value=[
                {"id": "prod-1", "name": "Dress", "price": 59.99},
            ])
            mock_whatsapp.send_message = AsyncMock(return_value=True)
            mock_conv.log_message = AsyncMock(return_value="conv-123")

            response = test_client.post("/webhook", json=browse_webhook_payload)

            assert response.status_code == 200
            mock_conv.log_message.assert_called()
            call_kwargs = mock_conv.log_message.call_args[1]
            assert call_kwargs.get("intent") == "catalog_browse"

    @pytest.mark.asyncio
    async def test_case_insensitive_triggers(
        self,
        test_client: TestClient,
    ):
        """Test that triggers work regardless of case."""
        for trigger in ["NEW ARRIVALS", "new arrivals", "New arrivals"]:
            payload = {
                "object": "whatsapp_business_account",
                "entry": [
                    {
                        "id": "123456789",
                        "changes": [
                            {
                                "value": {
                                    "messaging_product": "whatsapp",
                                    "metadata": {
                                        "display_phone_number": "15551234567",
                                        "phone_number_id": "987654321",
                                    },
                                    "contacts": [
                                        {
                                            "profile": {"name": "Test User"},
                                            "wa_id": "15559876543",
                                        }
                                    ],
                                    "messages": [
                                        {
                                            "from": "15559876543",
                                            "id": "wamid.test_case",
                                            "timestamp": "1700000003",
                                            "type": "text",
                                            "text": {"body": trigger},
                                        }
                                    ],
                                },
                                "field": "messages",
                            }
                        ],
                    }
                ],
            }

            with patch("app.api.webhook.product_service") as mock_product, \
                 patch("app.api.webhook.whatsapp_service") as mock_whatsapp, \
                 patch("app.api.webhook.conversation_service") as mock_conv:

                mock_product.get_new_arrivals = AsyncMock(return_value=[])
                mock_whatsapp.send_text = AsyncMock(return_value=True)
                mock_conv.log_message = AsyncMock()

                response = test_client.post("/webhook", json=payload)
                assert response.status_code == 200
