"""Tests for core domain models and enums."""

import pytest

from backend.core.enums import Direction, State
from backend.core.exceptions import (
    AudioError,
    ConfigurationError,
    GPIOError,
    HardwareError,
    RaspiRuxpinError,
    ServoError,
    ValidationError,
)


def test_state_enum_values() -> None:
    """Test State enum has expected values."""
    # str-mixin Enum vs str literal: mypy's literal-overlap check doesn't know
    # these enums subclass str, so it can't see the comparison is valid.
    assert State.OPEN == "open"  # type: ignore[comparison-overlap]
    assert State.CLOSED == "closed"
    assert State.UNKNOWN == "unknown"


def test_direction_enum_values() -> None:
    """Test Direction enum has expected values."""
    assert Direction.OPENING == "opening"  # type: ignore[comparison-overlap]
    assert Direction.CLOSING == "closing"
    assert Direction.BRAKE == "brake"


def test_state_enum_comparison() -> None:
    """Test State enum comparison."""
    assert State.OPEN == State.OPEN
    assert State.OPEN != State.CLOSED  # type: ignore[comparison-overlap]
    assert State.OPEN.value == "open"


def test_direction_enum_comparison() -> None:
    """Test Direction enum comparison."""
    assert Direction.OPENING == Direction.OPENING
    assert Direction.OPENING != Direction.CLOSING  # type: ignore[comparison-overlap]
    assert Direction.BRAKE.value == "brake"


def test_raspi_ruxpin_error() -> None:
    """Test base RaspiRuxpinError exception."""
    error = RaspiRuxpinError("Base error")

    assert isinstance(error, Exception)
    assert str(error) == "Base error"


def test_hardware_error() -> None:
    """Test HardwareError exception."""
    error = HardwareError("GPIO initialization failed")

    assert isinstance(error, RaspiRuxpinError)
    assert isinstance(error, Exception)
    assert str(error) == "GPIO initialization failed"


def test_gpio_error() -> None:
    """Test GPIOError exception."""
    error = GPIOError("GPIO pin setup failed")

    assert isinstance(error, HardwareError)
    assert isinstance(error, RaspiRuxpinError)
    assert str(error) == "GPIO pin setup failed"


def test_servo_error() -> None:
    """Test ServoError exception."""
    error = ServoError("Servo movement failed")

    assert isinstance(error, HardwareError)
    assert str(error) == "Servo movement failed"


def test_audio_error() -> None:
    """Test AudioError exception."""
    error = AudioError("Audio playback failed")

    assert isinstance(error, HardwareError)
    assert str(error) == "Audio playback failed"


def test_configuration_error() -> None:
    """Test ConfigurationError exception."""
    error = ConfigurationError("Invalid configuration")

    assert isinstance(error, RaspiRuxpinError)
    assert str(error) == "Invalid configuration"


def test_validation_error() -> None:
    """Test ValidationError exception."""
    error = ValidationError("Validation failed")

    assert isinstance(error, RaspiRuxpinError)
    assert str(error) == "Validation failed"


def test_exceptions_are_catchable() -> None:
    """Test custom exceptions can be caught."""
    with pytest.raises(HardwareError):
        raise HardwareError("Test hardware error")

    with pytest.raises(GPIOError):
        raise GPIOError("Test GPIO error")

    with pytest.raises(ConfigurationError):
        raise ConfigurationError("Test config error")


def test_state_enum_all_members() -> None:
    """Test State enum has all expected members."""
    members = [member.value for member in State]

    assert "open" in members
    assert "closed" in members
    assert "unknown" in members
    assert len(members) == 3


def test_direction_enum_all_members() -> None:
    """Test Direction enum has all expected members."""
    members = [member.value for member in Direction]

    assert "opening" in members
    assert "closing" in members
    assert "brake" in members
    assert len(members) == 3
