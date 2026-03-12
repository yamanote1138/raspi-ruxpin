"""Configuration management using Pydantic Settings.

This module provides type-safe configuration with environment variable support
and YAML override capability. Configuration precedence: env vars > YAML > defaults.
"""

import platform
from pathlib import Path

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.core.enums import ServoType, SyncMode
from backend.core.exceptions import ConfigurationError


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
    sounds_dir: Path = Field(default=Path("data/sounds"), description="Directory containing sound files")

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
        """Ensure sounds directory and required subdirectories exist."""
        if not v.is_absolute():
            v = Path.cwd() / v
        if not v.exists():
            raise ValueError(f"Sounds directory does not exist: {v}")
        (v / "examples").mkdir(exist_ok=True)
        (v / "user").mkdir(exist_ok=True)
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
        default=Path("data/tts"), description="Directory for generated TTS files"
    )

    @field_validator("output_dir")
    @classmethod
    def ensure_output_dir(cls, v: Path) -> Path:
        """Ensure output directory exists."""
        if not v.is_absolute():
            v = Path.cwd() / v
        v.mkdir(parents=True, exist_ok=True)
        return v


class SerialSettings(BaseSettings):
    """Serial communication settings for Arduino connection."""

    model_config = SettingsConfigDict(
        env_prefix="SERIAL__",
        env_nested_delimiter="__",
    )

    port: str = Field(default="/dev/ttyUSB0", description="Serial port for Arduino")
    baud_rate: int = Field(default=115200, description="Serial baud rate")
    timeout: float = Field(default=1.0, gt=0, description="Serial read timeout in seconds")
    connect_timeout: float = Field(
        default=10.0, gt=0, description="Timeout waiting for Arduino READY signal"
    )
    use_mock: bool = Field(
        default_factory=lambda: platform.system() == "Darwin",
        description="Use mock serial instead of real serial (auto-detected on macOS)",
    )


class SyncSettings(BaseSettings):
    """Audio-to-mouth synchronization settings."""

    model_config = SettingsConfigDict(
        env_prefix="SYNC__",
        env_nested_delimiter="__",
    )

    mode: SyncMode = Field(default=SyncMode.AMPLITUDE, description="Sync mode")
    servo_type: ServoType = Field(
        default=ServoType.HBRIDGE, description="Servo hardware type on Arduino"
    )
    calibration_file: Path = Field(
        default=Path("config/jaw_calibration.json"),
        description="Jaw calibration data file",
    )
    timing_dir: Path = Field(
        default=Path("data/timing"), description="Directory for cached timing CSVs"
    )

    @field_validator("timing_dir")
    @classmethod
    def ensure_timing_dir(cls, v: Path) -> Path:
        """Ensure timing directory exists."""
        if not v.is_absolute():
            v = Path.cwd() / v
        v.mkdir(parents=True, exist_ok=True)
        return v

    @property
    def phoneme_available(self) -> bool:
        """Check if phoneme analysis dependencies are installed.

        Requires both Python packages (faster-whisper, phonemizer) and
        the espeak-ng system binary + shared library (used by phonemizer).
        """
        return self.phoneme_missing_reason is None

    @property
    def phoneme_missing_reason(self) -> str | None:
        """Return a human-readable reason why phoneme mode is unavailable, or None."""
        import ctypes.util
        import shutil

        missing_pkgs = []
        try:
            import faster_whisper  # noqa: F401
        except ImportError:
            missing_pkgs.append("faster-whisper")
        try:
            import phonemizer  # noqa: F401
        except ImportError:
            missing_pkgs.append("phonemizer")

        if missing_pkgs:
            return (
                f"Missing Python packages: {', '.join(missing_pkgs)}. "
                "Install with: uv pip install -e '.[phoneme]'"
            )

        if not shutil.which("espeak-ng") and not shutil.which("espeak"):
            return (
                "espeak-ng is not installed on your system. "
                "Install with: brew install espeak-ng (macOS) "
                "or apt install espeak-ng (Linux)"
            )

        # Check shared library is discoverable (phonemizer uses ctypes)
        if ctypes.util.find_library("espeak-ng") is None:
            # Check if it exists in Homebrew but isn't in search path
            from pathlib import Path as _Path

            for lib_dir in ["/opt/homebrew/lib", "/usr/local/lib"]:
                if _Path(lib_dir, "libespeak-ng.dylib").exists():
                    # Library exists but ctypes can't find it — will be fixed at runtime
                    return None
            return (
                "espeak-ng shared library not found. "
                "Install with: brew install espeak-ng (macOS) "
                "or apt install libespeak-ng-dev (Linux)"
            )

        return None


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
    port: int = Field(default=8888, ge=1, le=65535, description="Server port")

    # Nested settings
    audio: AudioSettings = Field(default_factory=AudioSettings)
    tts: TTSSettings = Field(default_factory=TTSSettings)
    serial: SerialSettings = Field(default_factory=SerialSettings)
    sync: SyncSettings = Field(default_factory=SyncSettings)

    # Configuration files
    config_dir: Path = Field(default=Path("config"), description="Configuration directory")
    hardware_config_file: Path | None = Field(
        default=None, description="Optional YAML config override"
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
        """Load configuration overrides from YAML if file exists."""
        yaml_file = self.hardware_config_file or (self.config_dir / "hardware.yaml")

        if not yaml_file.exists():
            return

        try:
            with open(yaml_file, encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f)

            if not yaml_data:
                return

            for section_name in ("audio", "tts", "serial", "sync"):
                if section_name in yaml_data:
                    section_obj = getattr(self, section_name)
                    for key, value in yaml_data[section_name].items():
                        if hasattr(section_obj, key):
                            setattr(section_obj, key, value)

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
