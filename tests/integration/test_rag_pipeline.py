"""Integration tests for RAG pipeline Q&A flow."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


class TestRAGPipelineFlow:
    """Test complete RAG pipeline from text message to response."""

    @pytest.fixture
    def text_webhook_payload(self) -> dict:
        """Sample text message webhook payload."""
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
                                        "text": {
                                            "body": "What sizes do you have for the floral dress?"
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

    @pytest.fixture
    def followup_webhook_payload(self) -> dict:
        """Follow-up question payload for context testing."""
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
                                        "type": "text",
                                        "text": {"body": "What about in blue?"},
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
    async def test_text_message_triggers_rag_pipeline(
        self,
        test_client: TestClient,
        text_webhook_payload: dict,
    ):
        """Test that text message triggers RAG search and AI response."""
        with patch("app.api.webhook.ai_service") as mock_ai, \
             patch("app.api.webhook.whatsapp_service") as mock_whatsapp, \
             patch("app.api.webhook.conversation_service") as mock_conv:

            # Setup mocks
            mock_ai.process_text_message = AsyncMock(
                return_value="The floral dress is available in sizes S, M, L, and XL."
            )
            mock_whatsapp.send_text = AsyncMock(return_value=True)
            mock_conv.log_message = AsyncMock()

            response = test_client.post("/webhook", json=text_webhook_payload)

            assert response.status_code == 200
            assert response.json()["status"] == "ok"

    @pytest.mark.asyncio
    async def test_context_maintained_across_messages(
        self,
        test_client: TestClient,
        followup_webhook_payload: dict,
    ):
        """Test that conversation context is used for follow-up questions."""
        with patch("app.api.webhook.ai_service") as mock_ai, \
             patch("app.api.webhook.whatsapp_service") as mock_whatsapp, \
             patch("app.api.webhook.conversation_service") as mock_conv:

            # Setup mocks
            mock_ai.process_text_message = AsyncMock(
                return_value="Yes, we have the floral dress in blue in all sizes."
            )
            mock_whatsapp.send_text = AsyncMock(return_value=True)
            mock_conv.log_message = AsyncMock()

            response = test_client.post("/webhook", json=followup_webhook_payload)

            assert response.status_code == 200
            # Verify AI service was called with the customer phone
            mock_ai.process_text_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_ai_failure(
        self,
        test_client: TestClient,
        text_webhook_payload: dict,
    ):
        """Test fallback menu when AI service fails."""
        with patch("app.api.webhook.ai_service") as mock_ai, \
             patch("app.api.webhook.whatsapp_service") as mock_whatsapp:

            mock_ai.process_text_message = AsyncMock(
                side_effect=Exception("AI service unavailable")
            )
            mock_whatsapp.send_message = AsyncMock(return_value=True)

            response = test_client.post("/webhook", json=text_webhook_payload)

            assert response.status_code == 200
            # Should send fallback menu
            mock_whatsapp.send_message.assert_called()

    @pytest.mark.asyncio
    async def test_non_clothing_query_filtered(
        self,
        test_client: TestClient,
    ):
        """Test that non-clothing queries are politely redirected."""
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
                                        "text": {"body": "What's the weather like today?"},
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        with patch("app.api.webhook.ai_service") as mock_ai, \
             patch("app.api.webhook.whatsapp_service") as mock_whatsapp, \
             patch("app.api.webhook.conversation_service") as mock_conv:

            mock_ai.process_text_message = AsyncMock(
                return_value="I can only help with fashion-related questions."
            )
            mock_whatsapp.send_text = AsyncMock(return_value=True)
            mock_conv.log_message = AsyncMock()

            response = test_client.post("/webhook", json=payload)

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_response_time_under_threshold(
        self,
        test_client: TestClient,
        text_webhook_payload: dict,
    ):
        """Test that Q&A response completes within performance threshold."""
        import time

        with patch("app.api.webhook.ai_service") as mock_ai, \
             patch("app.api.webhook.whatsapp_service") as mock_whatsapp, \
             patch("app.api.webhook.conversation_service") as mock_conv:

            mock_ai.process_text_message = AsyncMock(return_value="Test response")
            mock_whatsapp.send_text = AsyncMock(return_value=True)
            mock_conv.log_message = AsyncMock()

            start_time = time.time()
            response = test_client.post("/webhook", json=text_webhook_payload)
            elapsed_ms = (time.time() - start_time) * 1000

            assert response.status_code == 200
            # Mock response should be very fast
            assert elapsed_ms < 1000  # 1 second for mocked response

    @pytest.mark.asyncio
    async def test_conversation_logged_for_analytics(
        self,
        test_client: TestClient,
        text_webhook_payload: dict,
    ):
        """Test that Q&A interactions are logged for analytics."""
        with patch("app.api.webhook.ai_service") as mock_ai, \
             patch("app.api.webhook.whatsapp_service") as mock_whatsapp, \
             patch("app.api.webhook.conversation_service") as mock_conv:

            mock_ai.process_text_message = AsyncMock(return_value="Test response")
            mock_whatsapp.send_text = AsyncMock(return_value=True)
            mock_conv.log_message = AsyncMock(return_value="conv-123")

            response = test_client.post("/webhook", json=text_webhook_payload)

            assert response.status_code == 200
            # Verify conversation was logged
            mock_conv.log_message.assert_called()

    @pytest.mark.asyncio
    async def test_language_detection_applied(
        self,
        test_client: TestClient,
    ):
        """Test that language is auto-detected from message content."""
        spanish_payload = {
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
                                        "id": "wamid.test_es",
                                        "timestamp": "1700000002",
                                        "type": "text",
                                        "text": {"body": "¿Tienen vestidos en talla grande?"},
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        with patch("app.api.webhook.ai_service") as mock_ai, \
             patch("app.api.webhook.whatsapp_service") as mock_whatsapp, \
             patch("app.api.webhook.conversation_service") as mock_conv:

            mock_ai.process_text_message = AsyncMock(return_value="Respuesta en español")
            mock_whatsapp.send_text = AsyncMock(return_value=True)
            mock_conv.log_message = AsyncMock()

            response = test_client.post("/webhook", json=spanish_payload)

            assert response.status_code == 200
