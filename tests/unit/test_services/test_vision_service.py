"""Unit tests for vision service."""

from unittest.mock import AsyncMock, patch

import pytest


class TestVisionService:
    """Test VisionService clothing attribute extraction."""

    @pytest.mark.asyncio
    async def test_analyze_clothing_image_returns_attributes(self) -> None:
        """Test that analyze_clothing_image returns expected attributes."""
        from app.services.vision_service import VisionService

        mock_gemini_response = '''{
            "garment_type": "dress",
            "colors": ["blue", "white"],
            "patterns": ["floral"],
            "style_keywords": ["summer", "casual", "midi"]
        }'''

        with patch("app.services.vision_service.analyze_image", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_gemini_response

            service = VisionService()
            result = await service.analyze_clothing_image(b"test_image")

            assert result["garment_type"] == "dress"
            assert "blue" in result["colors"]
            assert "floral" in result["patterns"]
            assert "summer" in result["style_keywords"]

    @pytest.mark.asyncio
    async def test_analyze_non_clothing_returns_is_clothing_false(self) -> None:
        """Test that non-clothing images return is_clothing: false."""
        from app.services.vision_service import VisionService

        mock_gemini_response = '''{
            "is_clothing": false,
            "reason": "This appears to be a landscape photo"
        }'''

        with patch("app.services.vision_service.analyze_image", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_gemini_response

            service = VisionService()
            result = await service.analyze_clothing_image(b"landscape_image")

            assert result.get("is_clothing") is False
            assert "reason" in result

    @pytest.mark.asyncio
    async def test_analyze_handles_json_in_code_block(self) -> None:
        """Test that JSON wrapped in code blocks is parsed correctly."""
        from app.services.vision_service import VisionService

        mock_gemini_response = '''```json
{
    "garment_type": "shirt",
    "colors": ["red"],
    "patterns": ["solid"],
    "style_keywords": ["formal"]
}
```'''

        with patch("app.services.vision_service.analyze_image", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_gemini_response

            service = VisionService()
            result = await service.analyze_clothing_image(b"test_image")

            assert result["garment_type"] == "shirt"

    @pytest.mark.asyncio
    async def test_analyze_handles_api_error(self) -> None:
        """Test that API errors are handled gracefully."""
        from app.core.exceptions import GeminiError
        from app.services.vision_service import VisionService

        with patch("app.services.vision_service.analyze_image", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = Exception("API error")

            service = VisionService()

            with pytest.raises(GeminiError):
                await service.analyze_clothing_image(b"test_image")


class TestClothingAttributeExtraction:
    """Test specific attribute extraction scenarios."""

    @pytest.mark.asyncio
    async def test_extracts_multiple_colors(self) -> None:
        """Test extraction of multiple colors."""
        from app.services.vision_service import VisionService

        mock_response = '''{
            "garment_type": "blouse",
            "colors": ["navy", "white", "gold"],
            "patterns": ["striped"],
            "style_keywords": ["nautical"]
        }'''

        with patch("app.services.vision_service.analyze_image", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            service = VisionService()
            result = await service.analyze_clothing_image(b"test")

            assert len(result["colors"]) == 3
            assert "navy" in result["colors"]

    @pytest.mark.asyncio
    async def test_extracts_patterns(self) -> None:
        """Test extraction of patterns."""
        from app.services.vision_service import VisionService

        mock_response = '''{
            "garment_type": "skirt",
            "colors": ["black"],
            "patterns": ["polka dot", "geometric"],
            "style_keywords": ["retro"]
        }'''

        with patch("app.services.vision_service.analyze_image", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            service = VisionService()
            result = await service.analyze_clothing_image(b"test")

            assert "polka dot" in result["patterns"]
