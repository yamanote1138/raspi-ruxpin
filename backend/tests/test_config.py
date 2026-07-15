"""Tests for configuration management."""

from pathlib import Path

import pytest

from backend.config import AppSettings, AudioSettings, HardwareSettings, TTSSettings


def test_app_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test default application settings."""
    # Clear any environment variables that might override defaults
    monkeypatch.delenv("DEBUG", raising=False)

    settings = AppSettings()

    assert settings.environment == "development"
    # debug can be True if set via .env file, just check it's a bool
    assert isinstance(settings.debug, bool)
    assert settings.host == "0.0.0.0"
    assert settings.port == 8080


def test_hardware_settings_defaults() -> None:
    """Test default hardware settings."""
    settings = HardwareSettings()

    # GPIO settings
    # use_mock_gpio defaults to True on macOS (Darwin)
    assert isinstance(settings.use_mock_gpio, bool)
    assert settings.eyes_pwm == 21
    assert settings.mouth_pwm == 25

    # Servo timing
    assert settings.eyes_duration == 0.8
    assert settings.mouth_duration == 0.3


def test_audio_settings_defaults() -> None:
    """Test default audio settings."""
    settings = AudioSettings()

    assert settings.sample_rate == 16000  # Actual default
    assert settings.amplitude_threshold == 500  # Actual default
    assert settings.start_volume == 90  # Capped to prevent instability
    assert isinstance(settings.sounds_dir, Path)


def test_tts_settings_defaults() -> None:
    """Test default TTS settings."""
    settings = TTSSettings()

    assert settings.engine == "espeak"
    assert settings.voice == "en+m3"
    assert settings.speed == 125
    assert settings.pitch == 50
    assert isinstance(settings.output_dir, Path)


def test_settings_with_environment_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test settings can be overridden with environment variables."""
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("HARDWARE__USE_MOCK_GPIO", "true")
    monkeypatch.setenv("AUDIO__START_VOLUME", "75")

    settings = AppSettings()

    assert settings.debug is True
    assert settings.port == 9000
    assert settings.hardware.use_mock_gpio is True
    assert settings.audio.start_volume == 75


def test_nested_settings_structure() -> None:
    """Test nested settings structure."""
    settings = AppSettings()

    assert isinstance(settings.hardware, HardwareSettings)
    assert isinstance(settings.audio, AudioSettings)
    assert isinstance(settings.tts, TTSSettings)


def test_hardware_gpio_pin_configuration() -> None:
    """Test GPIO pin configuration."""
    settings = HardwareSettings(
        eyes_pwm=20,
        eyes_dir=21,
        eyes_cdir=22,
        mouth_pwm=23,
        mouth_dir=24,
        mouth_cdir=25,
    )

    # Eyes pins
    assert settings.eyes_pwm == 20
    assert settings.eyes_dir == 21
    assert settings.eyes_cdir == 22

    # Mouth pins
    assert settings.mouth_pwm == 23
    assert settings.mouth_dir == 24
    assert settings.mouth_cdir == 25


def test_audio_paths_are_paths(tmp_path: Path) -> None:
    """Test that audio directory settings are Path objects."""
    # Create a temporary sounds directory for testing
    test_sounds_dir = tmp_path / "test_sounds"
    test_sounds_dir.mkdir()

    # Pydantic coerces this str to Path at runtime; mypy can't see that coercion.
    settings = AudioSettings(sounds_dir=str(test_sounds_dir))  # type: ignore[arg-type]

    assert isinstance(settings.sounds_dir, Path)
    assert settings.sounds_dir.exists()
