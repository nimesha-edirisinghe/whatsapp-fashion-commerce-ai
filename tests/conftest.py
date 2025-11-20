"""Pytest configuration and fixtures."""

import os
from datetime import datetime
from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Set test environment before importing app
os.environ["APP_ENV"] = "development"
os.environ["DEBUG"] = "true"
os.environ["WHATSAPP_ACCESS_TOKEN"] = "test_token"
os.environ["WHATSAPP_PHONE_NUMBER_ID"] = "123456789"
os.environ["WHATSAPP_VERIFY_TOKEN"] = "test_verify_token"
os.environ["WHATSAPP_APP_SECRET"] = "test_secret"
os.environ["OPENAI_API_KEY"] = "test_openai_key"
os.environ["GOOGLE_AI_API_KEY"] = "test_google_key"
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_ANON_KEY"] = "test_anon_key"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test_service_key"
os.environ["UPSTASH_REDIS_URL"] = "redis://localhost:6379"
os.environ["ADMIN_API_KEY"] = "test_admin_key"


@pytest.fixture
def test_client() -> TestClient:
    """Create test client for FastAPI app."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def sample_product() -> dict[str, Any]:
    """Sample product data for testing."""
    return {
        "id": "test-product-1",
        "name": "Summer Dress",
        "description": "A beautiful summer dress",
        "price": 29.99,
        "currency": "USD",
        "supplier_url": "https://example.com/dress",
        "image_urls": ["https://example.com/image1.jpg"],
        "sizes": ["S", "M", "L"],
        "colors": ["Blue", "White"],
        "inventory_count": 10,
        "category": "dress",
        "tags": ["summer", "casual"],
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.fixture
def sample_order() -> dict[str, Any]:
    """Sample order data for testing."""
    return {
        "id": "test-order-uuid",
        "order_id": "ORD-12345",
        "customer_phone": "1234567890",
        "status": "Processing",
        "tracking_number": None,
        "carrier": None,
        "estimated_delivery": "2025-12-01",
        "items": [
            {
                "product_id": "test-product-1",
                "name": "Summer Dress",
                "size": "M",
                "color": "Blue",
                "quantity": 1,
                "unit_price": 29.99,
            }
        ],
        "total_amount": 29.99,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.fixture
def sample_webhook_text_payload() -> dict[str, Any]:
    """Sample WhatsApp text message webhook payload."""
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
                                "phone_number_id": "123456789",
                            },
                            "messages": [
                                {
                                    "id": "wamid.test123",
                                    "from": "1234567890",
                                    "timestamp": "1234567890",
                                    "type": "text",
                                    "text": {"body": "Do you have summer dresses?"},
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
def sample_webhook_image_payload() -> dict[str, Any]:
    """Sample WhatsApp image message webhook payload."""
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
                                "phone_number_id": "123456789",
                            },
                            "messages": [
                                {
                                    "id": "wamid.test456",
                                    "from": "1234567890",
                                    "timestamp": "1234567890",
                                    "type": "image",
                                    "image": {
                                        "id": "media123",
                                        "mime_type": "image/jpeg",
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
def mock_supabase() -> MagicMock:
    """Mock Supabase client."""
    mock = MagicMock()
    mock.table.return_value.select.return_value.execute.return_value.data = []
    return mock


@pytest.fixture
def mock_redis() -> AsyncMock:
    """Mock Redis client."""
    mock = AsyncMock()
    mock.ping.return_value = True
    mock.lrange.return_value = []
    mock.hgetall.return_value = {}
    return mock


@pytest.fixture
def mock_openai() -> AsyncMock:
    """Mock OpenAI client."""
    mock = AsyncMock()
    mock.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="Test response"))
    ]
    mock.embeddings.create.return_value.data = [
        MagicMock(embedding=[0.1] * 1536)
    ]
    return mock
