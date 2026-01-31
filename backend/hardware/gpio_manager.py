"""Centralized GPIO management for Raspi Ruxpin.

This module provides a protocol-based GPIO manager that handles initialization,
pin setup, and cleanup. It supports both RPi.GPIO (production) and Mock.GPIO
(development) through a unified interface.
"""

import logging
import platform
from typing import Any, Literal, Protocol

from backend.core.exceptions import GPIOError

logger = logging.getLogger(__name__)


class PWM(Protocol):
    """Protocol for PWM objects."""

    def start(self, duty_cycle: float) -> None:
        """Start PWM with given duty cycle."""
        ...

    def stop(self) -> None:
        """Stop PWM."""
        ...

    def ChangeDutyCycle(self, duty_cycle: float) -> None:
        """Change PWM duty cycle."""
        ...

    def ChangeFrequency(self, frequency: float) -> None:
        """Change PWM frequency."""
        ...


class GPIOModule(Protocol):
    """Protocol for GPIO module interface."""

    BCM: int
    OUT: int
    IN: int
    HIGH: int
    LOW: int
    PUD_UP: int
    PUD_DOWN: int

    def setmode(self, mode: int) -> None:
        """Set GPIO pin numbering mode."""
        ...

    def setup(self, channel: int, direction: int, pull_up_down: int = ...) -> None:
        """Set up a GPIO channel."""
        ...

    def output(self, channel: int, value: int) -> None:
        """Set output value on a GPIO channel."""
        ...

    def input(self, channel: int) -> int:
        """Read input value from a GPIO channel."""
        ...

    def cleanup(self, channel: int | list[int] | None = None) -> None:
        """Clean up GPIO channels."""
        ...

    def PWM(self, channel: int, frequency: float) -> PWM:
        """Create a PWM instance."""
        ...

    def setwarnings(self, enabled: bool) -> None:
        """Enable or disable warnings."""
        ...


class GPIOManager:
    """Centralized GPIO manager with lifecycle management.

    This class provides a single point of control for all GPIO operations,
    ensuring proper initialization and cleanup. It automatically detects
    the platform and uses appropriate GPIO library (RPi.GPIO or Mock.GPIO).

    Attributes:
        gpio: The GPIO module (RPi.GPIO or Mock.GPIO)
        is_initialized: Whether GPIO has been initialized
        active_pins: Set of pins that have been set up
        active_pwms: Dictionary of active PWM instances
    """

    def __init__(self, use_mock: bool | None = None) -> None:
        """Initialize GPIO manager.

        Args:
            use_mock: Force use of Mock.GPIO. If None, auto-detect based on platform.
        """
        self.gpio: GPIOModule
        self.is_initialized = False
        self.active_pins: set[int] = set()
        self.active_pwms: dict[int, PWM] = {}

        # Determine which GPIO module to use
        if use_mock is None:
            use_mock = platform.system() == "Darwin"

        try:
            if use_mock:
                logger.info("Using Mock.GPIO for development")
                import Mock.GPIO as GPIO  # type: ignore

                self.gpio = GPIO  # type: ignore
            else:
                logger.info("Using RPi.GPIO for production")
                import RPi.GPIO as GPIO  # type: ignore

                self.gpio = GPIO  # type: ignore
        except ImportError as e:
            raise GPIOError(f"Failed to import GPIO module: {e}") from e

    def initialize(self) -> None:
        """Initialize GPIO with BCM pin numbering.

        This should be called once at application startup.
        """
        if self.is_initialized:
            logger.warning("GPIO already initialized")
            return

        try:
            self.gpio.setwarnings(False)
            self.gpio.setmode(self.gpio.BCM)
            self.is_initialized = True
            logger.info("GPIO initialized with BCM mode")
        except Exception as e:
            raise GPIOError(f"Failed to initialize GPIO: {e}") from e

    def setup_pin(
        self,
        pin: int,
        direction: Literal["OUT", "IN"],
        pull_up_down: Literal["UP", "DOWN"] | None = None,
    ) -> None:
        """Set up a GPIO pin.

        Args:
            pin: GPIO pin number (BCM numbering)
            direction: Pin direction (OUT or IN)
            pull_up_down: Optional pull-up/down resistor configuration

        Raises:
            GPIOError: If GPIO is not initialized or setup fails
        """
        if not self.is_initialized:
            raise GPIOError("GPIO not initialized. Call initialize() first.")

        try:
            gpio_direction = self.gpio.OUT if direction == "OUT" else self.gpio.IN

            if pull_up_down:
                pud = self.gpio.PUD_UP if pull_up_down == "UP" else self.gpio.PUD_DOWN
                self.gpio.setup(pin, gpio_direction, pull_up_down=pud)
            else:
                self.gpio.setup(pin, gpio_direction)

            self.active_pins.add(pin)
            logger.debug(f"Pin {pin} set up as {direction}")
        except Exception as e:
            raise GPIOError(f"Failed to setup pin {pin}: {e}") from e

    def output(self, pin: int, value: bool) -> None:
        """Set output value on a GPIO pin.

        Args:
            pin: GPIO pin number (BCM numbering)
            value: Output value (True=HIGH, False=LOW)

        Raises:
            GPIOError: If pin is not set up or output fails
        """
        if pin not in self.active_pins:
            raise GPIOError(f"Pin {pin} not set up. Call setup_pin() first.")

        try:
            gpio_value = self.gpio.HIGH if value else self.gpio.LOW
            self.gpio.output(pin, gpio_value)
            logger.debug(f"Pin {pin} set to {'HIGH' if value else 'LOW'}")
        except Exception as e:
            raise GPIOError(f"Failed to set output on pin {pin}: {e}") from e

    def create_pwm(self, pin: int, frequency: float) -> PWM:
        """Create a PWM instance for a pin.

        Args:
            pin: GPIO pin number (BCM numbering)
            frequency: PWM frequency in Hz

        Returns:
            PWM instance

        Raises:
            GPIOError: If pin is not set up or PWM creation fails
        """
        if pin not in self.active_pins:
            raise GPIOError(f"Pin {pin} not set up. Call setup_pin() first.")

        try:
            pwm = self.gpio.PWM(pin, frequency)
            self.active_pwms[pin] = pwm
            logger.debug(f"PWM created for pin {pin} at {frequency}Hz")
            return pwm
        except Exception as e:
            raise GPIOError(f"Failed to create PWM on pin {pin}: {e}") from e

    def cleanup_pin(self, pin: int) -> None:
        """Clean up a specific GPIO pin.

        Args:
            pin: GPIO pin number (BCM numbering)
        """
        try:
            # Stop PWM if active
            if pin in self.active_pwms:
                self.active_pwms[pin].stop()
                del self.active_pwms[pin]
                logger.debug(f"Stopped PWM on pin {pin}")

            # Cleanup the pin
            self.gpio.cleanup(pin)
            self.active_pins.discard(pin)
            logger.debug(f"Cleaned up pin {pin}")
        except Exception as e:
            logger.error(f"Error cleaning up pin {pin}: {e}")

    def cleanup_all(self) -> None:
        """Clean up all GPIO pins and PWM instances."""
        try:
            # Stop all PWMs
            for pin, pwm in list(self.active_pwms.items()):
                try:
                    pwm.stop()
                    logger.debug(f"Stopped PWM on pin {pin}")
                except Exception as e:
                    logger.error(f"Error stopping PWM on pin {pin}: {e}")

            self.active_pwms.clear()

            # Cleanup all pins
            if self.active_pins:
                pins_to_clean = list(self.active_pins)
                self.gpio.cleanup(pins_to_clean)
                logger.info(f"Cleaned up {len(pins_to_clean)} GPIO pins")

            self.active_pins.clear()
            self.is_initialized = False
        except Exception as e:
            logger.error(f"Error during GPIO cleanup: {e}")

    def __enter__(self) -> "GPIOManager":
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.cleanup_all()
