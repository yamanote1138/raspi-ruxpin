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


def test_state_enum_values():
    """Test State enum has expected values."""
    assert State.OPEN == "open"
    assert State.CLOSED == "closed"
    assert State.UNKNOWN == "unknown"


def test_state_enum_comparison():
    """Test State enum comparison."""
    assert State.OPEN == State.OPEN
    assert State.OPEN != State.CLOSED
    assert State.OPEN.value == "open"


def test_state_enum_all_members():
    """Test State enum has all expected members."""
    members = [member.value for member in State]
    assert "open" in members
    assert "closed" in members
    assert "unknown" in members
    assert len(members) == 3


def test_raspi_ruxpin_error():
    """Test base RaspiRuxpinError exception."""
    error = RaspiRuxpinError("Base error")
    assert isinstance(error, Exception)
    assert str(error) == "Base error"


def test_hardware_error():
    """Test HardwareError exception."""
    error = HardwareError("Hardware failure")
    assert isinstance(error, RaspiRuxpinError)
    assert isinstance(error, Exception)
    assert str(error) == "Hardware failure"


def test_audio_error():
    """Test AudioError exception."""
    error = AudioError("Audio playback failed")
    assert isinstance(error, HardwareError)
    assert str(error) == "Audio playback failed"


def test_serial_error():
    """Test SerialError exception."""
    error = SerialError("Serial connection lost")
    assert isinstance(error, HardwareError)
    assert str(error) == "Serial connection lost"


def test_configuration_error():
    """Test ConfigurationError exception."""
    error = ConfigurationError("Invalid configuration")
    assert isinstance(error, RaspiRuxpinError)
    assert str(error) == "Invalid configuration"


def test_exceptions_are_catchable():
    """Test custom exceptions can be caught."""
    with pytest.raises(HardwareError):
        raise HardwareError("Test hardware error")

    with pytest.raises(AudioError):
        raise AudioError("Test audio error")

    with pytest.raises(SerialError):
        raise SerialError("Test serial error")

    with pytest.raises(ConfigurationError):
        raise ConfigurationError("Test config error")
