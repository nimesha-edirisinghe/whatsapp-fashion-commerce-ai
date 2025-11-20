"""Contract tests for WhatsApp Cloud API."""

from typing import Any
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


class TestWebhookVerification:
    """Test WhatsApp webhook verification endpoint."""

    def test_verify_webhook_success(self, test_client: TestClient) -> None:
        """Test successful webhook verification."""
        response = test_client.get(
            "/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "test_verify_token",
                "hub.challenge": "challenge123",
            },
        )
        assert response.status_code == 200
        assert response.text == "challenge123"

    def test_verify_webhook_invalid_token(self, test_client: TestClient) -> None:
        """Test webhook verification with invalid token."""
        response = test_client.get(
            "/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong_token",
                "hub.challenge": "challenge123",
            },
        )
        assert response.status_code == 403

    def test_verify_webhook_invalid_mode(self, test_client: TestClient) -> None:
        """Test webhook verification with invalid mode."""
        response = test_client.get(
            "/webhook",
            params={
                "hub.mode": "unsubscribe",
                "hub.verify_token": "test_verify_token",
                "hub.challenge": "challenge123",
            },
        )
        assert response.status_code == 403


class TestWebhookHandler:
    """Test WhatsApp webhook handler endpoint."""

    def test_handle_text_message(
        self,
        test_client: TestClient,
        sample_webhook_text_payload: dict[str, Any],
    ) -> None:
        """Test handling text message webhook."""
        with patch("app.api.webhook.ai_service") as mock_ai, \
             patch("app.api.webhook.whatsapp_service") as mock_whatsapp, \
             patch("app.api.webhook.conversation_service") as mock_conv:

            mock_ai.process_text_message = AsyncMock(return_value="Test response")
            mock_whatsapp.send_text = AsyncMock(return_value=True)
            mock_conv.log_message = AsyncMock()

            response = test_client.post(
                "/webhook",
                json=sample_webhook_text_payload,
            )
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}

    def test_handle_image_message(
        self,
        test_client: TestClient,
        sample_webhook_image_payload: dict[str, Any],
    ) -> None:
        """Test handling image message webhook."""
        with patch("app.api.webhook.whatsapp_service") as mock_whatsapp, \
             patch("app.api.webhook.vision_service") as mock_vision, \
             patch("app.api.webhook.product_service") as mock_product, \
             patch("app.api.webhook.conversation_service") as mock_conv:

            mock_whatsapp.download_media = AsyncMock(return_value=b"fake_image")
            mock_whatsapp.send_text = AsyncMock(return_value=True)
            mock_vision.analyze_clothing_image = AsyncMock(return_value={
                "category": "dress", "color": "blue"
            })
            mock_vision.is_valid_clothing_result.return_value = True
            mock_product.search_by_attributes = AsyncMock(return_value=[])
            mock_conv.log_visual_search = AsyncMock()

            response = test_client.post(
                "/webhook",
                json=sample_webhook_image_payload,
            )
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}

    def test_handle_invalid_payload(self, test_client: TestClient) -> None:
        """Test handling invalid webhook payload."""
        response = test_client.post(
            "/webhook",
            json={"invalid": "payload"},
        )
        assert response.status_code == 422  # Validation error


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check_returns_status(self, test_client: TestClient) -> None:
        """Test health endpoint returns expected structure."""
        response = test_client.get("/health")
        # May fail on actual checks but should return valid structure
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "timestamp" in data
        assert "checks" in data
        assert "database" in data["checks"]
        assert "redis" in data["checks"]
        assert "openai" in data["checks"]
        assert "gemini" in data["checks"]


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root_returns_ok(self, test_client: TestClient) -> None:
        """Test root endpoint returns service info."""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "service" in data
