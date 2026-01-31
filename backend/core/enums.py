"""Core enumerations for the Raspi Ruxpin system."""

from enum import Enum, auto


class Direction(str, Enum):
    """Servo motor direction states."""

    OPENING = "opening"
    CLOSING = "closing"
    BRAKE = "brake"


class State(str, Enum):
    """Servo position states."""

    OPEN = "open"
    CLOSED = "closed"
    UNKNOWN = "unknown"


class Mode(str, Enum):
    """UI mode states."""

    PUPPET = "puppet"
    SPEAK = "speak"
    CONFIG = "config"
