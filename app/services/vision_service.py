"""Vision service for clothing image analysis."""

import json
from typing import Any

from app.core.gemini_client import analyze_image
from app.core.logging import logger
from app.core.exceptions import GeminiError
from app.utils.retry import async_retry


class VisionService:
    """Service for analyzing clothing images using Gemini Vision."""

    @async_retry(attempts=1, timeout=3.0)
    async def analyze_clothing_image(self, image_bytes: bytes) -> dict[str, Any]:
        """
        Analyze clothing image to extract attributes.

        Args:
            image_bytes: Raw image data

        Returns:
            Dict with garment_type, colors, patterns, style_keywords
            Or dict with is_clothing=False and reason if not clothing
        """
        prompt = """Analyze this image and determine if it shows clothing/fashion items.

If this IS a clothing item, return a JSON object with:
{
    "garment_type": "type of clothing (dress, shirt, pants, etc.)",
    "colors": ["list", "of", "colors"],
    "patterns": ["list", "of", "patterns like floral, striped, solid"],
    "style_keywords": ["descriptive", "style", "words"]
}

If this is NOT a clothing item (food, landscape, person without focus on clothes, blurry, etc.), return:
{
    "is_clothing": false,
    "reason": "brief explanation why this cannot be analyzed as clothing"
}

Return ONLY valid JSON, no other text."""

        try:
            response = await analyze_image(image_bytes, prompt)
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            raise GeminiError(f"Failed to analyze image: {e}")

    def _parse_response(self, response: str) -> dict[str, Any]:
        """Parse and clean JSON response from Gemini."""
        response_text = response.strip()

        # Handle markdown code blocks
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            # Remove first and last lines (``` markers)
            json_lines = []
            in_json = False
            for line in lines:
                if line.startswith("```") and not in_json:
                    in_json = True
                    continue
                elif line.startswith("```") and in_json:
                    break
                elif in_json:
                    json_lines.append(line)
            response_text = "\n".join(json_lines)

        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse vision response: {e}")
            logger.debug(f"Raw response: {response_text}")
            return {
                "is_clothing": False,
                "reason": "Failed to analyze image properly",
            }

    def is_valid_clothing_result(self, result: dict[str, Any]) -> bool:
        """Check if result contains valid clothing attributes."""
        if result.get("is_clothing") is False:
            return False
        return all(
            key in result
            for key in ["garment_type", "colors", "patterns", "style_keywords"]
        )


# Singleton instance
vision_service = VisionService()
