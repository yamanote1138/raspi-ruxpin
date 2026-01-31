"""Async audio playback and TTS for Raspi Ruxpin.

This module provides platform-aware audio playback with amplitude tracking
for mouth synchronization. It supports both Linux (ALSA) and macOS (afplay).
"""

import asyncio
import logging
import platform
import struct
import subprocess
from pathlib import Path
from typing import Callable

import wave

from backend.core.exceptions import AudioError

logger = logging.getLogger(__name__)


class AudioPlayer:
    """Async audio player with amplitude tracking.

    This class handles audio playback and TTS generation with thread-safe
    amplitude tracking for mouth synchronization. It automatically adapts
    to the host platform (Linux/macOS).

    Attributes:
        sample_rate: Audio sample rate in Hz
        amplitude_threshold: Amplitude threshold for mouth movement
        sounds_dir: Directory containing sound files
        tts_output_dir: Directory for generated TTS files
        tts_engine: TTS engine to use (espeak)
        tts_voice: Voice for TTS
        tts_speed: Speaking speed for TTS
        current_amplitude: Current audio amplitude (thread-safe)
        volume: Current volume level (0-100)
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        amplitude_threshold: int = 500,
        sounds_dir: Path = Path("sounds"),
        tts_output_dir: Path = Path("sounds/tts"),
        tts_engine: str = "espeak",
        tts_voice: str = "en+m3",
        tts_speed: int = 125,
        start_volume: int = 100,
    ) -> None:
        """Initialize audio player.

        Args:
            sample_rate: Audio sample rate
            amplitude_threshold: Threshold for mouth movement
            sounds_dir: Directory with sound files
            tts_output_dir: Directory for TTS output
            tts_engine: TTS engine name
            tts_voice: TTS voice
            tts_speed: TTS speaking speed
            start_volume: Initial volume level
        """
        self.sample_rate = sample_rate
        self.amplitude_threshold = amplitude_threshold
        self.sounds_dir = sounds_dir
        self.tts_output_dir = tts_output_dir
        self.tts_engine = tts_engine
        self.tts_voice = tts_voice
        self.tts_speed = tts_speed

        self._current_amplitude = 0
        self._amplitude_lock = asyncio.Lock()
        self._volume = start_volume
        self._platform = platform.system()

        # Initialize volume
        asyncio.create_task(self.set_volume(start_volume))

        logger.info(
            f"AudioPlayer initialized: platform={self._platform}, "
            f"sample_rate={sample_rate}Hz, threshold={amplitude_threshold}"
        )

    @property
    def current_amplitude(self) -> int:
        """Get current amplitude (thread-safe)."""
        return self._current_amplitude

    @property
    def volume(self) -> int:
        """Get current volume level."""
        return self._volume

    async def set_volume(self, level: int) -> None:
        """Set system volume level.

        Args:
            level: Volume level (0-100)

        Raises:
            AudioError: If volume setting fails
        """
        if not (0 <= level <= 100):
            raise AudioError(f"Volume must be between 0 and 100, got {level}")

        try:
            if self._platform == "Darwin":
                # macOS: Use AppleScript
                volume_percent = int((level / 100) * 7)  # macOS uses 0-7 scale
                await asyncio.create_subprocess_exec(
                    "osascript",
                    "-e",
                    f"set volume output volume {volume_percent}",
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
            else:
                # Linux: Use ALSA
                try:
                    import alsaaudio

                    mixer = alsaaudio.Mixer("PCM")
                    mixer.setvolume(level)
                except ImportError:
                    logger.warning("alsaaudio not available, skipping volume control")

            self._volume = level
            logger.info(f"Volume set to {level}%")
        except Exception as e:
            raise AudioError(f"Failed to set volume: {e}") from e

    async def generate_tts(self, text: str, output_file: Path | None = None) -> Path:
        """Generate TTS audio file from text.

        Args:
            text: Text to synthesize
            output_file: Optional output file path

        Returns:
            Path to generated audio file

        Raises:
            AudioError: If TTS generation fails
        """
        if not output_file:
            # Generate unique filename
            safe_text = "".join(c if c.isalnum() else "_" for c in text[:30])
            output_file = self.tts_output_dir / f"{safe_text}.wav"

        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Generate TTS using espeak
            process = await asyncio.create_subprocess_exec(
                self.tts_engine,
                "-v",
                self.tts_voice,
                "-s",
                str(self.tts_speed),
                "-w",
                str(output_file),
                text,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )

            _, stderr = await process.communicate()

            if process.returncode != 0:
                raise AudioError(f"espeak failed: {stderr.decode()}")

            logger.info(f"Generated TTS: {output_file}")
            return output_file
        except FileNotFoundError:
            raise AudioError(f"TTS engine '{self.tts_engine}' not found") from None
        except Exception as e:
            raise AudioError(f"TTS generation failed: {e}") from e

    def _read_amplitude(self, audio_file: Path) -> list[int]:
        """Read amplitude values from audio file.

        Args:
            audio_file: Path to WAV file

        Returns:
            List of amplitude values

        Raises:
            AudioError: If file reading fails
        """
        try:
            with wave.open(str(audio_file), "rb") as wf:
                frames = wf.readframes(wf.getnframes())
                sample_width = wf.getsampwidth()

                # Parse frames based on sample width
                if sample_width == 1:
                    # 8-bit unsigned
                    amplitudes = list(struct.unpack(f"{len(frames)}B", frames))
                elif sample_width == 2:
                    # 16-bit signed
                    num_samples = len(frames) // 2
                    amplitudes = [
                        abs(x) for x in struct.unpack(f"{num_samples}h", frames)
                    ]
                else:
                    raise AudioError(f"Unsupported sample width: {sample_width}")

                return amplitudes
        except Exception as e:
            raise AudioError(f"Failed to read amplitude from {audio_file}: {e}") from e

    async def _update_amplitude_loop(
        self, amplitudes: list[int], duration: float, callback: Callable[[], None] | None
    ) -> None:
        """Update amplitude values during playback.

        Args:
            amplitudes: List of amplitude values
            duration: Total playback duration
            callback: Optional callback for amplitude updates
        """
        if not amplitudes:
            return

        samples_per_update = max(1, len(amplitudes) // int(duration * 50))  # 50Hz update rate
        update_interval = duration / (len(amplitudes) / samples_per_update)

        try:
            for i in range(0, len(amplitudes), samples_per_update):
                chunk = amplitudes[i : i + samples_per_update]
                avg_amplitude = sum(chunk) // len(chunk) if chunk else 0

                async with self._amplitude_lock:
                    self._current_amplitude = avg_amplitude

                if callback:
                    callback()

                await asyncio.sleep(update_interval)
        finally:
            async with self._amplitude_lock:
                self._current_amplitude = 0

    async def play_file(
        self, audio_file: Path, amplitude_callback: Callable[[], None] | None = None
    ) -> None:
        """Play audio file with amplitude tracking.

        Args:
            audio_file: Path to audio file
            amplitude_callback: Optional callback for amplitude updates

        Raises:
            AudioError: If playback fails
        """
        if not audio_file.exists():
            raise AudioError(f"Audio file not found: {audio_file}")

        try:
            # Read amplitude data
            amplitudes = await asyncio.to_thread(self._read_amplitude, audio_file)

            # Get audio duration
            with wave.open(str(audio_file), "rb") as wf:
                duration = wf.getnframes() / wf.getframerate()

            # Start amplitude tracking task
            amplitude_task = asyncio.create_task(
                self._update_amplitude_loop(amplitudes, duration, amplitude_callback)
            )

            # Play audio (platform-specific)
            if self._platform == "Darwin":
                # macOS: Use afplay
                process = await asyncio.create_subprocess_exec(
                    "afplay",
                    str(audio_file),
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.PIPE,
                )
            else:
                # Linux: Use aplay
                process = await asyncio.create_subprocess_exec(
                    "aplay",
                    str(audio_file),
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.PIPE,
                )

            # Wait for playback to complete
            _, stderr = await process.communicate()

            if process.returncode != 0:
                raise AudioError(f"Audio playback failed: {stderr.decode()}")

            # Wait for amplitude tracking to complete
            await amplitude_task

            logger.info(f"Played audio: {audio_file}")
        except Exception as e:
            raise AudioError(f"Failed to play {audio_file}: {e}") from e

    async def play_sound(
        self, sound_name: str, amplitude_callback: Callable[[], None] | None = None
    ) -> None:
        """Play a sound file by name.

        Args:
            sound_name: Name of sound file (without .wav extension)
            amplitude_callback: Optional callback for amplitude updates

        Raises:
            AudioError: If sound file not found or playback fails
        """
        sound_file = self.sounds_dir / f"{sound_name}.wav"
        await self.play_file(sound_file, amplitude_callback)

    async def speak(
        self, text: str, amplitude_callback: Callable[[], None] | None = None
    ) -> None:
        """Synthesize and play speech.

        Args:
            text: Text to speak
            amplitude_callback: Optional callback for amplitude updates

        Raises:
            AudioError: If TTS or playback fails
        """
        # Generate TTS
        tts_file = await self.generate_tts(text)

        # Play the generated file
        await self.play_file(tts_file, amplitude_callback)

    def is_mouth_open_threshold(self) -> bool:
        """Check if current amplitude exceeds mouth threshold.

        Returns:
            True if amplitude is above threshold
        """
        return self._current_amplitude > self.amplitude_threshold
