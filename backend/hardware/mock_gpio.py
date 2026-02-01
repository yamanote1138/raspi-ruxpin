"""Simple Mock GPIO implementation for development without hardware.

This provides a minimal GPIO interface that works reliably on Mac/Linux
without requiring actual GPIO hardware.
"""

import logging

logger = logging.getLogger(__name__)

# GPIO modes
BCM = 11
BOARD = 10

# Pin directions
OUT = 0
IN = 1

# Pin states
HIGH = 1
LOW = 0

# Pull up/down
PUD_UP = 21
PUD_DOWN = 22

# Global state
_mode = None
_warnings = True


class MockPWM:
    """Mock PWM implementation."""

    def __init__(self, channel: int, frequency: float):
        self.channel = channel
        self.frequency = frequency
        self.duty_cycle = 0
        self.running = False
        logger.debug(f"Mock PWM created: channel={channel}, frequency={frequency}Hz")

    def start(self, duty_cycle: float) -> None:
        """Start PWM with given duty cycle."""
        self.duty_cycle = duty_cycle
        self.running = True
        logger.debug(f"Mock PWM started: channel={self.channel}, duty={duty_cycle}%")

    def stop(self) -> None:
        """Stop PWM."""
        self.running = False
        logger.debug(f"Mock PWM stopped: channel={self.channel}")

    def ChangeDutyCycle(self, duty_cycle: float) -> None:
        """Change PWM duty cycle."""
        self.duty_cycle = duty_cycle
        logger.debug(f"Mock PWM duty cycle changed: channel={self.channel}, duty={duty_cycle}%")

    def ChangeFrequency(self, frequency: float) -> None:
        """Change PWM frequency."""
        self.frequency = frequency
        logger.debug(f"Mock PWM frequency changed: channel={self.channel}, freq={frequency}Hz")


def setmode(mode: int) -> None:
    """Set GPIO pin numbering mode."""
    global _mode
    _mode = mode
    mode_name = "BCM" if mode == BCM else "BOARD"
    logger.debug(f"Mock GPIO mode set: {mode_name}")


def setwarnings(enabled: bool) -> None:
    """Enable or disable warnings."""
    global _warnings
    _warnings = enabled
    logger.debug(f"Mock GPIO warnings: {'enabled' if enabled else 'disabled'}")


def setup(channel: int, direction: int, pull_up_down: int = -1) -> None:
    """Set up a GPIO channel."""
    dir_name = "OUT" if direction == OUT else "IN"
    pud_name = ""
    if pull_up_down == PUD_UP:
        pud_name = ", pull_up"
    elif pull_up_down == PUD_DOWN:
        pud_name = ", pull_down"
    logger.debug(f"Mock GPIO setup: channel={channel}, direction={dir_name}{pud_name}")


def output(channel: int, value: int) -> None:
    """Set output value on a GPIO channel."""
    value_name = "HIGH" if value == HIGH else "LOW"
    logger.debug(f"Mock GPIO output: channel={channel}, value={value_name}")


def input(channel: int) -> int:
    """Read input value from a GPIO channel."""
    logger.debug(f"Mock GPIO input: channel={channel}")
    return LOW


def cleanup(channel: int | list[int] | None = None) -> None:
    """Clean up GPIO channels."""
    if channel is None:
        logger.debug("Mock GPIO cleanup: all channels")
    elif isinstance(channel, list):
        logger.debug(f"Mock GPIO cleanup: channels={channel}")
    else:
        logger.debug(f"Mock GPIO cleanup: channel={channel}")


def PWM(channel: int, frequency: float) -> MockPWM:
    """Create a PWM instance."""
    return MockPWM(channel, frequency)
