"""Pytest configuration and fixtures for backend tests."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.config import (
    AppSettings,
    AudioSettings,
    SerialSettings,
    SyncSettings,
    TTSSettings,
)
from backend.core.enums import MouthPosition, SyncMode


@pytest.fixture
def test_settings() -> AppSettings:
    """Provide test configuration settings."""
    return AppSettings(
        environment="testing",
        debug=True,
        host="127.0.0.1",
        port=8080,
        audio=AudioSettings(
            sample_rate=44100,
            amplitude_threshold=30,
            sounds_dir=Path("data/sounds"),
            start_volume=80,
            mixer="PCM",
        ),
        tts=TTSSettings(
            engine="espeak",
            output_dir=Path("/tmp/tts"),
            voice="en+m3",
            speed=125,
            pitch=50,
        ),
        serial=SerialSettings(
            port="/dev/mock",
            baud_rate=115200,
            timeout=1.0,
            connect_timeout=5.0,
            use_mock=True,
        ),
        sync=SyncSettings(
            mode=SyncMode.AMPLITUDE,
            timing_dir=Path("/tmp/timing"),
        ),
    )


@pytest.fixture
def mock_audio_player() -> MagicMock:
    """Provide a mock audio player."""
    player = MagicMock()
    player.play_file = AsyncMock(return_value=None)
    player.set_volume = AsyncMock(return_value=None)
    player.generate_tts = AsyncMock(return_value=Path("/tmp/tts/test.wav"))
    player.resolve_sound_file = MagicMock(return_value=Path("data/sounds/examples/test.wav"))
    player.list_sounds = MagicMock(return_value={})
    player.volume = 80
    player.sounds_dir = Path("data/sounds")
    return player


@pytest.fixture
def mock_arduino() -> AsyncMock:
    """Provide a mock Arduino controller."""
    arduino = AsyncMock()
    arduino.connected = True
    arduino.connect = AsyncMock()
    arduino.disconnect = AsyncMock()
    arduino.set_mouth_position = AsyncMock()
    arduino.set_mouth_angles = AsyncMock()
    arduino.open_eyes = AsyncMock()
    arduino.close_eyes = AsyncMock()
    arduino.blink_eyes = AsyncMock()
    arduino.set_mode = AsyncMock()
    arduino.set_mouth_position_callback = MagicMock()
    arduino.notify_audio_start = AsyncMock()
    arduino.notify_audio_stop = AsyncMock()
    arduino.ping = AsyncMock(return_value=True)
    arduino.get_status = AsyncMock(return_value=None)
    arduino.port = "/dev/mock"
    arduino.baud_rate = 115200
    arduino.use_mock = True
    return arduino


@pytest.fixture
def mock_timing_store() -> AsyncMock:
    """Provide a mock timing store."""
    store = AsyncMock()
    store.get_or_analyze = AsyncMock(
        return_value=[(0, MouthPosition.C), (100, MouthPosition.M), (200, MouthPosition.C)]
    )
    store.load = AsyncMock(return_value=[])
    store.save = AsyncMock()
    return store


@pytest.fixture
async def mock_bear_service(
    test_settings: AppSettings,
    mock_arduino: AsyncMock,
    mock_audio_player: MagicMock,
    mock_timing_store: AsyncMock,
) -> AsyncMock:
    """Provide a mock bear service (not started)."""
    from backend.services.bear_service import BearService

    service = BearService(
        settings=test_settings,
        arduino=mock_arduino,
        audio_player=mock_audio_player,
        timing_store=mock_timing_store,
    )

    # Don't actually start background tasks in tests
    service._talk_task = None
    service._blink_task = None

    return service  # type: ignore[return-value]
