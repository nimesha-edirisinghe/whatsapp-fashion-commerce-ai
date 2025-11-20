"""Health check endpoint."""

from datetime import datetime

from fastapi import APIRouter

from app.core.database import check_database_connection
from app.core.redis import check_redis_connection
from app.core.openai_client import check_openai_connection
from app.core.gemini_client import check_gemini_connection
from app.core.logging import logger

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """
    Check system health and dependencies.

    Returns status of:
    - Database (Supabase)
    - Cache (Redis)
    - AI services (OpenAI, Gemini)
    """
    checks = {
        "database": "checking",
        "redis": "checking",
        "openai": "checking",
        "gemini": "checking",
    }

    # Run health checks
    try:
        checks["database"] = "ok" if await check_database_connection() else "error"
    except Exception as e:
        logger.error(f"Database health check error: {e}")
        checks["database"] = "error"

    try:
        checks["redis"] = "ok" if await check_redis_connection() else "error"
    except Exception as e:
        logger.error(f"Redis health check error: {e}")
        checks["redis"] = "error"

    try:
        checks["openai"] = "ok" if await check_openai_connection() else "error"
    except Exception as e:
        logger.error(f"OpenAI health check error: {e}")
        checks["openai"] = "error"

    try:
        checks["gemini"] = "ok" if await check_gemini_connection() else "error"
    except Exception as e:
        logger.error(f"Gemini health check error: {e}")
        checks["gemini"] = "error"

    # Determine overall status
    all_ok = all(status == "ok" for status in checks.values())

    return {
        "status": "healthy" if all_ok else "unhealthy",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
    }
