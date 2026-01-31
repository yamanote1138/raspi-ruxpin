"""FastAPI dependency injection functions.

This module provides DI functions for accessing application services
and settings throughout the FastAPI application.
"""

from typing import Annotated

from fastapi import Depends, Request

from backend.config import AppSettings
from backend.services.bear_service import BearService


def get_settings(request: Request) -> AppSettings:
    """Get application settings from request state.

    Args:
        request: FastAPI request

    Returns:
        Application settings instance
    """
    return request.app.state.settings


def get_bear_service(request: Request) -> BearService:
    """Get bear service from request state.

    Args:
        request: FastAPI request

    Returns:
        Bear service instance
    """
    return request.app.state.bear_service


# Type aliases for dependency injection
SettingsDep = Annotated[AppSettings, Depends(get_settings)]
BearServiceDep = Annotated[BearService, Depends(get_bear_service)]
