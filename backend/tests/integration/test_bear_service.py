"""Integration tests for BearService."""

import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.config import AppSettings
from backend.core.enums import MouthPosition, State, SyncMode
from backend.services.bear_service import BearService


@pytest.fixture
async def bear_service(
    integration_settings: AppSettings,
    mock_arduino: AsyncMock,
    mock_audio_player: MagicMock,
    mock_timing_store: AsyncMock,
) -> AsyncGenerator[BearService, None]:
    """Provide a BearService instance (not started)."""
    service = BearService(
        settings=integration_settings,
        arduino=mock_arduino,
        audio_player=mock_audio_player,
        timing_store=mock_timing_store,
    )
    yield service

    # Cleanup
    service._shutdown = True
    for task in [service._talk_task, service._blink_task]:
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


@pytest.mark.asyncio
async def test_bear_service_initialization(
    integration_settings: AppSettings,
    mock_arduino: AsyncMock,
    mock_audio_player: MagicMock,
    mock_timing_store: AsyncMock,
) -> None:
    """Test BearService initializes correctly."""
    service = BearService(
        settings=integration_settings,
        arduino=mock_arduino,
        audio_player=mock_audio_player,
        timing_store=mock_timing_store,
    )

    assert service.arduino is not None
    assert service.audio_player is not None
    assert service.blink_enabled is False
    assert service.is_busy is False
    assert service.sync_mode == SyncMode.AMPLITUDE
    assert service.mouth_position == MouthPosition.C


@pytest.mark.asyncio
async def test_bear_service_start(bear_service: BearService) -> None:
    """Test BearService starts background tasks."""
    await bear_service.start()

    # Background tasks should be running
    assert bear_service._talk_task is not None
    assert bear_service._blink_task is not None
    assert not bear_service._talk_task.done()
    assert not bear_service._blink_task.done()

    # Arduino should have been connected
    bear_service.arduino.connect.assert_called_once()  # type: ignore[attr-defined]

    # Eyes should be open
    bear_service.arduino.open_eyes.assert_called_once()  # type: ignore[attr-defined]
    assert bear_service.eyes_open is True


@pytest.mark.asyncio
async def test_bear_service_stop(bear_service: BearService) -> None:
    """Test BearService stops cleanly."""
    await bear_service.start()
    await bear_service.stop()

    # Tasks should be done
    assert bear_service._talk_task is None or bear_service._talk_task.done()
    assert bear_service._blink_task is None or bear_service._blink_task.done()

    # Arduino should have been disconnected
    bear_service.arduino.disconnect.assert_called_once()  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_bear_service_update_eyes(bear_service: BearService) -> None:
    """Test updating eyes position."""
    await bear_service.start()

    await bear_service.update_positions(eyes_position=State.CLOSED)
    assert bear_service.eyes_open is False
    bear_service.arduino.close_eyes.assert_called()  # type: ignore[attr-defined]

    await bear_service.update_positions(eyes_position=State.OPEN)
    assert bear_service.eyes_open is True


@pytest.mark.asyncio
async def test_bear_service_update_mouth(bear_service: BearService) -> None:
    """Test updating mouth position."""
    await bear_service.start()

    await bear_service.update_positions(mouth_position=State.OPEN)
    assert bear_service.mouth_position == MouthPosition.W
    bear_service.arduino.set_mouth_position.assert_called_with(MouthPosition.W)  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_bear_service_update_both(bear_service: BearService) -> None:
    """Test updating both eyes and mouth."""
    await bear_service.start()

    await bear_service.update_positions(eyes_position=State.CLOSED, mouth_position=State.OPEN)
    assert bear_service.eyes_open is False
    assert bear_service.mouth_position == MouthPosition.W


@pytest.mark.asyncio
async def test_bear_service_set_volume(bear_service: BearService) -> None:
    """Test setting volume."""
    await bear_service.start()

    await bear_service.set_volume(75)
    bear_service.audio_player.set_volume.assert_called_once_with(75)  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_bear_service_busy_state(bear_service: BearService) -> None:
    """Test busy state management."""
    await bear_service.start()

    # Initially not busy
    assert not bear_service.is_busy


@pytest.mark.asyncio
async def test_bear_service_toggle_blink(bear_service: BearService) -> None:
    """Test toggling auto-blink."""
    assert bear_service.blink_enabled is False

    bear_service.set_blink_enabled(True)
    assert bear_service.blink_enabled is True

    bear_service.set_blink_enabled(False)
    assert bear_service.blink_enabled is False


@pytest.mark.asyncio
async def test_bear_service_get_state(bear_service: BearService) -> None:
    """Test getting current state."""
    state = bear_service.get_state()

    assert "eyes" in state
    assert "mouth" in state
    assert "is_busy" in state
    assert "blink_enabled" in state
    assert "sync_mode" in state
    assert "mouth_code" in state
    assert "arduino_connected" in state
    assert "arduino_port" in state
    assert "arduino_baud_rate" in state
    assert "arduino_connection_type" in state
    assert state["eyes"] in ["open", "closed"]
    assert state["mouth"] in ["open", "closed"]
    assert isinstance(state["is_busy"], bool)


@pytest.mark.asyncio
async def test_bear_service_set_sync_mode_phoneme_unavailable(
    bear_service: BearService, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test switching to phoneme mode rejects when deps unavailable."""
    await bear_service.start()

    # Pretend phoneme deps are NOT installed
    monkeypatch.setattr(
        type(bear_service.settings.sync), "phoneme_available", property(lambda self: False)
    )
    monkeypatch.setattr(
        type(bear_service.settings.sync),
        "phoneme_missing_reason",
        property(lambda self: "Missing Python packages: faster-whisper"),
    )

    with pytest.raises(Exception, match="Phoneme mode unavailable"):
        await bear_service.set_sync_mode(SyncMode.PHONEME)

    # Mode should remain amplitude
    assert bear_service.sync_mode == SyncMode.AMPLITUDE


@pytest.mark.asyncio
async def test_bear_service_set_sync_mode_with_mock(
    bear_service: BearService, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test switching sync mode succeeds when deps are available."""
    await bear_service.start()

    # Pretend phoneme deps are installed
    monkeypatch.setattr(
        type(bear_service.settings.sync), "phoneme_available", property(lambda self: True)
    )

    await bear_service.set_sync_mode(SyncMode.PHONEME)
    assert bear_service.sync_mode == SyncMode.PHONEME
    # Arduino gets AMPLITUDE (serial command mode) for both amplitude and phoneme
    bear_service.arduino.set_mode.assert_called_with(SyncMode.AMPLITUDE)  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_bear_service_set_sync_mode_realtime(bear_service: BearService) -> None:
    """Test switching to realtime mode."""
    await bear_service.start()

    await bear_service.set_sync_mode(SyncMode.REALTIME)
    assert bear_service.sync_mode == SyncMode.REALTIME
    # Arduino gets REALTIME (ADC mode)
    bear_service.arduino.set_mode.assert_called_with(SyncMode.REALTIME)  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_bear_service_lifecycle_full(bear_service: BearService) -> None:
    """Test full lifecycle: start, operate, stop."""
    await bear_service.start()
    assert bear_service._talk_task is not None
    assert bear_service._blink_task is not None

    # Perform operations
    await bear_service.update_positions(eyes_position=State.OPEN, mouth_position=State.CLOSED)
    await bear_service.set_volume(80)

    # Check state
    state = bear_service.get_state()
    assert state["eyes"] == "open"
    assert state["mouth"] == "closed"

    # Stop service
    await bear_service.stop()

    if bear_service._talk_task:
        assert bear_service._talk_task.done() or bear_service._talk_task.cancelled()


@pytest.mark.asyncio
async def test_bear_service_concurrent_operations(bear_service: BearService) -> None:
    """Test handling concurrent operations."""
    await bear_service.start()

    await asyncio.gather(
        bear_service.update_positions(eyes_position=State.OPEN, mouth_position=State.CLOSED),
        bear_service.set_volume(50),
        bear_service.update_positions(eyes_position=State.CLOSED, mouth_position=State.OPEN),
    )

    state = bear_service.get_state()
    assert state["eyes"] in ["open", "closed"]
    assert state["mouth"] in ["open", "closed"]


@pytest.mark.asyncio
async def test_bear_service_error_recovery(bear_service: BearService) -> None:
    """Test error recovery in operations."""
    await bear_service.start()

    # Simulate audio player error
    bear_service.audio_player.play_file.side_effect = Exception("Audio error")  # type: ignore[attr-defined]

    with pytest.raises(Exception, match="Audio error"):
        await bear_service.play_audio("test")

    # Service should still be operational
    await bear_service.update_positions(eyes_position=State.OPEN, mouth_position=State.CLOSED)
    state = bear_service.get_state()
    assert state is not None


@pytest.mark.asyncio
async def test_bear_service_mouth_position_percent(bear_service: BearService) -> None:
    """Test mouth position percentage calculation."""
    bear_service.mouth_position = MouthPosition.C
    assert bear_service._mouth_position_percent() == 0

    bear_service.mouth_position = MouthPosition.W
    assert bear_service._mouth_position_percent() == 100

    bear_service.mouth_position = MouthPosition.N
    assert bear_service._mouth_position_percent() == 45
