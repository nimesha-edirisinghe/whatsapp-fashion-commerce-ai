"""OpenAI client initialization and utilities."""

from openai import AsyncOpenAI

from app.config import settings
from app.core.logging import logger

# Initialize async OpenAI client
openai_client = AsyncOpenAI(api_key=settings.openai_api_key)


async def generate_response(
    messages: list[dict[str, str]],
    model: str = "gpt-4o",
    temperature: float = 0.7,
    max_tokens: int = 500,
) -> str:
    """Generate text response using GPT model."""
    try:
        response = await openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        logger.error(f"OpenAI generate_response failed: {e}")
        raise


async def create_embedding(text: str) -> list[float]:
    """Create embedding vector for text using OpenAI."""
    try:
        response = await openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"OpenAI create_embedding failed: {e}")
        raise


async def check_openai_connection() -> bool:
    """Check if OpenAI API is accessible."""
    try:
        # Simple models list call to verify API key
        await openai_client.models.list()
        return True
    except Exception as e:
        logger.error(f"OpenAI connection check failed: {e}")
        return False
