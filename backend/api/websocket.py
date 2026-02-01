"""WebSocket endpoint for real-time communication.

This module provides WebSocket support for the bear control interface,
handling bidirectional communication between the frontend and backend.
"""

import asyncio
import logging
import queue
from typing import Any, Literal

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field, ValidationError

from backend.core.enums import State
from backend.logging_config import log_queue, set_log_level
from backend.services.bear_service import BearService

logger = logging.getLogger(__name__)


# Message models
class UpdateBearMessage(BaseModel):
    """Message to update bear positions."""

    type: Literal["update_bear"] = "update_bear"
    eyes: State | None = None
    mouth: State | None = None


class SpeakMessage(BaseModel):
    """Message to speak text."""

    type: Literal["speak"] = "speak"
    text: str = Field(..., min_length=1, max_length=500)


class PlayMessage(BaseModel):
    """Message to play audio."""

    type: Literal["play"] = "play"
    sound: str = Field(..., min_length=1)


class SetVolumeMessage(BaseModel):
    """Message to set volume."""

    type: Literal["set_volume"] = "set_volume"
    level: int = Field(..., ge=0, le=100)


class FetchPhrasesMessage(BaseModel):
    """Message to fetch available phrases."""

    type: Literal["fetch_phrases"] = "fetch_phrases"


class SetBlinkEnabledMessage(BaseModel):
    """Message to enable/disable eye blinking."""

    type: Literal["set_blink_enabled"] = "set_blink_enabled"
    enabled: bool = Field(..., description="Enable or disable blinking")


class SetCharacterMessage(BaseModel):
    """Message to set character."""

    type: Literal["set_character"] = "set_character"
    character: str = Field(..., min_length=1, description="Character name (teddy or grubby)")


class SetLogLevelMessage(BaseModel):
    """Message to set logging level."""

    type: Literal["set_log_level"] = "set_log_level"
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        ..., description="Logging level"
    )


class GetGPIOStatusMessage(BaseModel):
    """Message to request GPIO status."""

    type: Literal["get_gpio_status"] = "get_gpio_status"


# Response models
class BearStateResponse(BaseModel):
    """Bear state response."""

    type: Literal["bear_state"] = "bear_state"
    data: dict[str, Any]


class PhrasesResponse(BaseModel):
    """Phrases response."""

    type: Literal["phrases"] = "phrases"
    data: dict[str, str]


class ErrorResponse(BaseModel):
    """Error response."""

    type: Literal["error"] = "error"
    message: str


class SuccessResponse(BaseModel):
    """Success response."""

    type: Literal["success"] = "success"
    message: str


class LogMessageResponse(BaseModel):
    """Log message response."""

    type: Literal["log"] = "log"
    data: dict[str, Any]  # Contains: timestamp, level, logger, message, module, function, line


class GPIOStatusResponse(BaseModel):
    """GPIO status response."""

    type: Literal["gpio_status"] = "gpio_status"
    data: dict[str, Any]  # Contains: pins: dict[int, bool]


class ConnectionManager:
    """Manages WebSocket connections.

    This class handles multiple WebSocket connections and provides
    methods for broadcasting messages to all connected clients.

    Attributes:
        active_connections: List of active WebSocket connections
    """

    def __init__(self) -> None:
        """Initialize connection manager."""
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket connection to register
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Unregister a WebSocket connection.

        Args:
            websocket: WebSocket connection to remove
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(
                f"WebSocket disconnected. Total connections: {len(self.active_connections)}"
            )
        else:
            logger.debug("Attempted to disconnect websocket that was not in active connections")

    async def send_personal(self, message: dict[str, Any], websocket: WebSocket) -> None:
        """Send a message to a specific client.

        Args:
            message: Message to send
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast a message to all connected clients.

        Args:
            message: Message to broadcast
        """
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)


# Global connection manager
manager = ConnectionManager()

# Background tasks
_broadcast_task: asyncio.Task[None] | None = None
_log_stream_task: asyncio.Task[None] | None = None


async def state_broadcast_loop(bear_service: BearService) -> None:
    """Periodically broadcast bear state to all connected clients.

    This runs at 10Hz to provide smooth visual updates of mouth movements.
    """
    try:
        while True:
            if manager.active_connections:
                state = bear_service.get_state()
                response = BearStateResponse(data=state)
                await manager.broadcast(response.model_dump())

                # Also broadcast GPIO status (every 10 iterations = 1Hz for efficiency)
                if hasattr(state_broadcast_loop, '_gpio_counter'):
                    state_broadcast_loop._gpio_counter += 1
                else:
                    state_broadcast_loop._gpio_counter = 0

                if state_broadcast_loop._gpio_counter >= 10:
                    state_broadcast_loop._gpio_counter = 0
                    gpio_states = bear_service.gpio_manager.get_pin_states()
                    gpio_response = GPIOStatusResponse(data={"pins": gpio_states})
                    await manager.broadcast(gpio_response.model_dump())

            await asyncio.sleep(0.1)  # 10Hz update rate
    except asyncio.CancelledError:
        logger.info("State broadcast loop cancelled")
        raise
    except Exception as e:
        logger.error(f"State broadcast loop error: {e}")


async def log_stream_loop() -> None:
    """Stream log messages to all connected clients.

    This continuously monitors the log queue and broadcasts new log entries.
    """
    try:
        while True:
            if manager.active_connections:
                try:
                    # Get log entry from queue (non-blocking)
                    log_entry = log_queue.get_nowait()
                    response = LogMessageResponse(data=log_entry)
                    await manager.broadcast(response.model_dump())
                except queue.Empty:
                    # No logs available, wait a bit
                    await asyncio.sleep(0.05)
            else:
                await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        logger.debug("Log stream loop cancelled")
        raise
    except Exception as e:
        logger.error(f"Log stream loop error: {e}")


async def handle_update_bear(
    message: UpdateBearMessage, bear_service: BearService, websocket: WebSocket
) -> None:
    """Handle update_bear message.

    Args:
        message: Update bear message
        bear_service: Bear service instance
        websocket: WebSocket connection
    """
    try:
        state = await bear_service.update_positions(
            eyes_position=message.eyes,
            mouth_position=message.mouth,
        )

        response = BearStateResponse(data=state)
        await manager.broadcast(response.model_dump())
    except Exception as e:
        error = ErrorResponse(message=str(e))
        await manager.send_personal(error.model_dump(), websocket)


async def handle_speak(
    message: SpeakMessage, bear_service: BearService, websocket: WebSocket
) -> None:
    """Handle speak message.

    Args:
        message: Speak message
        bear_service: Bear service instance
        websocket: WebSocket connection
    """
    try:
        # Notify all clients that bear is busy
        busy_state = bear_service.get_state()
        busy_state["is_busy"] = True
        response = BearStateResponse(data=busy_state)
        await manager.broadcast(response.model_dump())

        # Speak (this will block until complete)
        await bear_service.speak(message.text)

        # Notify all clients of new state
        final_state = bear_service.get_state()
        response = BearStateResponse(data=final_state)
        await manager.broadcast(response.model_dump())
    except Exception as e:
        error = ErrorResponse(message=str(e))
        await manager.send_personal(error.model_dump(), websocket)

        # Reset busy state on error
        state = bear_service.get_state()
        response = BearStateResponse(data=state)
        await manager.broadcast(response.model_dump())


async def handle_play(
    message: PlayMessage, bear_service: BearService, websocket: WebSocket
) -> None:
    """Handle play message.

    Args:
        message: Play message
        bear_service: Bear service instance
        websocket: WebSocket connection
    """
    try:
        # Notify all clients that bear is busy
        busy_state = bear_service.get_state()
        busy_state["is_busy"] = True
        response = BearStateResponse(data=busy_state)
        await manager.broadcast(response.model_dump())

        # Play audio (this will block until complete)
        await bear_service.play_audio(message.sound)

        # Notify all clients of new state
        final_state = bear_service.get_state()
        response = BearStateResponse(data=final_state)
        await manager.broadcast(response.model_dump())
    except Exception as e:
        error = ErrorResponse(message=str(e))
        await manager.send_personal(error.model_dump(), websocket)

        # Reset busy state on error
        state = bear_service.get_state()
        response = BearStateResponse(data=state)
        await manager.broadcast(response.model_dump())


async def handle_set_volume(
    message: SetVolumeMessage, bear_service: BearService, websocket: WebSocket
) -> None:
    """Handle set_volume message.

    Args:
        message: Set volume message
        bear_service: Bear service instance
        websocket: WebSocket connection
    """
    try:
        await bear_service.set_volume(message.level)

        state = bear_service.get_state()
        response = BearStateResponse(data=state)
        await manager.broadcast(response.model_dump())
    except Exception as e:
        error = ErrorResponse(message=str(e))
        await manager.send_personal(error.model_dump(), websocket)


async def handle_fetch_phrases(
    message: FetchPhrasesMessage, bear_service: BearService, websocket: WebSocket
) -> None:
    """Handle fetch_phrases message.

    Args:
        message: Fetch phrases message
        bear_service: Bear service instance
        websocket: WebSocket connection
    """
    try:
        phrases = bear_service.get_phrases()
        response = PhrasesResponse(data=phrases)
        await manager.send_personal(response.model_dump(), websocket)
    except Exception as e:
        error = ErrorResponse(message=str(e))
        await manager.send_personal(error.model_dump(), websocket)


async def handle_set_blink_enabled(
    message: SetBlinkEnabledMessage, bear_service: BearService, websocket: WebSocket
) -> None:
    """Handle set_blink_enabled message.

    Args:
        message: Set blink enabled message
        bear_service: Bear service instance
        websocket: WebSocket connection
    """
    try:
        bear_service.set_blink_enabled(message.enabled)

        state = bear_service.get_state()
        response = BearStateResponse(data=state)
        await manager.broadcast(response.model_dump())
    except Exception as e:
        error = ErrorResponse(message=str(e))
        await manager.send_personal(error.model_dump(), websocket)


async def handle_set_character(
    message: SetCharacterMessage, bear_service: BearService, websocket: WebSocket
) -> None:
    """Handle set_character message.

    Args:
        message: Set character message
        bear_service: Bear service instance
        websocket: WebSocket connection
    """
    try:
        bear_service.set_character(message.character)

        state = bear_service.get_state()
        response = BearStateResponse(data=state)
        await manager.broadcast(response.model_dump())
    except Exception as e:
        error = ErrorResponse(message=str(e))
        await manager.send_personal(error.model_dump(), websocket)


async def handle_set_log_level(message: SetLogLevelMessage, websocket: WebSocket) -> None:
    """Handle set_log_level message.

    Args:
        message: Set log level message
        websocket: WebSocket connection
    """
    try:
        set_log_level(message.level)
        logger.info(f"Log level changed to {message.level} via WebSocket")

        success = SuccessResponse(message=f"Log level set to {message.level}")
        await manager.send_personal(success.model_dump(), websocket)
    except Exception as e:
        error = ErrorResponse(message=str(e))
        await manager.send_personal(error.model_dump(), websocket)


async def handle_get_gpio_status(
    message: GetGPIOStatusMessage, bear_service: BearService, websocket: WebSocket
) -> None:
    """Handle get_gpio_status message.

    Args:
        message: Get GPIO status message
        bear_service: Bear service instance
        websocket: WebSocket connection
    """
    try:
        gpio_manager = bear_service.gpio_manager
        pin_states = gpio_manager.get_pin_states()

        response = GPIOStatusResponse(data={"pins": pin_states})
        await manager.send_personal(response.model_dump(), websocket)
    except Exception as e:
        error = ErrorResponse(message=str(e))
        await manager.send_personal(error.model_dump(), websocket)


async def websocket_endpoint(websocket: WebSocket, bear_service: BearService) -> None:
    """WebSocket endpoint for bear control.

    Args:
        websocket: WebSocket connection
        bear_service: Bear service instance
    """
    global _broadcast_task, _log_stream_task

    await manager.connect(websocket)
    logger.info(f"WebSocket connected from {websocket.client.host}:{websocket.client.port}")

    # Start state broadcast task if this is the first connection
    if len(manager.active_connections) == 1 and (_broadcast_task is None or _broadcast_task.done()):
        _broadcast_task = asyncio.create_task(state_broadcast_loop(bear_service))
        logger.info("Started state broadcast loop")

    # Start log streaming task if this is the first connection
    if len(manager.active_connections) == 1 and (
        _log_stream_task is None or _log_stream_task.done()
    ):
        _log_stream_task = asyncio.create_task(log_stream_loop())
        logger.info("Started log stream loop")
        logger.info("Log streaming is now active - you should see this message in the frontend!")

    try:
        # Send initial state
        state = bear_service.get_state()
        response = BearStateResponse(data=state)
        await manager.send_personal(response.model_dump(), websocket)

        # Message handling loop
        while True:
            data = await websocket.receive_json()

            # Route message based on type
            message_type = data.get("type")

            if message_type == "update_bear":
                msg = UpdateBearMessage(**data)
                await handle_update_bear(msg, bear_service, websocket)

            elif message_type == "speak":
                msg = SpeakMessage(**data)
                await handle_speak(msg, bear_service, websocket)

            elif message_type == "play":
                msg = PlayMessage(**data)
                await handle_play(msg, bear_service, websocket)

            elif message_type == "set_volume":
                msg = SetVolumeMessage(**data)
                await handle_set_volume(msg, bear_service, websocket)

            elif message_type == "fetch_phrases":
                msg = FetchPhrasesMessage(**data)
                await handle_fetch_phrases(msg, bear_service, websocket)

            elif message_type == "set_blink_enabled":
                msg = SetBlinkEnabledMessage(**data)
                await handle_set_blink_enabled(msg, bear_service, websocket)

            elif message_type == "set_character":
                msg = SetCharacterMessage(**data)
                await handle_set_character(msg, bear_service, websocket)

            elif message_type == "set_log_level":
                msg = SetLogLevelMessage(**data)
                await handle_set_log_level(msg, websocket)

            elif message_type == "get_gpio_status":
                msg = GetGPIOStatusMessage(**data)
                await handle_get_gpio_status(msg, bear_service, websocket)

            else:
                error = ErrorResponse(message=f"Unknown message type: {message_type}")
                await manager.send_personal(error.model_dump(), websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except ValidationError as e:
        error = ErrorResponse(message=f"Invalid message: {e}")
        await manager.send_personal(error.model_dump(), websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
    finally:
        logger.debug(f"WebSocket disconnected from {websocket.client.host}:{websocket.client.port}")

        # Stop broadcast tasks if this was the last connection
        if len(manager.active_connections) == 0:
            if _broadcast_task and not _broadcast_task.done():
                _broadcast_task.cancel()
                try:
                    await _broadcast_task
                except asyncio.CancelledError:
                    pass
                logger.info("Stopped state broadcast loop")

            if _log_stream_task and not _log_stream_task.done():
                _log_stream_task.cancel()
                try:
                    await _log_stream_task
                except asyncio.CancelledError:
                    pass
                logger.info("Stopped log stream loop")
