"""Structured logging setup with Sentry integration."""

import logging
import sys
from typing import Any

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.config import settings


def setup_logging() -> logging.Logger:
    """Configure structured logging for the application."""
    # Create logger
    logger = logging.getLogger("fashionimport")
    logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler with structured format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    # Structured format for production, readable for development
    if settings.is_production:
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"logger": "%(name)s", "message": "%(message)s"}'
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def setup_sentry() -> None:
    """Initialize Sentry for error tracking."""
    if not settings.sentry_dsn:
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.app_env,
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
        ],
        traces_sample_rate=0.1 if settings.is_production else 1.0,
        profiles_sample_rate=0.1 if settings.is_production else 1.0,
        send_default_pii=False,
    )


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    **context: Any,
) -> None:
    """Log a message with additional context."""
    if context:
        context_str = " ".join(f"{k}={v}" for k, v in context.items())
        message = f"{message} | {context_str}"
    logger.log(level, message)


# Initialize logger and Sentry
logger = setup_logging()
setup_sentry()
