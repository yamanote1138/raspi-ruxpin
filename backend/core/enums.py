"""Core enumerations for the Raspi Ruxpin system."""

from enum import StrEnum


class State(StrEnum):
    """Servo position states."""

    OPEN = "open"
    CLOSED = "closed"
    UNKNOWN = "unknown"


class MouthPosition(StrEnum):
    """7-position mouth model for animatronic jaw control.

    Based on the phoneme groupings from the original Teddy Ruxpin
    animation system. Maps to calibrated servo angles.
    """

    C = "C"  # Closed (silence)
    T = "T"  # Teeth together (t, d, s, z, n, l)
    S = "S"  # Slightly open (th, sh, ch, j)
    N = "N"  # Neutral/mid (schwa, short vowels)
    M = "M"  # Medium open (eh, ae)
    L = "L"  # Large open (ah, aw)
    W = "W"  # Wide open (aa, ow)


class SyncMode(StrEnum):
    """Audio-to-mouth synchronization mode."""

    AMPLITUDE = "amplitude"  # Pi pre-analyzes WAV amplitude, sends timed commands over serial
    PHONEME = "phoneme"  # Pi pre-analyzes phonemes (Whisper+phonemizer), sends timed commands
    REALTIME = "realtime"  # Arduino reads audio ADC, drives servos autonomously


class ServoType(StrEnum):
    """Servo hardware type for Arduino configuration."""

    HBRIDGE = "hbridge"  # 5-wire H-bridge (original Teddy Ruxpin servos)
    STANDARD = "standard"  # 3-wire standard hobby servos
