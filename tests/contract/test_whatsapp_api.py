"""Contract tests for WhatsApp Cloud API."""

from typing import Any

import pytest
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
