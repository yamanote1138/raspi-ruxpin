"""Bear orchestration service with async task management.

This module coordinates Arduino motor control, audio playback, and mouth
synchronization for the animatronic bear. In amplitude mode the Arduino
drives mouth movement autonomously from its ADC input. In phoneme mode
the Pi sends pre-computed timing commands over serial.
"""

import asyncio
import logging
import random
import time
from pathlib import Path
from typing import Any

from backend.config import AppSettings
from backend.core.enums import MouthPosition, State, SyncMode
from backend.core.exceptions import RaspiRuxpinError
from backend.hardware.arduino import ArduinoController
from backend.hardware.audio_player import AudioPlayer
from backend.hardware.timing_store import TimingStore

logger = logging.getLogger(__name__)


class BearService:
    """Orchestrates the animatronic bear behavior.

    This service manages:
    - Arduino communication for servo control (eyes and mouth)
    - Audio playback with mouth synchronization
    - Random eye blinking
    - Phrase management
    - Two sync modes: amplitude (Arduino-driven) and phoneme (Pi-driven)

    Attributes:
        settings: Application settings
        arduino: Arduino serial controller
        audio_player: Audio player instance
        timing_store: Timing data cache
        phrases: Dictionary of available phrases
        is_busy: Whether bear is currently performing an action
        sync_mode: Current synchronization mode
        mouth_position: Current mouth position code
    """

    def __init__(
        self,
        settings: AppSettings,
        arduino: ArduinoController,
        audio_player: AudioPlayer,
        timing_store: TimingStore,
    ) -> None:
        self.settings = settings
        self.arduino = arduino
        self.audio_player = audio_player
        self.timing_store = timing_store

        # State
        self.phrases: dict[str, str] = {}
        self.is_busy = False
        self.blink_enabled = False
        self.character = "teddy"
        self.sync_mode: SyncMode = settings.sync.mode
        self.mouth_position: MouthPosition = MouthPosition.C
        self.eyes_open = True
        self.status_text = ""
        self._talk_task: asyncio.Task[None] | None = None
        self._blink_task: asyncio.Task[None] | None = None
        self._timing_task: asyncio.Task[None] | None = None
        self._shutdown = False

        logger.info("BearService initialized")

    async def start(self) -> None:
        """Start the bear service.

        Connects to Arduino, opens eyes, and starts background tasks.

        Raises:
            RaspiRuxpinError: If startup fails
        """
        try:
            # Connect to Arduino
            from backend.hardware.calibration import get_default_calibration, load_calibration

            cal_path = self.settings.sync.calibration_file
            if not cal_path.is_absolute():
                cal_path = Path.cwd() / cal_path

            if cal_path.exists():
                calibration = load_calibration(cal_path)
            else:
                logger.warning(f"Calibration file not found: {cal_path}, using defaults")
                calibration = get_default_calibration()

            await self.arduino.connect(
                servo_type=self.settings.sync.servo_type,
                calibration=calibration,
                sync_mode=self.sync_mode,
            )

            # Register callback for realtime mouth position reports from Arduino
            self.arduino.set_mouth_position_callback(self._on_arduino_mouth_position)

            # Open eyes on startup
            await self.arduino.open_eyes()
            self.eyes_open = True

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

        Cancels background tasks, closes mouth, and disconnects Arduino.
        """
        logger.info("Stopping BearService...")
        self._shutdown = True

        # Cancel background tasks
        for task in [self._talk_task, self._blink_task, self._timing_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Close mouth and eyes
        try:
            await self.arduino.set_mouth_position(MouthPosition.C)
            await self.arduino.close_eyes()
        except Exception as e:
            logger.error(f"Error closing servos: {e}")

        # Disconnect
        await self.arduino.disconnect()
        logger.info("BearService stopped")

    async def _load_phrases(self) -> None:
        """Load phrases from WAV file metadata."""
        try:
            self.phrases = self.audio_player.list_sounds()
            logger.info(f"Loaded {len(self.phrases)} phrases from WAV metadata")
        except Exception as e:
            logger.error(f"Failed to load phrases: {e}")

    async def _talk_monitor(self) -> None:
        """Monitor audio state and clean up after playback ends.

        In REALTIME mode, the Arduino reports mouth positions via serial
        callback (_on_arduino_mouth_position). In AMPLITUDE/PHONEME modes,
        the timing schedule handles serial commands and self.mouth_position.
        The monitor watches for playback end to close the mouth.
        """
        logger.info("Talk monitor started")

        try:
            was_busy = False
            while not self._shutdown:
                if self.is_busy:
                    was_busy = True
                elif was_busy:
                    # Audio just ended — ensure mouth is closed
                    was_busy = False
                    try:
                        await self.arduino.set_mouth_position(MouthPosition.C)
                        self.mouth_position = MouthPosition.C
                    except Exception as e:
                        logger.error(f"Failed to close mouth after audio: {e}")

                await asyncio.sleep(0.04)  # 25Hz check rate
        except asyncio.CancelledError:
            logger.info("Talk monitor cancelled")
            raise
        except Exception as e:
            logger.error(f"Talk monitor error: {e}")

    async def _blink_monitor(self) -> None:
        """Randomly blink eyes when not busy.

        Uses Arduino firmware blink command for hardware-timed blink.
        Falls back to manual open/close if blink command not supported.
        """
        logger.info("Blink monitor started")

        try:
            while not self._shutdown:
                if self.blink_enabled and not self.is_busy and self.eyes_open:
                    delay = random.uniform(3.0, 7.0)
                    logger.debug(f"Blink scheduled in {delay:.1f}s")
                    await asyncio.sleep(delay)

                    if self.blink_enabled and not self.is_busy and self.eyes_open:
                        logger.debug("Executing blink")
                        await self.arduino.blink_eyes()
                        logger.debug("Blink completed")
                else:
                    await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            logger.info("Blink monitor cancelled")
            raise
        except Exception as e:
            logger.error(f"Blink monitor error: {e}")

    async def _execute_timing_schedule(
        self,
        timeline: list[tuple[int, MouthPosition]],
        audio_started: asyncio.Event | None = None,
    ) -> None:
        """Execute a phoneme timing schedule, sending position commands at correct times.

        Args:
            timeline: List of (time_ms, MouthPosition) to dispatch.
            audio_started: If provided, wait for this event before starting the clock.
                This ensures timing is synchronized with actual audio playback start.
        """
        if not timeline:
            return

        # Wait for audio to actually start before beginning the schedule
        if audio_started is not None:
            await audio_started.wait()

        start_time = time.monotonic()

        for target_ms, position in timeline:
            if self._shutdown:
                break

            # Calculate how long to wait
            elapsed_ms = (time.monotonic() - start_time) * 1000
            wait_ms = target_ms - elapsed_ms
            if wait_ms > 0:
                await asyncio.sleep(wait_ms / 1000)

            try:
                await self.arduino.set_mouth_position(position)
                self.mouth_position = position
            except Exception as e:
                logger.error(f"Timing dispatch error at {target_ms}ms: {e}")

    async def update_positions(
        self,
        eyes_position: State | None = None,
        mouth_position: State | None = None,
    ) -> dict[str, Any]:
        """Update servo positions manually (puppet mode).

        Args:
            eyes_position: Target eyes position (OPEN or CLOSED)
            mouth_position: Target mouth position (OPEN or CLOSED)

        Returns:
            Current bear state
        """
        if self.is_busy:
            raise RaspiRuxpinError("Bear is busy")

        try:
            if eyes_position is not None:
                if eyes_position == State.OPEN:
                    await self.arduino.open_eyes()
                    self.eyes_open = True
                elif eyes_position == State.CLOSED:
                    await self.arduino.close_eyes()
                    self.eyes_open = False

            if mouth_position is not None:
                if mouth_position == State.OPEN:
                    await self.arduino.set_mouth_position(MouthPosition.W)
                    self.mouth_position = MouthPosition.W
                elif mouth_position == State.CLOSED:
                    await self.arduino.set_mouth_position(MouthPosition.C)
                    self.mouth_position = MouthPosition.C

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
        self.status_text = "Generating speech..."
        logger.info(f"Speaking: {text}")
        tts_file = await self.audio_player.generate_tts(text)
        await self._perform_playback(tts_file, error_label="Speech failed")

    async def play_audio(self, sound_name: str) -> None:
        """Play audio file with mouth sync.

        Args:
            sound_name: Name of sound file (without .wav extension)

        Raises:
            RaspiRuxpinError: If already busy or playback fails
        """
        logger.info(f"Playing audio: {sound_name}")
        sound_file = self.audio_player.resolve_sound_file(sound_name)
        await self._perform_playback(sound_file, error_label="Audio playback failed")

    async def _perform_playback(self, audio_file: Path, error_label: str = "Playback failed") -> None:
        """Play an audio file with mouth sync, managing busy state.

        Args:
            audio_file: Path to the audio file.
            error_label: Prefix for error messages.

        Raises:
            RaspiRuxpinError: If already busy or playback fails.
        """
        if self.is_busy:
            raise RaspiRuxpinError("Bear is busy")

        try:
            self.is_busy = True

            if not self.eyes_open:
                await self.arduino.open_eyes()
                self.eyes_open = True

            await self._play_with_sync(audio_file)

            await self.arduino.set_mouth_position(MouthPosition.C)
            self.mouth_position = MouthPosition.C
        except Exception as e:
            raise RaspiRuxpinError(f"{error_label}: {e}") from e
        finally:
            self.is_busy = False
            self.status_text = ""

    async def _play_with_sync(self, audio_file: Path) -> None:
        """Play audio with the appropriate sync method.

        In amplitude mode, just plays audio — Arduino handles mouth from ADC.
        In phoneme mode, analyzes timing then dispatches commands during playback.
        Falls back to amplitude if phoneme deps aren't installed.
        """
        if self.sync_mode == SyncMode.REALTIME:
            # Realtime mode — Arduino reads ADC and drives servos autonomously
            self.status_text = "Playing..."
            await self.arduino.notify_audio_start()
            try:
                await self.audio_player.play_file(audio_file)
            finally:
                await self.arduino.notify_audio_stop()
        else:
            # Amplitude or phoneme — pre-analyze timing, then send commands
            method_label = self.sync_mode.value
            self.status_text = f"Analyzing audio ({method_label})..."
            timeline = await self.timing_store.get_or_analyze(
                audio_file, self.sync_mode
            )
            self.status_text = "Playing..."
            await self._play_audio_with_timing(audio_file, timeline)

    async def _play_audio_with_timing(
        self,
        audio_file: Path,
        timeline: list[tuple[int, MouthPosition]],
    ) -> None:
        """Play audio and execute timing schedule in parallel.

        The timing schedule waits for a start signal from play_file's
        start_callback, ensuring mouth movements are synchronized with
        the actual moment audio begins playing.

        Args:
            audio_file: Path to audio file.
            timeline: Timing schedule to execute.
        """
        audio_started = asyncio.Event()

        def on_audio_start() -> None:
            audio_started.set()

        timing_task = asyncio.create_task(
            self._execute_timing_schedule(timeline, audio_started)
        )
        try:
            await self.audio_player.play_file(audio_file, start_callback=on_audio_start)
        finally:
            # Ensure timing task completes or is cancelled
            if not timing_task.done():
                timing_task.cancel()
                try:
                    await timing_task
                except asyncio.CancelledError:
                    pass

    async def set_sync_mode(self, mode: SyncMode) -> None:
        """Switch synchronization mode.

        Args:
            mode: New sync mode.

        Raises:
            RaspiRuxpinError: If phoneme mode requested but deps unavailable.
        """
        if mode == SyncMode.PHONEME and not self.settings.sync.phoneme_available:
            reason = self.settings.sync.phoneme_missing_reason or "Unknown dependency issue"
            raise RaspiRuxpinError(f"Phoneme mode unavailable: {reason}")
        self.sync_mode = mode
        # Tell Arduino: realtime = ADC mode, amplitude/phoneme = serial command mode
        arduino_mode = SyncMode.REALTIME if mode == SyncMode.REALTIME else SyncMode.AMPLITUDE
        await self.arduino.set_mode(arduino_mode)
        logger.info(f"Sync mode set to {mode.value}")

    async def set_volume(self, level: int) -> None:
        """Set audio volume.

        Args:
            level: Volume level (0-90)
        """
        try:
            await self.audio_player.set_volume(level)
            logger.info(f"Volume set to {level}")
        except Exception as e:
            raise RaspiRuxpinError(f"Failed to set volume: {e}") from e

    def set_blink_enabled(self, enabled: bool) -> None:
        """Enable or disable automatic eye blinking."""
        self.blink_enabled = enabled
        logger.info(f"Eye blinking {'enabled' if enabled else 'disabled'}")

    def set_character(self, character: str) -> None:
        """Set the active character."""
        if character not in ["teddy", "grubby"]:
            logger.warning(f"Unknown character: {character}, defaulting to teddy")
            character = "teddy"
        self.character = character
        logger.info(f"Character set to {character}")

    def get_phrases(self) -> dict[str, str]:
        """Get available phrases."""
        return self.phrases.copy()

    def get_state(self) -> dict[str, Any]:
        """Get current bear state.

        Returns:
            Dictionary with current state information.
        """
        connection_type = "mock" if self.arduino.use_mock else "serial"
        return {
            "eyes": "open" if self.eyes_open else "closed",
            "mouth": "closed" if self.mouth_position == MouthPosition.C else "open",
            "eyes_position": 100 if self.eyes_open else 0,
            "mouth_position": self._mouth_position_percent(),
            "is_busy": self.is_busy,
            "volume": self.audio_player.volume,
            "blink_enabled": self.blink_enabled,
            "character": self.character,
            "sync_mode": self.sync_mode.value,
            "mouth_code": self.mouth_position.value,
            "arduino_connected": self.arduino.connected,
            "arduino_port": self.arduino.port,
            "arduino_baud_rate": self.arduino.baud_rate,
            "arduino_connection_type": connection_type,
            "status_text": self.status_text,
        }

    def _mouth_position_percent(self) -> int:
        """Convert current MouthPosition to a 0-100 percentage."""
        position_map: dict[MouthPosition, int] = {
            MouthPosition.C: 0,
            MouthPosition.T: 15,
            MouthPosition.S: 30,
            MouthPosition.N: 45,
            MouthPosition.M: 60,
            MouthPosition.L: 80,
            MouthPosition.W: 100,
        }
        return position_map.get(self.mouth_position, 0)

    def _on_arduino_mouth_position(self, position: MouthPosition) -> None:
        """Handle realtime mouth position reports from Arduino ADC mode.

        Called from the serial reader thread — updates state for the 10Hz
        state broadcast to pick up and relay to the frontend. Ignores
        reports when not playing audio (ambient noise guard).
        """
        if self.is_busy:
            self.mouth_position = position

