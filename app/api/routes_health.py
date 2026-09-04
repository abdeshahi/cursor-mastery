"""Health check API routes."""

from fastapi import APIRouter

from app.core.config import get_settings
from app.core.constants import (
    HEALTH_STATUS_DEGRADED,
    HEALTH_STATUS_HEALTHY,
    HEALTH_STATUS_UNHEALTHY,
)
from app.database.db import check_database_connection

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """Return application and dependency health status."""
    settings = get_settings()
    db_ok, db_error = await check_database_connection()

    if db_ok:
        status = HEALTH_STATUS_HEALTHY
    else:
        status = HEALTH_STATUS_DEGRADED

    response = {
        "status": status,
        "app": settings.app_name,
        "version": settings.app_version,
        "paper_mode": settings.paper_mode,
        "checks": {
            "database": {
                "status": HEALTH_STATUS_HEALTHY if db_ok else HEALTH_STATUS_UNHEALTHY,
                "error": db_error,
            }
        },
    }
    return response
