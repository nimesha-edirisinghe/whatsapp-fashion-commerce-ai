"""Unit tests for escalation service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.escalation_service import EscalationService


class TestEscalationService:
    """Tests for escalation service methods."""

    @pytest.fixture
    def escalation_service(self) -> EscalationService:
        """Create escalation service instance."""
        return EscalationService()

    @pytest.mark.asyncio
    async def test_escalate_to_human_success(
        self, escalation_service: EscalationService
    ):
        """Test successful escalation to human."""
        with patch("app.services.escalation_service.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client:

            mock_settings.n8n_webhook_url = "https://n8n.example.com/webhook"
            mock_settings.n8n_webhook_secret = "secret"

            mock_response = MagicMock()
            mock_response.status_code = 200

            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            result = await escalation_service.escalate_to_human(
                customer_phone="15559876543",
                reason="Low confidence",
                confidence_score=0.5,
                last_message="I need help",
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_escalate_to_human_no_webhook_url(
        self, escalation_service: EscalationService
    ):
        """Test escalation skipped when no webhook URL."""
        with patch("app.services.escalation_service.settings") as mock_settings:
            mock_settings.n8n_webhook_url = None

            result = await escalation_service.escalate_to_human(
                customer_phone="15559876543",
                reason="Test",
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_escalate_to_human_webhook_failure(
        self, escalation_service: EscalationService
    ):
        """Test escalation handles webhook failure."""
        with patch("app.services.escalation_service.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client:

            mock_settings.n8n_webhook_url = "https://n8n.example.com/webhook"
            mock_settings.n8n_webhook_secret = "secret"

            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal error"

            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            result = await escalation_service.escalate_to_human(
                customer_phone="15559876543",
                reason="Test",
            )

            assert result is False


class TestShouldEscalate:
    """Tests for escalation decision logic."""

    @pytest.fixture
    def escalation_service(self) -> EscalationService:
        """Create escalation service instance."""
        return EscalationService()

    def test_should_escalate_explicit_request(
        self, escalation_service: EscalationService
    ):
        """Test escalation for explicit request."""
        should, reason = escalation_service.should_escalate(
            confidence_score=0.9,
            explicit_request=True,
        )

        assert should is True
        assert "requested" in reason.lower()

    def test_should_escalate_low_confidence(
        self, escalation_service: EscalationService
    ):
        """Test escalation for low confidence score."""
        should, reason = escalation_service.should_escalate(
            confidence_score=0.5,
        )

        assert should is True
        assert "confidence" in reason.lower()

    def test_should_not_escalate_high_confidence(
        self, escalation_service: EscalationService
    ):
        """Test no escalation for high confidence."""
        should, reason = escalation_service.should_escalate(
            confidence_score=0.9,
        )

        assert should is False
        assert reason == ""

    def test_should_escalate_at_threshold(
        self, escalation_service: EscalationService
    ):
        """Test escalation at exactly threshold."""
        # At threshold should not escalate
        should, _ = escalation_service.should_escalate(
            confidence_score=0.7,
        )
        assert should is False

        # Just below threshold should escalate
        should, _ = escalation_service.should_escalate(
            confidence_score=0.69,
        )
        assert should is True

    def test_should_escalate_no_confidence(
        self, escalation_service: EscalationService
    ):
        """Test escalation when confidence is None."""
        should, _ = escalation_service.should_escalate(
            confidence_score=None,
        )

        assert should is False


class TestDetectEscalationRequest:
    """Tests for detecting escalation requests in messages."""

    @pytest.fixture
    def escalation_service(self) -> EscalationService:
        """Create escalation service instance."""
        return EscalationService()

    def test_detect_talk_to_human(
        self, escalation_service: EscalationService
    ):
        """Test detection of 'talk to human' phrase."""
        assert escalation_service.detect_escalation_request("I want to talk to human") is True
        assert escalation_service.detect_escalation_request("Talk to human please") is True

    def test_detect_human_agent(
        self, escalation_service: EscalationService
    ):
        """Test detection of 'human agent' phrase."""
        assert escalation_service.detect_escalation_request("I need a human agent") is True

    def test_detect_real_person(
        self, escalation_service: EscalationService
    ):
        """Test detection of 'real person' phrase."""
        assert escalation_service.detect_escalation_request("Can I speak to a real person?") is True

    def test_detect_customer_service(
        self, escalation_service: EscalationService
    ):
        """Test detection of 'customer service' phrase."""
        assert escalation_service.detect_escalation_request("Connect me to customer service") is True

    def test_no_escalation_normal_message(
        self, escalation_service: EscalationService
    ):
        """Test no detection for normal messages."""
        assert escalation_service.detect_escalation_request("What sizes do you have?") is False
        assert escalation_service.detect_escalation_request("Hello") is False
        assert escalation_service.detect_escalation_request("Show me dresses") is False

    def test_case_insensitive_detection(
        self, escalation_service: EscalationService
    ):
        """Test case-insensitive detection."""
        assert escalation_service.detect_escalation_request("TALK TO HUMAN") is True
        assert escalation_service.detect_escalation_request("Talk To Human") is True


class TestEscalationMessages:
    """Tests for escalation message formatting."""

    @pytest.fixture
    def escalation_service(self) -> EscalationService:
        """Create escalation service instance."""
        return EscalationService()

    def test_get_escalation_message(
        self, escalation_service: EscalationService
    ):
        """Test escalation message content."""
        message = escalation_service.get_escalation_message()

        assert "human" in message.lower() or "agent" in message.lower()
        assert "business hours" in message.lower()

    def test_confidence_threshold_value(
        self, escalation_service: EscalationService
    ):
        """Test confidence threshold is correctly set."""
        assert escalation_service.CONFIDENCE_THRESHOLD == 0.7
