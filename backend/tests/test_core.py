"""Tests for core domain models and enums."""

import pytest

from backend.core.enums import State, Direction
from backend.core.exceptions import (
    RaspiRuxpinError,
    HardwareError,
    GPIOError,
    ServoError,
    AudioError,
    ConfigurationError,
    ValidationError,
)


def test_state_enum_values():
    """Test State enum has expected values."""
    assert State.OPEN == "open"
    assert State.CLOSED == "closed"
    assert State.UNKNOWN == "unknown"


def test_direction_enum_values():
    """Test Direction enum has expected values."""
    assert Direction.OPENING == "opening"
    assert Direction.CLOSING == "closing"
    assert Direction.BRAKE == "brake"


def test_state_enum_comparison():
    """Test State enum comparison."""
    assert State.OPEN == State.OPEN
    assert State.OPEN != State.CLOSED
    assert State.OPEN.value == "open"


def test_direction_enum_comparison():
    """Test Direction enum comparison."""
    assert Direction.OPENING == Direction.OPENING
    assert Direction.OPENING != Direction.CLOSING
    assert Direction.BRAKE.value == "brake"


def test_raspi_ruxpin_error():
    """Test base RaspiRuxpinError exception."""
    error = RaspiRuxpinError("Base error")

    assert isinstance(error, Exception)
    assert str(error) == "Base error"


def test_hardware_error():
    """Test HardwareError exception."""
    error = HardwareError("GPIO initialization failed")

    assert isinstance(error, RaspiRuxpinError)
    assert isinstance(error, Exception)
    assert str(error) == "GPIO initialization failed"


def test_gpio_error():
    """Test GPIOError exception."""
    error = GPIOError("GPIO pin setup failed")

    assert isinstance(error, HardwareError)
    assert isinstance(error, RaspiRuxpinError)
    assert str(error) == "GPIO pin setup failed"


def test_servo_error():
    """Test ServoError exception."""
    error = ServoError("Servo movement failed")

    assert isinstance(error, HardwareError)
    assert str(error) == "Servo movement failed"


def test_audio_error():
    """Test AudioError exception."""
    error = AudioError("Audio playback failed")

    assert isinstance(error, HardwareError)
    assert str(error) == "Audio playback failed"


def test_configuration_error():
    """Test ConfigurationError exception."""
    error = ConfigurationError("Invalid configuration")

    assert isinstance(error, RaspiRuxpinError)
    assert str(error) == "Invalid configuration"


def test_validation_error():
    """Test ValidationError exception."""
    error = ValidationError("Validation failed")

    assert isinstance(error, RaspiRuxpinError)
    assert str(error) == "Validation failed"


def test_exceptions_are_catchable():
    """Test custom exceptions can be caught."""
    with pytest.raises(HardwareError):
        raise HardwareError("Test hardware error")

    with pytest.raises(GPIOError):
        raise GPIOError("Test GPIO error")

    with pytest.raises(ConfigurationError):
        raise ConfigurationError("Test config error")


def test_state_enum_all_members():
    """Test State enum has all expected members."""
    members = [member.value for member in State]

    assert "open" in members
    assert "closed" in members
    assert "unknown" in members
    assert len(members) == 3


def test_direction_enum_all_members():
    """Test Direction enum has all expected members."""
    members = [member.value for member in Direction]

    assert "opening" in members
    assert "closing" in members
    assert "brake" in members
    assert len(members) == 3
