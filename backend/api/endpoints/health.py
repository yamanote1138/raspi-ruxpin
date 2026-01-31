"""Health check and status endpoints."""

import platform
from typing import Any

from fastapi import APIRouter

from backend import __version__
from backend.dependencies import BearServiceDep, SettingsDep

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Health status
    """
    return {
        "status": "ok",
        "version": __version__,
    }


@router.get("/status")
async def system_status(
    settings: SettingsDep,
    bear_service: BearServiceDep,
) -> dict[str, Any]:
    """Get system status.

    Args:
        settings: Application settings
        bear_service: Bear service

    Returns:
        System status information
    """
    bear_state = bear_service.get_state()

    return {
        "version": __version__,
        "environment": settings.environment,
        "platform": platform.system(),
        "bear": bear_state,
        "phrases_count": len(bear_service.get_phrases()),
    }
