"""Custom exceptions for the Raspi Ruxpin system."""


class RaspiRuxpinError(Exception):
    """Base exception for all Raspi Ruxpin errors."""

    pass


class HardwareError(RaspiRuxpinError):
    """Raised when hardware operations fail."""

    pass


class AudioError(HardwareError):
    """Raised when audio operations fail."""

    pass


class SerialError(HardwareError):
    """Raised when serial/Arduino communication fails."""

    pass


class ConfigurationError(RaspiRuxpinError):
    """Raised when configuration is invalid."""

    pass


