"""FastAPI application for Raspi Ruxpin.

This is the main entry point for the backend server. It sets up the FastAPI
application with WebSocket support, CORS, static file serving, and lifecycle management.
"""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.endpoints.health import router as health_router
from backend.api.websocket import websocket_endpoint
from backend.config import get_settings
from backend.hardware.audio_player import AudioPlayer
from backend.hardware.gpio_manager import GPIOManager
from backend.services.bear_service import BearService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Handles startup and shutdown tasks:
    - Initialize settings, GPIO, audio player, and bear service
    - Start bear service background tasks
    - Clean up on shutdown

    Args:
        app: FastAPI application

    Yields:
        None
    """
    # Startup
    logger.info("Starting Raspi Ruxpin backend...")

    try:
        # Load settings
        settings = get_settings()
        app.state.settings = settings

        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Debug mode: {settings.debug}")

        # Initialize GPIO manager
        gpio_manager = GPIOManager(use_mock=settings.hardware.use_mock_gpio)
        gpio_manager.initialize()
        app.state.gpio_manager = gpio_manager

        # Initialize audio player
        audio_player = AudioPlayer(
            sample_rate=settings.audio.sample_rate,
            amplitude_threshold=settings.audio.amplitude_threshold,
            sounds_dir=settings.audio.sounds_dir,
            tts_output_dir=settings.tts.output_dir,
            tts_engine=settings.tts.engine,
            tts_voice=settings.tts.voice,
            tts_speed=settings.tts.speed,
            start_volume=settings.audio.start_volume,
        )
        app.state.audio_player = audio_player

        # Initialize bear service
        bear_service = BearService(
            settings=settings,
            gpio_manager=gpio_manager,
            audio_player=audio_player,
        )
        await bear_service.start()
        app.state.bear_service = bear_service

        logger.info("Raspi Ruxpin backend started successfully")

        yield

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    finally:
        # Shutdown
        logger.info("Shutting down Raspi Ruxpin backend...")

        try:
            if hasattr(app.state, "bear_service"):
                await app.state.bear_service.stop()

            if hasattr(app.state, "gpio_manager"):
                app.state.gpio_manager.cleanup_all()

            logger.info("Raspi Ruxpin backend shut down successfully")
        except Exception as e:
            logger.error(f"Shutdown error: {e}")


# Create FastAPI application
app = FastAPI(
    title="Raspi Ruxpin",
    description="Modern animatronic bear control system",
    version="2.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    """WebSocket endpoint for real-time communication."""
    bear_service = app.state.bear_service
    await websocket_endpoint(websocket, bear_service)


# Serve static files in production
settings = get_settings()
if settings.is_production and settings.frontend_dist_dir.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(settings.frontend_dist_dir), html=True),
        name="frontend",
    )
    logger.info(f"Serving frontend from {settings.frontend_dist_dir}")

# Serve sounds directory
if settings.audio.sounds_dir.exists():
    app.mount(
        "/sounds",
        StaticFiles(directory=str(settings.audio.sounds_dir)),
        name="sounds",
    )
    logger.info(f"Serving sounds from {settings.audio.sounds_dir}")


def main() -> None:
    """Main entry point for CLI."""
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        log_level="debug" if settings.debug else "info",
    )


if __name__ == "__main__":
    main()
