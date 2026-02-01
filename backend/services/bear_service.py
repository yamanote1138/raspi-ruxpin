"""Bear orchestration service with async task management.

This module coordinates servo control, audio playback, and mouth synchronization
for the animatronic bear. It replaces threading with asyncio tasks.
"""

import asyncio
import json
import logging
import random
from pathlib import Path
from typing import Any

from backend.config import AppSettings
from backend.core.enums import State
from backend.core.exceptions import RaspiRuxpinError
from backend.hardware.audio_player import AudioPlayer
from backend.hardware.gpio_manager import GPIOManager
from backend.hardware.models import PinSet
from backend.hardware.servo import Servo

logger = logging.getLogger(__name__)


class BearService:
    """Orchestrates the animatronic bear behavior.

    This service manages:
    - Servo control for eyes and mouth
    - Audio playback with mouth synchronization
    - Random eye blinking
    - Phrase management

    Attributes:
        settings: Application settings
        gpio_manager: GPIO manager instance
        audio_player: Audio player instance
        eyes: Eyes servo controller
        mouth: Mouth servo controller
        phrases: Dictionary of available phrases
        is_busy: Whether bear is currently performing an action
        _talk_task: Background task for mouth sync
        _blink_task: Background task for eye blinks
    """

    def __init__(
        self,
        settings: AppSettings,
        gpio_manager: GPIOManager,
        audio_player: AudioPlayer,
    ) -> None:
        """Initialize bear service.

        Args:
            settings: Application settings
            gpio_manager: Initialized GPIO manager
            audio_player: Initialized audio player
        """
        self.settings = settings
        self.gpio_manager = gpio_manager
        self.audio_player = audio_player

        # Initialize servos
        eyes_pins = PinSet(
            pwm=settings.hardware.eyes_pwm,
            dir=settings.hardware.eyes_dir,
            cdir=settings.hardware.eyes_cdir,
        )
        self.eyes = Servo(
            name="eyes",
            pins=eyes_pins,
            speed=settings.hardware.eyes_speed,
            default_duration=settings.hardware.eyes_duration,
            gpio_manager=gpio_manager,
        )

        mouth_pins = PinSet(
            pwm=settings.hardware.mouth_pwm,
            dir=settings.hardware.mouth_dir,
            cdir=settings.hardware.mouth_cdir,
        )
        self.mouth = Servo(
            name="mouth",
            pins=mouth_pins,
            speed=settings.hardware.mouth_speed,
            default_duration=settings.hardware.mouth_duration,
            gpio_manager=gpio_manager,
        )

        # State
        self.phrases: dict[str, str] = {}
        self.is_busy = False
        self.blink_enabled = False  # Eye blinking disabled by default
        self._talk_task: asyncio.Task[None] | None = None
        self._blink_task: asyncio.Task[None] | None = None
        self._shutdown = False

        logger.info("BearService initialized")

    async def start(self) -> None:
        """Start the bear service.

        Initializes hardware, opens eyes, and starts background tasks.

        Raises:
            RaspiRuxpinError: If startup fails
        """
        try:
            # Initialize servos
            await self.eyes.initialize()
            await self.mouth.initialize()

            # Open eyes on startup
            await self.eyes.open()

            # Load phrases
            await self._load_phrases()

            # Start background tasks
            self._talk_task = asyncio.create_task(self._talk_monitor())
            self._blink_task = asyncio.create_task(self._blink_monitor())

            logger.info("BearService started successfully")
        except Exception as e:
            raise RaspiRuxpinError(f"Failed to start BearService: {e}") from e

    async def stop(self) -> None:
        """Stop the bear service.

        Cancels background tasks, closes servos, and cleans up hardware.
        """
        logger.info("Stopping BearService...")
        self._shutdown = True

        # Cancel background tasks
        if self._talk_task and not self._talk_task.done():
            self._talk_task.cancel()
            try:
                await self._talk_task
            except asyncio.CancelledError:
                pass

        if self._blink_task and not self._blink_task.done():
            self._blink_task.cancel()
            try:
                await self._blink_task
            except asyncio.CancelledError:
                pass

        # Close servos
        try:
            await self.eyes.close()
            await self.mouth.close()
        except Exception as e:
            logger.error(f"Error closing servos: {e}")

        # Cleanup
        await self.eyes.cleanup()
        await self.mouth.cleanup()

        logger.info("BearService stopped")

    async def _load_phrases(self) -> None:
        """Load phrases from JSON file."""
        phrases_file = self.settings.phrases_file

        if not phrases_file.exists():
            logger.warning(f"Phrases file not found: {phrases_file}")
            return

        try:
            with open(phrases_file, "r", encoding="utf-8") as f:
                self.phrases = json.load(f)

            logger.info(f"Loaded {len(self.phrases)} phrases")
        except Exception as e:
            logger.error(f"Failed to load phrases: {e}")

    async def _talk_monitor(self) -> None:
        """Monitor audio amplitude and sync mouth movement proportionally.

        This task runs continuously, checking audio amplitude and setting
        mouth position proportionally to the sound level for natural animation.
        """
        logger.info("Talk monitor started")

        try:
            while not self._shutdown:
                if self.is_busy:
                    # Get proportional mouth position based on amplitude
                    target_position = self.audio_player.get_mouth_position()

                    # Update mouth position (slower for 40+ year old servo)
                    # 0.15s allows old servo to respond while maintaining speech sync
                    await self.mouth.set_position_percent(target_position, duration=0.15)

                # 25Hz update rate (slower for smoother animation)
                await asyncio.sleep(0.04)
        except asyncio.CancelledError:
            logger.info("Talk monitor cancelled")
            raise
        except Exception as e:
            logger.error(f"Talk monitor error: {e}")

    async def _blink_monitor(self) -> None:
        """Randomly blink eyes when not busy.

        This task runs continuously, blinking the eyes at random intervals
        when the bear is not performing other actions and blinking is enabled.
        """
        logger.info("Blink monitor started")

        try:
            while not self._shutdown:
                if self.blink_enabled and not self.is_busy and self.eyes.state == State.OPEN:
                    # Random delay between blinks (3-7 seconds)
                    delay = random.uniform(3.0, 7.0)
                    logger.debug(f"Blink scheduled in {delay:.1f}s")
                    await asyncio.sleep(delay)

                    # Check conditions again after delay
                    if self.blink_enabled and not self.is_busy and self.eyes.state == State.OPEN:
                        logger.debug("Executing blink")
                        # Natural blink: slow servos need more time (40+ year old motors)
                        await self.eyes.close(0.6)    # Close slowly (old servo)
                        await asyncio.sleep(0.2)      # Stay closed briefly
                        await self.eyes.open(0.6)     # Open slowly (old servo)
                        logger.debug("Blink completed")
                    else:
                        logger.debug(f"Blink cancelled: enabled={self.blink_enabled}, busy={self.is_busy}, eyes={self.eyes.state}")
                else:
                    await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            logger.info("Blink monitor cancelled")
            raise
        except Exception as e:
            logger.error(f"Blink monitor error: {e}")

    async def update_positions(
        self,
        eyes_position: State | None = None,
        mouth_position: State | None = None,
    ) -> dict[str, Any]:
        """Update servo positions manually.

        Args:
            eyes_position: Target eyes position (OPEN or CLOSED)
            mouth_position: Target mouth position (OPEN or CLOSED)

        Returns:
            Current bear state

        Raises:
            RaspiRuxpinError: If update fails
        """
        if self.is_busy:
            raise RaspiRuxpinError("Bear is busy")

        try:
            # Use slower duration for manual movements to show smooth animation
            # Longer duration for old servos (40+ years old) to complete movement
            eyes_manual_duration = 0.8   # Eyes are slower
            mouth_manual_duration = 0.5  # Mouth can be a bit faster

            if eyes_position is not None:
                await self.eyes.set_position(eyes_position, eyes_manual_duration)

            if mouth_position is not None:
                await self.mouth.set_position(mouth_position, mouth_manual_duration)

            logger.info(f"Positions updated: eyes={eyes_position}, mouth={mouth_position}")

            return self.get_state()
        except Exception as e:
            raise RaspiRuxpinError(f"Failed to update positions: {e}") from e

    async def speak(self, text: str) -> None:
        """Synthesize and speak text with mouth sync.

        Args:
            text: Text to speak

        Raises:
            RaspiRuxpinError: If already busy or speech fails
        """
        if self.is_busy:
            raise RaspiRuxpinError("Bear is busy")

        try:
            self.is_busy = True
            logger.info(f"Speaking: {text}")

            # Ensure eyes are open
            if self.eyes.state != State.OPEN:
                await self.eyes.open()

            # Speak with mouth sync
            await self.audio_player.speak(text)

            # Close mouth after speaking
            if self.mouth.state != State.CLOSED:
                await self.mouth.close()

        except Exception as e:
            raise RaspiRuxpinError(f"Speech failed: {e}") from e
        finally:
            self.is_busy = False

    async def play_audio(self, sound_name: str) -> None:
        """Play audio file with mouth sync.

        Args:
            sound_name: Name of sound file (without .wav extension)

        Raises:
            RaspiRuxpinError: If already busy or playback fails
        """
        if self.is_busy:
            raise RaspiRuxpinError("Bear is busy")

        try:
            self.is_busy = True
            logger.info(f"Playing audio: {sound_name}")

            # Ensure eyes are open
            if self.eyes.state != State.OPEN:
                await self.eyes.open()

            # Play audio with mouth sync
            await self.audio_player.play_sound(sound_name)

            # Close mouth after playing
            if self.mouth.state != State.CLOSED:
                await self.mouth.close()

        except Exception as e:
            raise RaspiRuxpinError(f"Audio playback failed: {e}") from e
        finally:
            self.is_busy = False

    async def set_volume(self, level: int) -> None:
        """Set audio volume.

        Args:
            level: Volume level (0-100)

        Raises:
            RaspiRuxpinError: If volume setting fails
        """
        try:
            await self.audio_player.set_volume(level)
            logger.info(f"Volume set to {level}")
        except Exception as e:
            raise RaspiRuxpinError(f"Failed to set volume: {e}") from e

    def set_blink_enabled(self, enabled: bool) -> None:
        """Enable or disable automatic eye blinking.

        Args:
            enabled: True to enable blinking, False to disable
        """
        self.blink_enabled = enabled
        logger.info(f"Eye blinking {'enabled' if enabled else 'disabled'}")

    def get_phrases(self) -> dict[str, str]:
        """Get available phrases.

        Returns:
            Dictionary of phrase key to description
        """
        return self.phrases.copy()

    def get_state(self) -> dict[str, Any]:
        """Get current bear state.

        Returns:
            Dictionary with current state information
        """
        return {
            "eyes": self.eyes.state.value,
            "mouth": self.mouth.state.value,
            "eyes_position": self.eyes.position_percent,
            "mouth_position": self.mouth.position_percent,
            "is_busy": self.is_busy,
            "volume": self.audio_player.volume,
            "blink_enabled": self.blink_enabled,
        }
