"""Tests for core domain models and enums."""

import pytest

from backend.core.enums import State
from backend.core.exceptions import (
    AudioError,
    ConfigurationError,
    HardwareError,
    RaspiRuxpinError,
    SerialError,
)


def test_state_enum_values() -> None:
    """Test State enum has expected values."""
    assert State.OPEN.value == "open"
    assert State.CLOSED.value == "closed"
    assert State.UNKNOWN.value == "unknown"


def test_state_enum_comparison() -> None:
    """Test State enum comparison."""
    assert State.OPEN is State.OPEN
    open_state, closed_state = State.OPEN, State.CLOSED
    assert open_state != closed_state
    assert State.OPEN.value == "open"


def test_state_enum_all_members() -> None:
    """Test State enum has all expected members."""
    members = [member.value for member in State]
    assert "open" in members
    assert "closed" in members
    assert "unknown" in members
    assert len(members) == 3


def test_raspi_ruxpin_error() -> None:
    """Test base RaspiRuxpinError exception."""
    error = RaspiRuxpinError("Base error")
    assert isinstance(error, Exception)
    assert str(error) == "Base error"


def test_hardware_error() -> None:
    """Test HardwareError exception."""
    error = HardwareError("Hardware failure")
    assert isinstance(error, RaspiRuxpinError)
    assert isinstance(error, Exception)
    assert str(error) == "Hardware failure"


def test_audio_error() -> None:
    """Test AudioError exception."""
    error = AudioError("Audio playback failed")
    assert isinstance(error, HardwareError)
    assert str(error) == "Audio playback failed"


def test_serial_error() -> None:
    """Test SerialError exception."""
    error = SerialError("Serial connection lost")
    assert isinstance(error, HardwareError)
    assert str(error) == "Serial connection lost"


def test_configuration_error() -> None:
    """Test ConfigurationError exception."""
    error = ConfigurationError("Invalid configuration")
    assert isinstance(error, RaspiRuxpinError)
    assert str(error) == "Invalid configuration"


def test_exceptions_are_catchable() -> None:
    """Test custom exceptions can be caught."""
    with pytest.raises(HardwareError):
        raise HardwareError("Test hardware error")

    with pytest.raises(AudioError):
        raise AudioError("Test audio error")

    with pytest.raises(SerialError):
        raise SerialError("Test serial error")

    with pytest.raises(ConfigurationError):
        raise ConfigurationError("Test config error")
