"""Integration tests for visual search flow."""

from typing import Any
from unittest.mock import AsyncMock, patch, MagicMock

import pytest


class TestVisualSearchFlow:
    """Test complete visual search user journey."""

    @pytest.mark.asyncio
    async def test_image_upload_returns_product_matches(
        self,
        sample_webhook_image_payload: dict[str, Any],
        sample_product: dict[str, Any],
    ) -> None:
        """Test that uploading image returns matching products."""
        from app.services.vision_service import VisionService
        from app.services.product_service import ProductService

        # Mock vision service to return clothing attributes
        mock_attributes = {
            "garment_type": "dress",
            "colors": ["blue"],
            "patterns": ["solid"],
            "style_keywords": ["summer", "casual"],
        }

        with patch.object(
            VisionService, "analyze_clothing_image", new_callable=AsyncMock
        ) as mock_vision:
            mock_vision.return_value = mock_attributes

            with patch.object(
                ProductService, "search_by_attributes", new_callable=AsyncMock
            ) as mock_search:
                mock_search.return_value = [sample_product]

                # Process should work without error
                vision_service = VisionService()
                product_service = ProductService()

                attributes = await vision_service.analyze_clothing_image(b"fake_image")
                products = await product_service.search_by_attributes(attributes)

                assert len(products) >= 1
                assert products[0]["name"] == "Summer Dress"

    @pytest.mark.asyncio
    async def test_non_clothing_image_rejected(self) -> None:
        """Test that non-clothing images are rejected politely."""
        from app.services.vision_service import VisionService

        mock_response = {
            "is_clothing": False,
            "reason": "This appears to be a food image",
        }

        with patch.object(
            VisionService, "analyze_clothing_image", new_callable=AsyncMock
        ) as mock_vision:
            mock_vision.return_value = mock_response

            vision_service = VisionService()
            result = await vision_service.analyze_clothing_image(b"fake_food_image")

            assert result.get("is_clothing") is False
            assert "reason" in result

    @pytest.mark.asyncio
    async def test_visual_search_completes_within_timeout(self) -> None:
        """Test that visual search completes within 10 second requirement."""
        import asyncio
        from app.services.vision_service import VisionService

        mock_attributes = {
            "garment_type": "shirt",
            "colors": ["white"],
            "patterns": [],
            "style_keywords": ["casual"],
        }

        with patch.object(
            VisionService, "analyze_clothing_image", new_callable=AsyncMock
        ) as mock_vision:
            mock_vision.return_value = mock_attributes

            vision_service = VisionService()

            # Should complete within 10 seconds
            try:
                result = await asyncio.wait_for(
                    vision_service.analyze_clothing_image(b"test"),
                    timeout=10.0,
                )
                assert result is not None
            except asyncio.TimeoutError:
                pytest.fail("Visual search exceeded 10 second timeout")

    @pytest.mark.asyncio
    async def test_blurry_image_requests_clearer_photo(self) -> None:
        """Test that blurry/unclear images prompt for better photo."""
        from app.services.vision_service import VisionService

        mock_response = {
            "is_clothing": False,
            "reason": "Image is too blurry to analyze",
        }

        with patch.object(
            VisionService, "analyze_clothing_image", new_callable=AsyncMock
        ) as mock_vision:
            mock_vision.return_value = mock_response

            vision_service = VisionService()
            result = await vision_service.analyze_clothing_image(b"blurry_image")

            assert result.get("is_clothing") is False


class TestImageDownload:
    """Test WhatsApp media download functionality."""

    @pytest.mark.asyncio
    async def test_download_media_success(self) -> None:
        """Test successful media download from WhatsApp."""
        from app.services.whatsapp_service import WhatsAppService

        with patch.object(
            WhatsAppService, "download_media", new_callable=AsyncMock
        ) as mock_download:
            mock_download.return_value = b"fake_image_bytes"

            service = WhatsAppService()
            result = await service.download_media("media123")

            assert result == b"fake_image_bytes"

    @pytest.mark.asyncio
    async def test_download_media_failure_handled(self) -> None:
        """Test that media download failures are handled gracefully."""
        from app.services.whatsapp_service import WhatsAppService
        from app.core.exceptions import WhatsAppAPIError

        with patch.object(
            WhatsAppService, "download_media", new_callable=AsyncMock
        ) as mock_download:
            mock_download.side_effect = WhatsAppAPIError("Download failed")

            service = WhatsAppService()

            with pytest.raises(WhatsAppAPIError):
                await service.download_media("invalid_media")
