"""Custom exception classes for the application."""

from typing import Any


class BaseAppError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ServiceError(BaseAppError):
    """Error in business logic or service layer."""

    pass


class ValidationError(BaseAppError):
    """Error in data validation."""

    pass


class ExternalAPIError(BaseAppError):
    """Error communicating with external APIs."""

    def __init__(
        self,
        message: str,
        service: str,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.service = service
        self.status_code = status_code
        super().__init__(message, details)


class WhatsAppAPIError(ExternalAPIError):
    """Error from WhatsApp Cloud API."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, "whatsapp", status_code, details)


class OpenAIError(ExternalAPIError):
    """Error from OpenAI API."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, "openai", status_code, details)


class GeminiError(ExternalAPIError):
    """Error from Google Gemini API."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, "gemini", status_code, details)


class DatabaseError(BaseAppError):
    """Error in database operations."""

    pass


class SessionError(BaseAppError):
    """Error in session/cache operations."""

    pass


class EscalationError(BaseAppError):
    """Error in human escalation process."""

    pass
