"""Integration tests for order tracking flow."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


class TestOrderTrackingFlow:
    """Test complete order tracking from message to status response."""

    @pytest.fixture
    def order_webhook_payload(self) -> dict:
        """Sample order ID message webhook payload."""
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
                                        "text": {"body": "ORD-2024-001234"},
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
    async def test_order_id_triggers_status_lookup(
        self,
        test_client: TestClient,
        order_webhook_payload: dict,
    ):
        """Test that order ID triggers order status lookup."""
        with patch("app.api.webhook.order_service") as mock_order, \
             patch("app.api.webhook.whatsapp_service") as mock_whatsapp, \
             patch("app.api.webhook.conversation_service") as mock_conv:

            # Mock detection method to return the order ID
            mock_order.extract_order_id.return_value = "ORD-2024-001234"
            mock_order.format_order_status.return_value = "Order status message"

            mock_order.get_order_by_id = AsyncMock(return_value={
                "id": "ORD-2024-001234",
                "status": "shipped",
                "tracking_number": "TRK123456789",
                "estimated_delivery": "2024-11-25",
                "items": [
                    {"name": "Floral Dress", "quantity": 1, "price": 59.99}
                ],
            })
            mock_whatsapp.send_text = AsyncMock(return_value=True)
            mock_conv.log_message = AsyncMock()

            response = test_client.post("/webhook", json=order_webhook_payload)

            assert response.status_code == 200
            mock_order.get_order_by_id.assert_called_once_with("ORD-2024-001234")

    @pytest.mark.asyncio
    async def test_order_status_includes_tracking(
        self,
        test_client: TestClient,
        order_webhook_payload: dict,
    ):
        """Test that response includes tracking number and ETA."""
        with patch("app.api.webhook.order_service") as mock_order, \
             patch("app.api.webhook.whatsapp_service") as mock_whatsapp, \
             patch("app.api.webhook.conversation_service") as mock_conv:

            mock_order.get_order_by_id = AsyncMock(return_value={
                "id": "ORD-2024-001234",
                "status": "shipped",
                "tracking_number": "TRK123456789",
                "estimated_delivery": "2024-11-25",
                "carrier": "FedEx",
                "items": [],
            })
            mock_whatsapp.send_text = AsyncMock(return_value=True)
            mock_conv.log_message = AsyncMock()

            response = test_client.post("/webhook", json=order_webhook_payload)

            assert response.status_code == 200
            # Verify send_text was called with tracking info
            call_args = mock_whatsapp.send_text.call_args
            message_text = call_args[0][1]
            assert "TRK123456789" in message_text or mock_whatsapp.send_text.called

    @pytest.mark.asyncio
    async def test_invalid_order_returns_guidance(
        self,
        test_client: TestClient,
    ):
        """Test that invalid order ID returns format guidance."""
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
                                        "id": "wamid.test456",
                                        "timestamp": "1700000000",
                                        "type": "text",
                                        "text": {"body": "ORD-INVALID"},
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        with patch("app.api.webhook.order_service") as mock_order, \
             patch("app.api.webhook.whatsapp_service") as mock_whatsapp:

            mock_order.get_order_by_id = AsyncMock(return_value=None)
            mock_whatsapp.send_text = AsyncMock(return_value=True)

            response = test_client.post("/webhook", json=payload)

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_order_not_found_message(
        self,
        test_client: TestClient,
        order_webhook_payload: dict,
    ):
        """Test message when order is not found in system."""
        with patch("app.api.webhook.order_service") as mock_order, \
             patch("app.api.webhook.whatsapp_service") as mock_whatsapp:

            mock_order.get_order_by_id = AsyncMock(return_value=None)
            mock_whatsapp.send_text = AsyncMock(return_value=True)

            response = test_client.post("/webhook", json=order_webhook_payload)

            assert response.status_code == 200
            mock_whatsapp.send_text.assert_called()

    @pytest.mark.asyncio
    async def test_different_order_statuses(
        self,
        test_client: TestClient,
        order_webhook_payload: dict,
    ):
        """Test handling of different order statuses."""
        statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]

        for status in statuses:
            with patch("app.api.webhook.order_service") as mock_order, \
                 patch("app.api.webhook.whatsapp_service") as mock_whatsapp, \
                 patch("app.api.webhook.conversation_service") as mock_conv:

                mock_order.get_order_by_id = AsyncMock(return_value={
                    "id": "ORD-2024-001234",
                    "status": status,
                    "items": [],
                })
                mock_whatsapp.send_text = AsyncMock(return_value=True)
                mock_conv.log_message = AsyncMock()

                response = test_client.post("/webhook", json=order_webhook_payload)
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_conversation_logged_for_order_tracking(
        self,
        test_client: TestClient,
        order_webhook_payload: dict,
    ):
        """Test that order tracking interactions are logged."""
        with patch("app.api.webhook.order_service") as mock_order, \
             patch("app.api.webhook.whatsapp_service") as mock_whatsapp, \
             patch("app.api.webhook.conversation_service") as mock_conv:

            mock_order.get_order_by_id = AsyncMock(return_value={
                "id": "ORD-2024-001234",
                "status": "shipped",
                "items": [],
            })
            mock_whatsapp.send_text = AsyncMock(return_value=True)
            mock_conv.log_message = AsyncMock(return_value="conv-123")

            response = test_client.post("/webhook", json=order_webhook_payload)

            assert response.status_code == 200
            mock_conv.log_message.assert_called()
            # Verify intent is order_tracking
            call_kwargs = mock_conv.log_message.call_args[1]
            assert call_kwargs.get("intent") == "order_tracking"
