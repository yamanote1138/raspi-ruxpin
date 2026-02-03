"""Configuration management using Pydantic Settings.

This module provides type-safe configuration with environment variable support
and YAML override capability. Configuration precedence: env vars > YAML > defaults.
"""

import platform
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.core.exceptions import ConfigurationError


class HardwareSettings(BaseSettings):
    """Hardware-related settings for GPIO and servos."""

    model_config = SettingsConfigDict(
        env_prefix="HARDWARE__",
        env_nested_delimiter="__",
    )

    # Eyes servo pins
    eyes_pwm: int = Field(default=21, description="PWM pin for eyes servo")
    eyes_dir: int = Field(default=16, description="Direction pin for eyes servo")
    eyes_cdir: int = Field(default=20, description="Counter-direction pin for eyes servo")
    eyes_speed: int = Field(default=100, ge=1, le=1000, description="PWM frequency for eyes")
    eyes_duration: float = Field(
        default=0.8, gt=0, le=2.0, description="Default duration for eyes movement (slower for 40+ year old servos)"
    )

    # Mouth servo pins
    mouth_pwm: int = Field(default=25, description="PWM pin for mouth servo")
    mouth_dir: int = Field(default=7, description="Direction pin for mouth servo")
    mouth_cdir: int = Field(default=8, description="Counter-direction pin for mouth servo")
    mouth_speed: int = Field(default=100, ge=1, le=1000, description="PWM frequency for mouth")
    mouth_duration: float = Field(
        default=0.3, gt=0, le=2.0, description="Default duration for mouth movement (slower for 40+ year old servos)"
    )

    # Platform detection
    use_mock_gpio: bool = Field(
        default_factory=lambda: platform.system() == "Darwin",
        description="Use Mock.GPIO instead of RPi.GPIO",
    )

    @field_validator("eyes_duration", "mouth_duration")
    @classmethod
    def validate_duration(cls, v: float) -> float:
        """Ensure duration is in valid range."""
        if not (0 < v <= 2.0):
            raise ValueError("Duration must be between 0 and 2.0 seconds")
        return v


class AudioSettings(BaseSettings):
    """Audio playback settings."""

    model_config = SettingsConfigDict(
        env_prefix="AUDIO__",
        env_nested_delimiter="__",
    )

    device: str | None = Field(default=None, description="ALSA device name (e.g., 'hw:1,0', 'plughw:1,0', 'default')")
    card_index: int | None = Field(default=None, ge=0, description="ALSA card index for mixer control (0, 1, 2, etc.)")
    mixer: str = Field(default="PCM", description="ALSA mixer name (Linux only)")
    start_volume: int = Field(default=90, ge=0, le=90, description="Initial volume level (0-90, capped to prevent instability)")
    sample_rate: int = Field(default=16000, description="Audio sample rate")
    amplitude_threshold: int = Field(default=500, ge=0, description="Threshold for mouth movement")
    sounds_dir: Path = Field(default=Path("sounds"), description="Directory containing sound files")

    @field_validator("start_volume")
    @classmethod
    def validate_volume(cls, v: int) -> int:
        """Ensure volume is in valid range."""
        if not (0 <= v <= 90):
            raise ValueError("Volume must be between 0 and 90")
        return v

    @field_validator("sounds_dir")
    @classmethod
    def validate_sounds_dir(cls, v: Path) -> Path:
        """Ensure sounds directory exists."""
        if not v.is_absolute():
            v = Path.cwd() / v
        if not v.exists():
            raise ValueError(f"Sounds directory does not exist: {v}")
        return v


class TTSSettings(BaseSettings):
    """Text-to-speech settings."""

    model_config = SettingsConfigDict(
        env_prefix="TTS__",
        env_nested_delimiter="__",
    )

    engine: str = Field(default="espeak", description="TTS engine to use")
    voice: str = Field(default="en+m3", description="Voice to use for TTS")
    speed: int = Field(default=125, ge=80, le=500, description="Speaking speed (words per minute)")
    pitch: int = Field(default=50, ge=0, le=99, description="Voice pitch (0-99)")
    output_dir: Path = Field(
        default=Path("sounds/tts"), description="Directory for generated TTS files"
    )

    @field_validator("output_dir")
    @classmethod
    def ensure_output_dir(cls, v: Path) -> Path:
        """Ensure output directory exists."""
        if not v.is_absolute():
            v = Path.cwd() / v
        v.mkdir(parents=True, exist_ok=True)
        return v


class AppSettings(BaseSettings):
    """Application-wide settings."""

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    # Application settings
    environment: str = Field(
        default="development", description="Environment (development/production)"
    )
    debug: bool = Field(default=False, description="Enable debug mode")
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8080, ge=1, le=65535, description="Server port")

    # Nested settings
    hardware: HardwareSettings = Field(default_factory=HardwareSettings)
    audio: AudioSettings = Field(default_factory=AudioSettings)
    tts: TTSSettings = Field(default_factory=TTSSettings)

    # Configuration files
    config_dir: Path = Field(default=Path("config"), description="Configuration directory")
    phrases_file: Path = Field(default=Path("config/phrases.json"), description="Phrases JSON file")
    hardware_config_file: Path | None = Field(
        default=None, description="Optional YAML hardware config override"
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Ensure environment is valid."""
        valid_envs = {"development", "production", "testing"}
        if v.lower() not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v.lower()

    @field_validator("config_dir")
    @classmethod
    def ensure_config_dir(cls, v: Path) -> Path:
        """Ensure config directory exists."""
        if not v.is_absolute():
            v = Path.cwd() / v
        v.mkdir(parents=True, exist_ok=True)
        return v

    def load_yaml_overrides(self) -> None:
        """Load hardware configuration from YAML if file exists."""
        yaml_file = self.hardware_config_file or (self.config_dir / "hardware.yaml")

        if not yaml_file.exists():
            return

        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f)

            if not yaml_data:
                return

            # Apply hardware overrides
            if "hardware" in yaml_data:
                hw_data = yaml_data["hardware"]
                for key, value in hw_data.items():
                    if hasattr(self.hardware, key):
                        setattr(self.hardware, key, value)

            # Apply audio overrides
            if "audio" in yaml_data:
                audio_data = yaml_data["audio"]
                for key, value in audio_data.items():
                    if hasattr(self.audio, key):
                        setattr(self.audio, key, value)

            # Apply TTS overrides
            if "tts" in yaml_data:
                tts_data = yaml_data["tts"]
                for key, value in tts_data.items():
                    if hasattr(self.tts, key):
                        setattr(self.tts, key, value)

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to parse YAML config: {e}") from e
        except Exception as e:
            raise ConfigurationError(f"Failed to load YAML config: {e}") from e

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"

    @property
    def frontend_dist_dir(self) -> Path:
        """Get frontend build directory."""
        return Path.cwd() / "frontend" / "dist"


# Singleton instance
_settings: AppSettings | None = None


def get_settings() -> AppSettings:
    """Get or create application settings singleton."""
    global _settings
    if _settings is None:
        _settings = AppSettings()
        _settings.load_yaml_overrides()
    return _settings
