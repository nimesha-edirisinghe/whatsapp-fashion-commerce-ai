"""Custom exception classes for the application."""

from typing import Any


class BaseAppException(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ServiceError(BaseAppException):
    """Error in business logic or service layer."""

    pass


class ValidationError(BaseAppException):
    """Error in data validation."""

    pass


class ExternalAPIError(BaseAppException):
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


class DatabaseError(BaseAppException):
    """Error in database operations."""

    pass


class SessionError(BaseAppException):
    """Error in session/cache operations."""

    pass


class EscalationError(BaseAppException):
    """Error in human escalation process."""

    pass
