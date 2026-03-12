"""Async audio playback and TTS for Raspi Ruxpin.

This module provides platform-aware audio playback with amplitude tracking
for mouth synchronization. It supports both Linux (ALSA) and macOS (afplay).
"""

import asyncio
import hashlib
import logging
import platform
import struct
import wave
from collections.abc import Callable
from pathlib import Path

from mutagen.wave import WAVE

from backend.core.exceptions import AudioError

# Optional piper import (only available on Pi with [hardware] dependencies)
try:
    from piper import PiperVoice  # noqa: F401

    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False

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
        sounds_dir: Path = Path("data/sounds"),
        tts_output_dir: Path = Path("data/tts"),
        tts_engine: str = "espeak",
        tts_voice: str = "en+m3",
        tts_speed: int = 125,
        tts_pitch: int = 50,
        start_volume: int = 100,
        alsa_device: str | None = None,
        alsa_card_index: int | None = None,
        alsa_mixer: str = "PCM",
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
            tts_pitch: TTS voice pitch (0-99)
            start_volume: Initial volume level
            alsa_device: ALSA device name (e.g., 'hw:1,0', 'plughw:1,0')
            alsa_card_index: ALSA card index for mixer control
            alsa_mixer: ALSA mixer name (default 'PCM')
        """
        self.sample_rate = sample_rate
        self.amplitude_threshold = amplitude_threshold
        self.sounds_dir = sounds_dir
        self.tts_output_dir = tts_output_dir
        self.tts_engine = tts_engine
        self.tts_voice = tts_voice
        self.tts_speed = tts_speed
        self.tts_pitch = tts_pitch
        self.alsa_device = alsa_device
        self.alsa_card_index = alsa_card_index
        self.alsa_mixer = alsa_mixer

        self._current_amplitude = 0
        self._amplitude_lock = asyncio.Lock()
        self._volume = start_volume
        self._platform = platform.system()

        # Read current system volume and sync
        asyncio.create_task(self._initialize_volume(start_volume))

        device_info = f", device={alsa_device}" if alsa_device else ""
        card_info = f", card={alsa_card_index}" if alsa_card_index is not None else ""
        logger.info(
            f"AudioPlayer initialized: platform={self._platform}, "
            f"sample_rate={sample_rate}Hz, threshold={amplitude_threshold}"
            f"{device_info}{card_info}"
        )

    @property
    def current_amplitude(self) -> int:
        """Get current amplitude (thread-safe)."""
        return self._current_amplitude

    @property
    def volume(self) -> int:
        """Get current volume level."""
        return self._volume

    async def _initialize_volume(self, fallback_volume: int) -> None:
        """Initialize volume by reading system volume or using fallback.

        Args:
            fallback_volume: Fallback volume if system volume can't be read
        """
        try:
            # Try to read current system volume
            system_volume = await self.get_system_volume()
            if system_volume is not None:
                self._volume = system_volume
                logger.info(f"Synced with system volume: {system_volume}%")
            else:
                # Use fallback and set it
                await self.set_volume(fallback_volume)
                logger.info(f"Set volume to fallback: {fallback_volume}%")
        except Exception as e:
            logger.warning(f"Failed to read system volume: {e}, using fallback")
            await self.set_volume(fallback_volume)

    async def get_system_volume(self) -> int | None:
        """Get current system volume.

        Returns:
            Current system volume (0-100) or None if unavailable
        """
        try:
            if self._platform == "Darwin":
                # macOS: Read volume using AppleScript
                process = await asyncio.create_subprocess_exec(
                    "osascript",
                    "-e",
                    "output volume of (get volume settings)",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                stdout, _ = await process.communicate()
                volume = int(stdout.decode().strip())
                return volume
            else:
                # Linux: Read ALSA volume
                try:
                    import alsaaudio

                    if self.alsa_card_index is not None:
                        mixer = alsaaudio.Mixer(self.alsa_mixer, cardindex=self.alsa_card_index)
                    else:
                        mixer = alsaaudio.Mixer(self.alsa_mixer)
                    volumes = mixer.getvolume()
                    return volumes[0] if volumes else None
                except ImportError:
                    logger.debug("alsaaudio not available")
                    return None
        except Exception as e:
            logger.debug(f"Failed to read system volume: {e}")
            return None

    async def set_volume(self, level: int) -> None:
        """Set system volume level.

        Args:
            level: Volume level (0-90, capped to prevent system instability)

        Raises:
            AudioError: If volume setting fails
        """
        if not (0 <= level <= 90):
            raise AudioError(f"Volume must be between 0 and 90, got {level}")

        try:
            if self._platform == "Darwin":
                # macOS: Use AppleScript (0-100 scale)
                process = await asyncio.create_subprocess_exec(
                    "osascript",
                    "-e",
                    f"set volume output volume {level}",
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await process.wait()
            else:
                # Linux: Use ALSA
                try:
                    import alsaaudio

                    if self.alsa_card_index is not None:
                        mixer = alsaaudio.Mixer(self.alsa_mixer, cardindex=self.alsa_card_index)
                    else:
                        mixer = alsaaudio.Mixer(self.alsa_mixer)
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
        if self.tts_engine == "piper":
            return await self._generate_tts_piper(text, output_file)
        else:
            return await self._generate_tts_espeak(text, output_file)

    async def _generate_tts_piper(self, text: str, output_file: Path | None = None) -> Path:
        """Generate TTS using Piper CLI (neural TTS).

        Args:
            text: Text to synthesize
            output_file: Optional output file path

        Returns:
            Path to generated audio file

        Raises:
            AudioError: If TTS generation fails
        """
        if not output_file:
            text_hash = hashlib.md5(text.encode()).hexdigest()[:12]
            output_file = self.tts_output_dir / f"{text_hash}.wav"

        if output_file.exists():
            logger.info(f"TTS cache hit: {output_file.name}")
            return output_file

        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Piper model path (tts_voice contains the model path)
            model_path = Path(self.tts_voice)
            if not model_path.exists():
                raise AudioError(f"Piper model not found: {model_path}")

            # Find piper binary (look in models/piper/ or system PATH)
            piper_bin = None
            piper_paths = [
                Path("models/piper/piper"),
                Path("/usr/local/bin/piper"),
                Path("/opt/homebrew/bin/piper"),
            ]
            for path in piper_paths:
                if path.exists():
                    piper_bin = path
                    break

            if not piper_bin:
                raise AudioError(
                    "Piper binary not found. Download from: https://github.com/rhasspy/piper/releases"
                )

            # Call piper CLI as subprocess
            process = await asyncio.create_subprocess_exec(
                str(piper_bin),
                "--model",
                str(model_path),
                "--output_file",
                str(output_file),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Send text to stdin
            stdout, stderr = await process.communicate(input=text.encode())

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise AudioError(f"Piper CLI failed: {error_msg}")

            logger.info(f"Generated TTS with Piper: {output_file}")
            return output_file
        except FileNotFoundError:
            raise AudioError("Piper binary not found") from None
        except Exception as e:
            raise AudioError(f"Piper TTS generation failed: {e}") from e

    async def _generate_tts_espeak(self, text: str, output_file: Path | None = None) -> Path:
        """Generate TTS using espeak (Linux) or say (macOS).

        Args:
            text: Text to synthesize
            output_file: Optional output file path

        Returns:
            Path to generated audio file

        Raises:
            AudioError: If TTS generation fails
        """
        if not output_file:
            text_hash = hashlib.md5(text.encode()).hexdigest()[:12]
            output_file = self.tts_output_dir / f"{text_hash}.wav"

        if output_file.exists():
            logger.info(f"TTS cache hit: {output_file.name}")
            return output_file

        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            if self._platform == "Darwin":
                # macOS: Use built-in 'say' command with high-quality voices
                # Available voices: Fred (male), Samantha (female), Alex (default male)
                voice = "Fred"  # Natural male voice

                # Generate TTS using macOS 'say'
                # Output as AIFF first (say's native format)
                aiff_file = output_file.with_suffix(".aiff")

                process = await asyncio.create_subprocess_exec(
                    "say",
                    "-v",
                    voice,
                    "-o",
                    str(aiff_file),
                    text,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.PIPE,
                )

                _, stderr = await process.communicate()

                if process.returncode != 0:
                    raise AudioError(f"say failed: {stderr.decode()}")

                # Convert AIFF to 16kHz WAV using afconvert (built-in macOS tool)
                convert_process = await asyncio.create_subprocess_exec(
                    "afconvert",
                    "-f",
                    "WAVE",
                    "-d",
                    "LEI16",  # 16-bit signed int
                    "-r",
                    "16000",  # Resample to 16kHz
                    str(aiff_file),
                    str(output_file),
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, convert_stderr = await convert_process.communicate()

                if convert_process.returncode != 0:
                    raise AudioError(f"Audio conversion failed: {convert_stderr.decode()}")

                # Clean up temporary AIFF file
                aiff_file.unlink(missing_ok=True)

            else:
                # Linux: Use espeak
                process = await asyncio.create_subprocess_exec(
                    self.tts_engine,
                    "-v",
                    self.tts_voice,
                    "-s",
                    str(self.tts_speed),
                    "-p",
                    str(self.tts_pitch),
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
            engine = "say" if self._platform == "Darwin" else self.tts_engine
            raise AudioError(f"TTS engine '{engine}' not found") from None
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
                    amplitudes = [abs(x) for x in struct.unpack(f"{num_samples}h", frames)]
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
        self,
        audio_file: Path,
        amplitude_callback: Callable[[], None] | None = None,
        start_callback: Callable[[], None] | None = None,
    ) -> None:
        """Play audio file with amplitude tracking.

        Args:
            audio_file: Path to audio file
            amplitude_callback: Optional callback for amplitude updates
            start_callback: Optional callback invoked at the exact moment audio starts

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

            # Set initial amplitude to trigger mouth movement before audio starts
            # This gives the mouth a "head start" to begin opening
            if amplitudes:
                samples_for_preview = len(amplitudes) // int(duration * 50)
                initial_chunk = amplitudes[:samples_for_preview]
                initial_amplitude = sum(initial_chunk) // len(initial_chunk) if initial_chunk else 0

                async with self._amplitude_lock:
                    self._current_amplitude = initial_amplitude

            # Give mouth time to start moving (monitor checks every 0.04s + servo needs ~0.1s)
            await asyncio.sleep(0.10)

            # Signal that audio is about to start
            if start_callback:
                start_callback()

            # Now start both amplitude tracking and audio together (in sync)
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
                if self.alsa_device:
                    process = await asyncio.create_subprocess_exec(
                        "aplay",
                        "-D",
                        self.alsa_device,
                        str(audio_file),
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.PIPE,
                    )
                else:
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

    def resolve_sound_file(self, sound_name: str) -> Path:
        """Resolve a sound name to its file path, searching examples/ then user/.

        Args:
            sound_name: Name of sound file (without .wav extension)

        Returns:
            Path to the sound file

        Raises:
            AudioError: If sound file not found in any subdirectory
        """
        filename = f"{sound_name}.wav"
        for subdir in ("examples", "user"):
            candidate = self.sounds_dir / subdir / filename
            if candidate.exists():
                return candidate
        raise AudioError(
            f"Sound file not found: {sound_name} "
            f"(searched {self.sounds_dir}/examples/ and {self.sounds_dir}/user/)"
        )

    @staticmethod
    def read_wav_title(path: Path) -> str | None:
        """Read the title metadata from a WAV file.

        Args:
            path: Path to WAV file

        Returns:
            Title string or None if no title metadata
        """
        try:
            w = WAVE(path)
            if w.tags and "TIT2" in w.tags:
                return str(w.tags["TIT2"])
        except Exception as e:
            logger.debug(f"Failed to read metadata from {path}: {e}")
        return None

    def list_sounds(self) -> dict[str, str]:
        """Discover all available sounds with titles from WAV metadata.

        Scans examples/ and user/ subdirectories. Returns a dictionary
        mapping sound name to its title (from WAV metadata) or the
        filename stem if no title is embedded.

        Returns:
            Dictionary mapping sound name to display title
        """
        sounds: dict[str, str] = {}
        for subdir in ("examples", "user"):
            subdir_path = self.sounds_dir / subdir
            if subdir_path.is_dir():
                for wav in sorted(subdir_path.glob("*.wav")):
                    title = self.read_wav_title(wav)
                    sounds[wav.stem] = title or wav.stem
        return sounds

