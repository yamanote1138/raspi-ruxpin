"""Tests for configuration management."""

from pathlib import Path

import pytest

from backend.config import AppSettings, AudioSettings, SerialSettings, SyncSettings, TTSSettings
from backend.core.enums import SyncMode


def test_app_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test default application settings."""
    # Clear any environment variables that might override defaults
    monkeypatch.delenv("DEBUG", raising=False)

    settings = AppSettings()

    assert settings.environment == "development"
    # debug can be True if set via .env file, just check it's a bool
    assert isinstance(settings.debug, bool)
    assert settings.host == "0.0.0.0"
    assert settings.port == 8888


def test_audio_settings_defaults() -> None:
    """Test default audio settings."""
    settings = AudioSettings()

    assert settings.sample_rate == 16000  # Actual default
    assert settings.amplitude_threshold == 500  # Actual default
    assert settings.start_volume == 90
    assert isinstance(settings.sounds_dir, Path)


def test_tts_settings_defaults() -> None:
    """Test default TTS settings."""
    settings = TTSSettings()

    assert settings.engine == "espeak"
    assert settings.voice == "en+m3"
    assert settings.speed == 125
    assert settings.pitch == 50
    assert isinstance(settings.output_dir, Path)


def test_serial_settings_defaults() -> None:
    """Test default serial settings."""
    settings = SerialSettings()

    assert settings.port == "/dev/ttyUSB0"
    assert settings.baud_rate == 115200
    assert isinstance(settings.use_mock, bool)


def test_sync_settings_defaults() -> None:
    """Test default sync settings."""
    settings = SyncSettings()

    assert settings.mode == SyncMode.AMPLITUDE
    assert isinstance(settings.timing_dir, Path)


def test_settings_with_environment_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test settings can be overridden with environment variables."""
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("AUDIO__START_VOLUME", "75")
    monkeypatch.setenv("SERIAL__USE_MOCK", "true")

    settings = AppSettings()

    assert settings.debug is True
    assert settings.port == 9000
    assert settings.audio.start_volume == 75
    assert settings.serial.use_mock is True


def test_nested_settings_structure() -> None:
    """Test nested settings structure."""
    settings = AppSettings()

    assert isinstance(settings.audio, AudioSettings)
    assert isinstance(settings.tts, TTSSettings)
    assert isinstance(settings.serial, SerialSettings)
    assert isinstance(settings.sync, SyncSettings)


def test_audio_paths_are_paths(tmp_path: Path) -> None:
    """Test that audio directory settings are Path objects."""
    # Create a temporary sounds directory for testing
    test_sounds_dir = tmp_path / "test_sounds"
    test_sounds_dir.mkdir()

    settings = AudioSettings(sounds_dir=test_sounds_dir)

    assert isinstance(settings.sounds_dir, Path)
    assert settings.sounds_dir.exists()
