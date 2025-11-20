"""Google Gemini client initialization and utilities."""

import google.generativeai as genai

from app.config import settings
from app.core.logging import logger

# Configure Google AI
genai.configure(api_key=settings.google_ai_api_key)

# Initialize vision model
vision_model = genai.GenerativeModel("gemini-2.0-flash-exp")


async def analyze_image(
    image_bytes: bytes,
    prompt: str,
    mime_type: str = "image/jpeg",
) -> str:
    """Analyze image using Gemini Vision model."""
    try:
        response = await vision_model.generate_content_async([
            prompt,
            {"mime_type": mime_type, "data": image_bytes},
        ])
        return response.text
    except Exception as e:
        logger.error(f"Gemini analyze_image failed: {e}")
        raise


async def analyze_clothing_image(image_bytes: bytes) -> dict:
    """
    Analyze clothing image to extract attributes.

    Returns dict with: garment_type, colors, patterns, style_keywords
    """
    prompt = """Analyze this clothing image and extract the following attributes.
Return ONLY a valid JSON object with these fields:
{
    "garment_type": "type of clothing (e.g., dress, shirt, pants)",
    "colors": ["list", "of", "colors"],
    "patterns": ["list", "of", "patterns"],
    "style_keywords": ["list", "of", "style", "descriptors"]
}

If this is not a clothing image, return:
{"is_clothing": false, "reason": "brief explanation"}
"""
    try:
        import json
        response = await analyze_image(image_bytes, prompt)
        # Clean response and parse JSON
        response_text = response.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        return json.loads(response_text)
    except Exception as e:
        logger.error(f"Gemini analyze_clothing_image failed: {e}")
        raise


async def check_gemini_connection() -> bool:
    """Check if Gemini API is accessible."""
    try:
        # Simple text generation to verify API key
        response = await vision_model.generate_content_async("Say hello")
        return bool(response.text)
    except Exception as e:
        logger.error(f"Gemini connection check failed: {e}")
        return False
