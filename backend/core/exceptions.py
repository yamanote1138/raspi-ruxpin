"""Custom exceptions for the Raspi Ruxpin system."""


class RaspiRuxpinError(Exception):
    """Base exception for all Raspi Ruxpin errors."""

    pass


class HardwareError(RaspiRuxpinError):
    """Raised when hardware operations fail."""

    pass


class GPIOError(HardwareError):
    """Raised when GPIO operations fail."""

    pass


class ServoError(HardwareError):
    """Raised when servo operations fail."""

    pass


class AudioError(HardwareError):
    """Raised when audio operations fail."""

    pass


class ConfigurationError(RaspiRuxpinError):
    """Raised when configuration is invalid."""

    pass


class ValidationError(RaspiRuxpinError):
    """Raised when validation fails."""

    pass
