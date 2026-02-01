"""Pytest configuration and fixtures for backend tests."""

import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path

from backend.config import AppSettings, HardwareSettings, AudioSettings, TTSSettings


@pytest.fixture
def mock_gpio():
    """Provide mock GPIO for tests."""
    # Mock the RPi.GPIO module
    gpio_mock = MagicMock()
    gpio_mock.BCM = 11
    gpio_mock.OUT = 0
    gpio_mock.HIGH = 1
    gpio_mock.LOW = 0

    # Mock PWM
    pwm_mock = MagicMock()
    pwm_mock.start = MagicMock()
    pwm_mock.ChangeDutyCycle = MagicMock()
    pwm_mock.stop = MagicMock()
    gpio_mock.PWM.return_value = pwm_mock

    return gpio_mock


@pytest.fixture
def test_settings():
    """Provide test configuration settings."""
    return AppSettings(
        environment="test",
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
            sample_rate=44100,
            amplitude_threshold=30,
            sounds_dir=Path("sounds"),
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
    )


@pytest.fixture
def mock_gpio_manager(mock_gpio):
    """Provide a mock GPIO manager."""
    from backend.hardware.gpio_manager import GPIOManager

    manager = GPIOManager(use_mock=True)
    manager.gpio = mock_gpio
    manager.initialize()

    return manager


@pytest.fixture
def mock_audio_player():
    """Provide a mock audio player."""
    player = MagicMock()
    player.play_file = MagicMock(return_value=None)
    player.speak = MagicMock(return_value=None)
    player.set_volume = MagicMock(return_value=None)
    player.get_amplitude = MagicMock(return_value=0)
    player.is_playing = MagicMock(return_value=False)

    return player


@pytest.fixture
async def mock_bear_service(test_settings, mock_gpio_manager, mock_audio_player):
    """Provide a mock bear service."""
    from backend.services.bear_service import BearService

    service = BearService(
        settings=test_settings,
        gpio_manager=mock_gpio_manager,
        audio_player=mock_audio_player,
    )

    # Don't actually start background tasks in tests
    service._talk_task = None
    service._blink_task = None

    return service
