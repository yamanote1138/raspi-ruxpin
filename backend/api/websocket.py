"""WebSocket endpoint for real-time communication.

This module provides WebSocket support for the bear control interface,
handling bidirectional communication between the frontend and backend.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any, Literal

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field, ValidationError

from backend.core.enums import State, SyncMode
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


class SetSyncModeMessage(BaseModel):
    """Message to set sync mode."""

    type: Literal["set_sync_mode"] = "set_sync_mode"
    mode: str = Field(..., description="Sync mode: amplitude, phoneme, or realtime")


class AnalyzeAudioMessage(BaseModel):
    """Message to pre-analyze audio timing."""

    type: Literal["analyze_audio"] = "analyze_audio"
    sound: str = Field(..., min_length=1, description="Sound name to analyze")


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


class ConnectionManager:
    """Manages WebSocket connections and provides broadcast methods."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(
                f"WebSocket disconnected. Total connections: {len(self.active_connections)}"
            )

    async def send_personal(self, message: dict[str, Any], websocket: WebSocket) -> None:
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")

    async def broadcast(self, message: dict[str, Any]) -> None:
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)


# Global connection manager
manager = ConnectionManager()

# Background tasks
_broadcast_task: asyncio.Task[None] | None = None


async def state_broadcast_loop(bear_service: BearService) -> None:
    """Periodically broadcast bear state to all connected clients at 10Hz."""
    try:
        while True:
            if manager.active_connections:
                state = bear_service.get_state()
                response = BearStateResponse(data=state)
                await manager.broadcast(response.model_dump())
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        logger.info("State broadcast loop cancelled")
        raise
    except Exception as e:
        logger.error(f"State broadcast loop error: {e}")


# --- Helpers ---


async def _run_bear_action(
    action: Callable[[], Awaitable[None]],
    bear_service: BearService,
    websocket: WebSocket,
) -> None:
    """Run a bear action (speak/play) with busy-state broadcasting and error handling."""
    try:
        busy_state = bear_service.get_state()
        busy_state["is_busy"] = True
        await manager.broadcast(BearStateResponse(data=busy_state).model_dump())

        await action()

        final_state = bear_service.get_state()
        await manager.broadcast(BearStateResponse(data=final_state).model_dump())
    except Exception as e:
        error = ErrorResponse(message=str(e))
        await manager.send_personal(error.model_dump(), websocket)
        state = bear_service.get_state()
        await manager.broadcast(BearStateResponse(data=state).model_dump())


async def _broadcast_state(bear_service: BearService) -> None:
    """Broadcast current bear state to all clients."""
    state = bear_service.get_state()
    await manager.broadcast(BearStateResponse(data=state).model_dump())


# --- Handlers ---


async def handle_update_bear(
    message: UpdateBearMessage, bear_service: BearService, websocket: WebSocket
) -> None:
    try:
        state = await bear_service.update_positions(
            eyes_position=message.eyes,
            mouth_position=message.mouth,
        )
        await manager.broadcast(BearStateResponse(data=state).model_dump())
    except Exception as e:
        await manager.send_personal(ErrorResponse(message=str(e)).model_dump(), websocket)


async def handle_speak(
    message: SpeakMessage, bear_service: BearService, websocket: WebSocket
) -> None:
    await _run_bear_action(lambda: bear_service.speak(message.text), bear_service, websocket)


async def handle_play(
    message: PlayMessage, bear_service: BearService, websocket: WebSocket
) -> None:
    await _run_bear_action(lambda: bear_service.play_audio(message.sound), bear_service, websocket)


async def handle_set_volume(
    message: SetVolumeMessage, bear_service: BearService, websocket: WebSocket
) -> None:
    try:
        await bear_service.set_volume(message.level)
        await _broadcast_state(bear_service)
    except Exception as e:
        await manager.send_personal(ErrorResponse(message=str(e)).model_dump(), websocket)


async def handle_fetch_phrases(
    message: FetchPhrasesMessage, bear_service: BearService, websocket: WebSocket
) -> None:
    try:
        phrases = bear_service.get_phrases()
        response = PhrasesResponse(data=phrases)
        await manager.send_personal(response.model_dump(), websocket)
    except Exception as e:
        await manager.send_personal(ErrorResponse(message=str(e)).model_dump(), websocket)


async def handle_set_blink_enabled(
    message: SetBlinkEnabledMessage, bear_service: BearService, websocket: WebSocket
) -> None:
    try:
        bear_service.set_blink_enabled(message.enabled)
        await _broadcast_state(bear_service)
    except Exception as e:
        await manager.send_personal(ErrorResponse(message=str(e)).model_dump(), websocket)


async def handle_set_character(
    message: SetCharacterMessage, bear_service: BearService, websocket: WebSocket
) -> None:
    try:
        bear_service.set_character(message.character)
        await _broadcast_state(bear_service)
    except Exception as e:
        await manager.send_personal(ErrorResponse(message=str(e)).model_dump(), websocket)


async def handle_set_sync_mode(
    message: SetSyncModeMessage, bear_service: BearService, websocket: WebSocket
) -> None:
    try:
        mode = SyncMode(message.mode)
        await bear_service.set_sync_mode(mode)
        await _broadcast_state(bear_service)
    except ValueError:
        await manager.send_personal(
            ErrorResponse(message=f"Invalid sync mode: {message.mode}").model_dump(), websocket
        )
    except Exception as e:
        await manager.send_personal(ErrorResponse(message=str(e)).model_dump(), websocket)


async def handle_analyze_audio(
    message: AnalyzeAudioMessage, bear_service: BearService, websocket: WebSocket
) -> None:
    try:
        sound_file = bear_service.audio_player.resolve_sound_file(message.sound)
        timeline = await bear_service.timing_store.get_or_analyze(
            sound_file, bear_service.sync_mode
        )
        await manager.send_personal(
            SuccessResponse(
                message=f"Analyzed {message.sound}: {len(timeline)} timing events"
            ).model_dump(),
            websocket,
        )
    except Exception as e:
        await manager.send_personal(ErrorResponse(message=str(e)).model_dump(), websocket)


# --- Message routing ---

_MESSAGE_HANDLERS: dict[str, Any] = {
    "update_bear": (UpdateBearMessage, handle_update_bear),
    "speak": (SpeakMessage, handle_speak),
    "play": (PlayMessage, handle_play),
    "set_volume": (SetVolumeMessage, handle_set_volume),
    "fetch_phrases": (FetchPhrasesMessage, handle_fetch_phrases),
    "set_blink_enabled": (SetBlinkEnabledMessage, handle_set_blink_enabled),
    "set_character": (SetCharacterMessage, handle_set_character),
    "set_sync_mode": (SetSyncModeMessage, handle_set_sync_mode),
    "analyze_audio": (AnalyzeAudioMessage, handle_analyze_audio),
}


async def websocket_endpoint(websocket: WebSocket, bear_service: BearService) -> None:
    """WebSocket endpoint for bear control."""
    global _broadcast_task

    await manager.connect(websocket)
    client_info = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown"
    logger.info(f"WebSocket connected from {client_info}")

    # Start broadcast task on first connection
    if len(manager.active_connections) == 1:
        if _broadcast_task is None or _broadcast_task.done():
            _broadcast_task = asyncio.create_task(state_broadcast_loop(bear_service))
            logger.info("Started state broadcast loop")

    try:
        # Send initial state
        state = bear_service.get_state()
        await manager.send_personal(BearStateResponse(data=state).model_dump(), websocket)

        # Message handling loop
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type in _MESSAGE_HANDLERS:
                model_cls, handler = _MESSAGE_HANDLERS[message_type]
                msg = model_cls(**data)
                await handler(msg, bear_service, websocket)
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
        client_info_dc = (
            f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown"
        )
        logger.debug(f"WebSocket disconnected from {client_info_dc}")

        # Stop broadcast task if this was the last connection
        if len(manager.active_connections) == 0:
            if _broadcast_task and not _broadcast_task.done():
                _broadcast_task.cancel()
                try:
                    await _broadcast_task
                except asyncio.CancelledError:
                    pass
                logger.info("Stopped state broadcast loop")
