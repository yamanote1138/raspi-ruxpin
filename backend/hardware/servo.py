"""Async servo motor control for Raspi Ruxpin.

This module provides async servo control with proper lifecycle management,
dependency injection, and type safety.
"""

import asyncio
import logging
from typing import Literal

from backend.core.enums import Direction, State
from backend.core.exceptions import ServoError
from backend.hardware.gpio_manager import GPIOManager
from backend.hardware.models import PinSet

logger = logging.getLogger(__name__)


class Servo:
    """Async servo motor controller.

    This class manages a single servo motor using PWM and direction control pins.
    It supports async operations to avoid blocking the event loop.

    Attributes:
        name: Human-readable name for this servo (e.g., "eyes", "mouth")
        pins: GPIO pin configuration
        speed: PWM frequency in Hz
        default_duration: Default movement duration in seconds
        gpio_manager: GPIO manager for hardware control
        state: Current servo state (OPEN, CLOSED, UNKNOWN)
        pwm: PWM instance for speed control
    """

    def __init__(
        self,
        name: str,
        pins: PinSet,
        speed: int,
        default_duration: float,
        gpio_manager: GPIOManager,
    ) -> None:
        """Initialize servo controller.

        Args:
            name: Servo name for logging
            pins: GPIO pin configuration
            speed: PWM frequency (1-1000 Hz)
            default_duration: Default movement duration (0-2.0 seconds)
            gpio_manager: Initialized GPIO manager

        Raises:
            ServoError: If parameters are invalid
        """
        if not (1 <= speed <= 1000):
            raise ServoError(f"Speed must be between 1 and 1000 Hz, got {speed}")

        if not (0 < default_duration <= 2.0):
            raise ServoError(f"Duration must be between 0 and 2.0 seconds, got {default_duration}")

        self.name = name
        self.pins = pins
        self.speed = speed
        self.default_duration = default_duration
        self.gpio_manager = gpio_manager
        self.state = State.UNKNOWN
        self.position_percent = 0  # 0 = fully closed, 100 = fully open
        self.pwm = None
        self._lock = asyncio.Lock()

        logger.info(
            f"Servo '{name}' initialized: pins={pins.model_dump()}, "
            f"speed={speed}Hz, duration={default_duration}s"
        )

    async def initialize(self) -> None:
        """Initialize GPIO pins and PWM.

        This should be called once before using the servo.

        Raises:
            ServoError: If initialization fails
        """
        try:
            # Set up all pins as outputs
            self.gpio_manager.setup_pin(self.pins.pwm, "OUT")
            self.gpio_manager.setup_pin(self.pins.dir, "OUT")
            self.gpio_manager.setup_pin(self.pins.cdir, "OUT")

            # Create PWM instance
            self.pwm = self.gpio_manager.create_pwm(self.pins.pwm, self.speed)

            # Initialize in brake state
            await self._set_direction(Direction.BRAKE)

            logger.info(f"Servo '{self.name}' initialized successfully")
        except Exception as e:
            raise ServoError(f"Failed to initialize servo '{self.name}': {e}") from e

    async def _set_direction(self, direction: Direction) -> None:
        """Set servo direction.

        Args:
            direction: Direction to set (OPENING, CLOSING, BRAKE)
        """
        if direction == Direction.OPENING:
            self.gpio_manager.output(self.pins.dir, True)
            self.gpio_manager.output(self.pins.cdir, False)
        elif direction == Direction.CLOSING:
            self.gpio_manager.output(self.pins.dir, False)
            self.gpio_manager.output(self.pins.cdir, True)
        elif direction == Direction.BRAKE:
            self.gpio_manager.output(self.pins.dir, False)
            self.gpio_manager.output(self.pins.cdir, False)

        logger.debug(f"Servo '{self.name}' direction set to {direction.value}")

    async def _move(self, direction: Direction, duration: float) -> None:
        """Move servo in specified direction for given duration.

        Args:
            direction: Direction to move (OPENING or CLOSING)
            duration: Movement duration in seconds

        Raises:
            ServoError: If duration is invalid or PWM not initialized
        """
        if not self.pwm:
            raise ServoError(f"Servo '{self.name}' not initialized")

        if not (0 < duration <= 2.0):
            raise ServoError(f"Duration must be between 0 and 2.0 seconds, got {duration}")

        async with self._lock:
            try:
                # Set direction and start PWM
                await self._set_direction(direction)
                await asyncio.to_thread(self.pwm.start, 50)

                # Animate position during movement
                start_position = self.position_percent
                target_position = 100 if direction == Direction.OPENING else 0
                start_time = asyncio.get_event_loop().time()

                # Update position in small increments during movement
                update_interval = 0.05  # 20Hz updates
                while True:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed >= duration:
                        self.position_percent = target_position
                        break

                    # Linear interpolation of position
                    progress = elapsed / duration
                    self.position_percent = int(start_position + (target_position - start_position) * progress)

                    await asyncio.sleep(update_interval)

                # Stop and brake
                await asyncio.to_thread(self.pwm.stop)
                await self._set_direction(Direction.BRAKE)

                logger.debug(
                    f"Servo '{self.name}' moved {direction.value} for {duration}s to {self.position_percent}%"
                )
            except Exception as e:
                # Ensure we brake on error
                if self.pwm:
                    try:
                        await asyncio.to_thread(self.pwm.stop)
                        await self._set_direction(Direction.BRAKE)
                    except Exception:
                        pass
                raise ServoError(f"Servo '{self.name}' movement failed: {e}") from e

    async def open(self, duration: float | None = None) -> None:
        """Open the servo (move to open position).

        Args:
            duration: Optional override for movement duration

        Raises:
            ServoError: If movement fails
        """
        duration = duration or self.default_duration
        await self._move(Direction.OPENING, duration)
        self.state = State.OPEN
        self.position_percent = 100
        logger.info(f"Servo '{self.name}' opened to 100%")

    async def close(self, duration: float | None = None) -> None:
        """Close the servo (move to closed position).

        Args:
            duration: Optional override for movement duration

        Raises:
            ServoError: If movement fails
        """
        duration = duration or self.default_duration
        await self._move(Direction.CLOSING, duration)
        self.state = State.CLOSED
        self.position_percent = 0
        logger.info(f"Servo '{self.name}' closed to 0%")

    async def set_position(self, position: State, duration: float | None = None) -> None:
        """Set servo to specific position.

        Args:
            position: Target position (OPEN or CLOSED)
            duration: Optional override for movement duration

        Raises:
            ServoError: If position is invalid or movement fails
        """
        if position == State.OPEN:
            await self.open(duration)
        elif position == State.CLOSED:
            await self.close(duration)
        else:
            raise ServoError(f"Invalid position: {position}")

    async def set_position_percent(self, target_percent: int, duration: float = 0.05) -> None:
        """Set servo to specific percentage position (0-100).

        Args:
            target_percent: Target position as percentage (0=closed, 100=open)
            duration: Movement duration in seconds (default 0.05 for quick response)

        Raises:
            ServoError: If position is invalid or movement fails
        """
        if not (0 <= target_percent <= 100):
            raise ServoError(f"Position must be between 0 and 100, got {target_percent}")

        if not self.pwm:
            raise ServoError(f"Servo '{self.name}' not initialized")

        current = self.position_percent

        # Skip if already close to target (within 8% to reduce jitter)
        if abs(current - target_percent) < 8:
            return

        # Determine direction
        if target_percent > current:
            direction = Direction.OPENING
            move_duration = duration * (target_percent - current) / 100
        else:
            direction = Direction.CLOSING
            move_duration = duration * (current - target_percent) / 100

        # Move to target position
        await self._move_to_percent(direction, target_percent, move_duration)

    async def _move_to_percent(self, direction: Direction, target_percent: int, duration: float) -> None:
        """Move servo to specific percentage.

        Args:
            direction: Direction to move
            target_percent: Target position percentage
            duration: Movement duration
        """
        if duration < 0.01:
            duration = 0.01  # Minimum duration

        async with self._lock:
            try:
                # Set direction and start PWM
                await self._set_direction(direction)
                await asyncio.to_thread(self.pwm.start, 50)

                # Animate position during movement
                start_position = self.position_percent
                start_time = asyncio.get_event_loop().time()

                # Update position in small increments
                update_interval = 0.05  # 20Hz updates for smooth animation
                while True:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed >= duration:
                        self.position_percent = target_percent
                        break

                    # Linear interpolation
                    progress = elapsed / duration
                    self.position_percent = int(start_position + (target_percent - start_position) * progress)

                    await asyncio.sleep(update_interval)

                # Stop and brake
                await asyncio.to_thread(self.pwm.stop)
                await self._set_direction(Direction.BRAKE)

                # Update state
                if target_percent == 0:
                    self.state = State.CLOSED
                elif target_percent == 100:
                    self.state = State.OPEN
                else:
                    self.state = State.UNKNOWN

            except Exception as e:
                # Ensure we brake on error
                if self.pwm:
                    try:
                        await asyncio.to_thread(self.pwm.stop)
                        await self._set_direction(Direction.BRAKE)
                    except Exception:
                        pass
                raise ServoError(f"Servo '{self.name}' movement failed: {e}") from e

    async def cleanup(self) -> None:
        """Clean up servo resources.

        Stops PWM and sets servo to brake state.
        """
        try:
            if self.pwm:
                await asyncio.to_thread(self.pwm.stop)
                await self._set_direction(Direction.BRAKE)

            logger.info(f"Servo '{self.name}' cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up servo '{self.name}': {e}")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Servo(name={self.name!r}, state={self.state.value}, "
            f"position={self.position_percent}%, "
            f"speed={self.speed}Hz, duration={self.default_duration}s)"
        )
