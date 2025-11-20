"""WhatsApp Cloud API client service."""

from typing import Any

import httpx

from app.config import settings
from app.core.exceptions import WhatsAppAPIError
from app.core.logging import logger
from app.utils.retry import async_retry


class WhatsAppService:
    """Service for interacting with WhatsApp Cloud API."""

    def __init__(self) -> None:
        self.access_token = settings.whatsapp_access_token
        self.phone_number_id = settings.whatsapp_phone_number_id
        self.base_url = settings.whatsapp_base_url

    @async_retry(attempts=1, timeout=3.0)
    async def send_message(self, message: dict[str, Any]) -> dict[str, Any]:
        """Send a message via WhatsApp Cloud API."""
        url = f"{self.base_url}/{self.phone_number_id}/messages"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                json=message,
            )

            if response.status_code != 200:
                logger.error(f"WhatsApp API error: {response.text}")
                raise WhatsAppAPIError(
                    message=f"Failed to send message: {response.text}",
                    status_code=response.status_code,
                    details={"response": response.text},
                )

            return response.json()

    @async_retry(attempts=1, timeout=3.0)
    async def download_media(self, media_id: str) -> bytes:
        """Download media file from WhatsApp servers."""
        # First, get the media URL
        url = f"{self.base_url}/{media_id}"

        async with httpx.AsyncClient() as client:
            # Get media URL
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {self.access_token}"},
            )

            if response.status_code != 200:
                raise WhatsAppAPIError(
                    message=f"Failed to get media URL: {response.text}",
                    status_code=response.status_code,
                )

            media_url = response.json().get("url")
            if not media_url:
                raise WhatsAppAPIError(
                    message="No URL in media response",
                    status_code=response.status_code,
                )

            # Download the actual media
            media_response = await client.get(
                media_url,
                headers={"Authorization": f"Bearer {self.access_token}"},
            )

            if media_response.status_code != 200:
                raise WhatsAppAPIError(
                    message=f"Failed to download media: {media_response.text}",
                    status_code=media_response.status_code,
                )

            return media_response.content

    async def send_text(self, to: str, text: str) -> dict[str, Any]:
        """Convenience method to send a text message."""
        from app.utils.message_builder import build_text_message
        return await self.send_message(build_text_message(to, text))


# Singleton instance
whatsapp_service = WhatsAppService()
