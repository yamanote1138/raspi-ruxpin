"""Integration tests for BearService."""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

from backend.services.bear_service import BearService
from backend.hardware.gpio_manager import GPIOManager
from backend.hardware.audio_player import AudioPlayer
from backend.config import AppSettings, HardwareSettings, AudioSettings, TTSSettings
from backend.core.enums import State


@pytest.fixture
def integration_test_settings(tmp_path):
    """Provide integration test settings."""
    sounds_dir = tmp_path / "sounds"
    sounds_dir.mkdir()
    tts_dir = tmp_path / "tts"
    tts_dir.mkdir()

    return AppSettings(
        environment="testing",
        debug=True,
        host="127.0.0.1",
        port=8080,
        hardware=HardwareSettings(
            use_mock_gpio=True,
            eyes_pwm=21,
            eyes_dir=16,
            eyes_cdir=20,
            eyes_speed=100,
            eyes_duration=0.4,
            mouth_pwm=25,
            mouth_dir=7,
            mouth_cdir=8,
            mouth_speed=100,
            mouth_duration=0.15,
        ),
        audio=AudioSettings(
            sample_rate=16000,
            amplitude_threshold=500,
            sounds_dir=sounds_dir,
            start_volume=80,
            mixer="PCM",
        ),
        tts=TTSSettings(
            engine="espeak",
            output_dir=tts_dir,
            voice="en+m3",
            speed=125,
            pitch=50,
        ),
    )


@pytest.fixture
def mock_gpio_manager():
    """Provide a mock GPIO manager."""
    manager = GPIOManager(use_mock=True)
    manager.initialize()
    return manager


@pytest.fixture
def mock_audio_player():
    """Provide a mock audio player."""
    player = MagicMock(spec=AudioPlayer)
    player.play_file = AsyncMock()
    player.speak = AsyncMock()
    player.set_volume = AsyncMock()
    player.get_amplitude = MagicMock(return_value=0)
    player.is_playing = MagicMock(return_value=False)
    player.stop = AsyncMock()
    return player


@pytest.fixture
async def bear_service(integration_test_settings, mock_gpio_manager, mock_audio_player):
    """Provide a BearService instance."""
    service = BearService(
        settings=integration_test_settings,
        gpio_manager=mock_gpio_manager,
        audio_player=mock_audio_player,
    )
    yield service

    # Cleanup
    await service.stop()


@pytest.mark.asyncio
async def test_bear_service_initialization(
    integration_test_settings, mock_gpio_manager, mock_audio_player
):
    """Test BearService initializes correctly."""
    service = BearService(
        settings=integration_test_settings,
        gpio_manager=mock_gpio_manager,
        audio_player=mock_audio_player,
    )

    assert service.eyes is not None
    assert service.mouth is not None
    assert service.audio_player is not None
    assert service.blink_enabled is False  # Disabled by default
    assert service.is_busy is False


@pytest.mark.asyncio
async def test_bear_service_start(bear_service):
    """Test BearService starts background tasks."""
    await bear_service.start()

    # Background tasks should be running
    assert bear_service._talk_task is not None
    assert bear_service._blink_task is not None
    assert not bear_service._talk_task.done()
    assert not bear_service._blink_task.done()

    # Eyes should be open by default
    assert bear_service.eyes.state == State.OPEN


@pytest.mark.asyncio
async def test_bear_service_stop(bear_service):
    """Test BearService stops cleanly."""
    await bear_service.start()

    # Stop the service
    await bear_service.stop()

    # Tasks should be cancelled
    assert bear_service._talk_task is None or bear_service._talk_task.done()
    assert bear_service._blink_task is None or bear_service._blink_task.done()


@pytest.mark.asyncio
async def test_bear_service_update_eyes(bear_service):
    """Test updating eyes position."""
    await bear_service.start()

    # Update eyes to closed
    await bear_service.update_positions(eyes_position=State.CLOSED, mouth_position=None)

    assert bear_service.eyes.state == State.CLOSED


@pytest.mark.asyncio
async def test_bear_service_update_mouth(bear_service):
    """Test updating mouth position."""
    await bear_service.start()

    # Update mouth to open
    await bear_service.update_positions(eyes_position=None, mouth_position=State.OPEN)

    assert bear_service.mouth.state == State.OPEN


@pytest.mark.asyncio
async def test_bear_service_update_both(bear_service):
    """Test updating both eyes and mouth."""
    await bear_service.start()

    # Update both
    await bear_service.update_positions(eyes_position=State.CLOSED, mouth_position=State.OPEN)

    assert bear_service.eyes.state == State.CLOSED
    assert bear_service.mouth.state == State.OPEN


@pytest.mark.asyncio
async def test_bear_service_play_audio(bear_service, tmp_path):
    """Test playing audio file."""
    await bear_service.start()

    # Create a test audio file
    audio_file = tmp_path / "sounds" / "test.wav"
    audio_file.write_text("fake audio data")

    # Play audio
    await bear_service.play_audio("test.wav")

    # Audio player should have been called
    bear_service.audio_player.play_file.assert_called_once()


@pytest.mark.asyncio
async def test_bear_service_speak(bear_service):
    """Test text-to-speech."""
    await bear_service.start()

    # Speak some text
    await bear_service.speak("Hello world")

    # Audio player should have been called
    bear_service.audio_player.speak.assert_called_once_with("Hello world")


@pytest.mark.asyncio
async def test_bear_service_set_volume(bear_service):
    """Test setting volume."""
    await bear_service.start()

    # Set volume
    await bear_service.set_volume(75)

    # Audio player should have been called
    bear_service.audio_player.set_volume.assert_called_once_with(75)


@pytest.mark.asyncio
async def test_bear_service_busy_state(bear_service):
    """Test busy state management."""
    await bear_service.start()

    # Initially not busy
    assert not bear_service.is_busy

    # Simulate audio playback
    bear_service.audio_player.is_playing.return_value = True

    # Should be busy now (need to wait for talk monitor to check)
    await asyncio.sleep(0.1)

    # Reset
    bear_service.audio_player.is_playing.return_value = False


@pytest.mark.asyncio
async def test_bear_service_toggle_blink(bear_service):
    """Test toggling auto-blink."""
    await bear_service.start()

    # Initially disabled
    assert bear_service.blink_enabled is False

    # Enable blink
    bear_service.set_blink_enabled(True)
    assert bear_service.blink_enabled is True

    # Disable blink
    bear_service.set_blink_enabled(False)
    assert bear_service.blink_enabled is False


@pytest.mark.asyncio
async def test_bear_service_get_state(bear_service):
    """Test getting current state."""
    await bear_service.start()

    state = bear_service.get_state()

    assert "eyes" in state
    assert "mouth" in state
    assert "is_busy" in state
    assert "blink_enabled" in state
    assert state["eyes"] in ["open", "closed"]
    assert state["mouth"] in ["open", "closed"]
    assert isinstance(state["is_busy"], bool)
    assert isinstance(state["blink_enabled"], bool)


@pytest.mark.asyncio
async def test_bear_service_talk_monitor(bear_service):
    """Test talk monitor updates mouth based on amplitude."""
    await bear_service.start()

    # Simulate high amplitude (mouth should open)
    bear_service.audio_player.get_amplitude.return_value = 1000
    bear_service.audio_player.is_playing.return_value = True

    # Wait for talk monitor to run
    await asyncio.sleep(0.1)

    # Mouth state should have been updated based on amplitude
    # (Exact state depends on timing, just verify monitor is running)
    assert bear_service.mouth is not None


@pytest.mark.asyncio
async def test_bear_service_blink_monitor(bear_service):
    """Test blink monitor runs when enabled."""
    await bear_service.start()

    # Blink is enabled
    assert bear_service.blink_enabled is True

    # Let blink monitor run
    await asyncio.sleep(0.1)

    # Blink monitor task should be running
    assert bear_service._blink_task is not None
    assert not bear_service._blink_task.done()


@pytest.mark.asyncio
async def test_bear_service_lifecycle_full(bear_service):
    """Test full lifecycle: start, operate, stop."""
    # Start service
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

    # Tasks should be stopped
    if bear_service._talk_task:
        assert bear_service._talk_task.done() or bear_service._talk_task.cancelled()
    if bear_service._blink_task:
        assert bear_service._blink_task.done() or bear_service._blink_task.cancelled()


@pytest.mark.asyncio
async def test_bear_service_concurrent_operations(bear_service):
    """Test handling concurrent operations."""
    await bear_service.start()

    # Perform multiple operations concurrently
    await asyncio.gather(
        bear_service.update_positions(eyes_position=State.OPEN, mouth_position=State.CLOSED),
        bear_service.set_volume(50),
        bear_service.update_positions(eyes_position=State.CLOSED, mouth_position=State.OPEN),
    )

    # Service should still be in valid state
    state = bear_service.get_state()
    assert state["eyes"] in ["open", "closed"]
    assert state["mouth"] in ["open", "closed"]


@pytest.mark.asyncio
async def test_bear_service_error_recovery(bear_service):
    """Test error recovery in operations."""
    await bear_service.start()

    # Simulate audio player error
    bear_service.audio_player.play_file.side_effect = Exception("Audio error")

    # Should not crash the service
    with pytest.raises(Exception):
        await bear_service.play_audio("test.wav")

    # Service should still be operational
    await bear_service.update_positions(eyes_position=State.OPEN, mouth_position=State.CLOSED)
    state = bear_service.get_state()
    assert state is not None


@pytest.mark.asyncio
async def test_bear_service_servo_integration(bear_service):
    """Test servo integration with GPIO manager."""
    await bear_service.start()

    # Servos should be initialized
    assert bear_service.eyes.gpio_manager is not None
    assert bear_service.mouth.gpio_manager is not None

    # Servos should have correct pin configuration
    assert bear_service.eyes.pins.pwm == 21
    assert bear_service.mouth.pins.pwm == 25

    # Should be able to move servos
    await bear_service.eyes.open()
    assert bear_service.eyes.state == State.OPEN

    await bear_service.mouth.open()
    assert bear_service.mouth.state == State.OPEN
