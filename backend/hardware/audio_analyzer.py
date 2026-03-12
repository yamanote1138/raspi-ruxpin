"""Audio analysis for mouth synchronization.

Provides two analysis methods:
- Amplitude: Fast, works everywhere. Maps RMS amplitude to 7 mouth positions.
- Phoneme: Higher quality, requires faster-whisper + phonemizer. Transcribes audio
  to phonemes and maps each to a mouth position with timing.

Both methods produce the same output format: a list of (time_ms, MouthPosition) tuples
that can be used as a timing schedule or cached as CSV.
"""

import logging
import math
import struct
import wave
from pathlib import Path

from backend.core.enums import MouthPosition

logger = logging.getLogger(__name__)

# Amplitude thresholds for mapping normalized RMS to mouth positions.
# These are tuned for 0.0-1.0 normalized float audio with 0.7 power compression.
AMPLITUDE_THRESHOLDS: list[tuple[float, MouthPosition]] = [
    (0.17, MouthPosition.W),
    (0.12, MouthPosition.L),
    (0.085, MouthPosition.M),
    (0.055, MouthPosition.N),
    (0.03, MouthPosition.S),
    (0.01, MouthPosition.T),
    (0.0, MouthPosition.C),
]

# IPA phoneme to mouth position mappings.
# Covers the standard IPA phonemes produced by phonemizer.
PHONEME_TO_MOUTH: dict[str, MouthPosition] = {
    # Closed / silence
    "": MouthPosition.C,
    # Teeth together — alveolar stops, fricatives, nasals, laterals
    "t": MouthPosition.T,
    "d": MouthPosition.T,
    "s": MouthPosition.T,
    "z": MouthPosition.T,
    "n": MouthPosition.T,
    "l": MouthPosition.T,
    "ɹ": MouthPosition.T,
    "ɾ": MouthPosition.T,
    # Slightly open — post-alveolar, dental
    "θ": MouthPosition.S,
    "ð": MouthPosition.S,
    "ʃ": MouthPosition.S,
    "ʒ": MouthPosition.S,
    "tʃ": MouthPosition.S,
    "dʒ": MouthPosition.S,
    "j": MouthPosition.S,
    # Neutral — schwa, short vowels, reduced vowels
    "ə": MouthPosition.N,
    "ɪ": MouthPosition.N,
    "ʊ": MouthPosition.N,
    "ɨ": MouthPosition.N,
    "i": MouthPosition.N,
    "u": MouthPosition.N,
    "ɚ": MouthPosition.N,
    # Medium open — mid vowels
    "ɛ": MouthPosition.M,
    "æ": MouthPosition.M,
    "e": MouthPosition.M,
    "ɝ": MouthPosition.M,
    "ʌ": MouthPosition.M,
    "ɔ": MouthPosition.M,
    # Large open — open vowels
    "ɑ": MouthPosition.L,
    "ɒ": MouthPosition.L,
    "a": MouthPosition.L,
    # Wide open — diphthongs, wide vowels
    "aɪ": MouthPosition.W,
    "aʊ": MouthPosition.W,
    "ɔɪ": MouthPosition.W,
    "oʊ": MouthPosition.W,
    # Bilabials and labials
    "p": MouthPosition.C,
    "b": MouthPosition.C,
    "m": MouthPosition.C,
    "f": MouthPosition.T,
    "v": MouthPosition.T,
    "w": MouthPosition.N,
    # Velars and glottals
    "k": MouthPosition.N,
    "ɡ": MouthPosition.N,
    "g": MouthPosition.N,
    "ŋ": MouthPosition.N,
    "h": MouthPosition.S,
    "ʔ": MouthPosition.C,
}

# Window size for amplitude analysis (milliseconds)
WINDOW_MS = 20

# Power compression exponent for amplitude analysis
POWER_COMPRESSION = 0.7


def amplitude_to_position(normalized_rms: float) -> MouthPosition:
    """Map a normalized RMS amplitude value to a mouth position.

    Args:
        normalized_rms: RMS value in range 0.0 to 1.0 (after power compression).

    Returns:
        The corresponding MouthPosition.
    """
    for threshold, position in AMPLITUDE_THRESHOLDS:
        if normalized_rms >= threshold:
            return position
    return MouthPosition.C


async def analyze_wav_amplitude(audio_file: Path) -> list[tuple[int, MouthPosition]]:
    """Analyze a WAV file using amplitude-based method.

    Reads audio in 20ms windows, computes RMS, applies power compression,
    and maps to mouth positions.

    Args:
        audio_file: Path to WAV file.

    Returns:
        List of (time_ms, MouthPosition) tuples.
    """
    import asyncio

    return await asyncio.to_thread(_analyze_amplitude_sync, audio_file)


def _analyze_amplitude_sync(audio_file: Path) -> list[tuple[int, MouthPosition]]:
    """Synchronous amplitude analysis (called via to_thread)."""
    with wave.open(str(audio_file), "rb") as wf:
        sample_rate = wf.getframerate()
        n_channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        n_frames = wf.getnframes()
        raw_data = wf.readframes(n_frames)

    # Parse samples to floats normalized to -1.0..1.0
    if sample_width == 2:
        num_samples = len(raw_data) // 2
        samples = list(struct.unpack(f"<{num_samples}h", raw_data))
        max_val = 32768.0
    elif sample_width == 1:
        samples = [s - 128 for s in raw_data]
        max_val = 128.0
    else:
        logger.warning(f"Unsupported sample width {sample_width}, treating as 16-bit")
        num_samples = len(raw_data) // 2
        samples = list(struct.unpack(f"<{num_samples}h", raw_data))
        max_val = 32768.0

    # If stereo, take only the first channel
    if n_channels > 1:
        samples = samples[::n_channels]

    # Process in windows
    window_samples = int(sample_rate * WINDOW_MS / 1000)
    timeline: list[tuple[int, MouthPosition]] = []

    for i in range(0, len(samples), window_samples):
        chunk = samples[i : i + window_samples]
        if not chunk:
            break

        # Compute RMS
        sum_sq = sum((s / max_val) ** 2 for s in chunk)
        rms = math.sqrt(sum_sq / len(chunk))

        # Apply power compression
        compressed = rms**POWER_COMPRESSION if rms > 0 else 0.0

        position = amplitude_to_position(compressed)
        time_ms = int(i / sample_rate * 1000)
        timeline.append((time_ms, position))

    logger.info(f"Amplitude analysis: {len(timeline)} frames from {audio_file.name}")
    return timeline


async def analyze_wav_phoneme(audio_file: Path) -> list[tuple[int, MouthPosition]]:
    """Analyze a WAV file using phoneme-based method.

    Uses faster-whisper for transcription with word timestamps,
    then phonemizer to convert words to IPA phonemes.

    Args:
        audio_file: Path to WAV file.

    Returns:
        List of (time_ms, MouthPosition) tuples.

    Raises:
        ImportError: If faster-whisper or phonemizer are not installed.
    """
    import asyncio

    return await asyncio.to_thread(_analyze_phoneme_sync, audio_file)


def _ensure_espeak_library() -> None:
    """Ensure the espeak-ng shared library is discoverable.

    On macOS with Homebrew (especially Apple Silicon), the espeak-ng dylib
    lives in /opt/homebrew/lib which isn't in the default search path.
    """
    import ctypes.util
    import os

    if ctypes.util.find_library("espeak-ng") is None:
        # Try common Homebrew paths
        for lib_path in ["/opt/homebrew/lib", "/usr/local/lib"]:
            espeak_dylib = Path(lib_path) / "libespeak-ng.dylib"
            if espeak_dylib.exists():
                existing = os.environ.get("DYLD_LIBRARY_PATH", "")
                if lib_path not in existing:
                    os.environ["DYLD_LIBRARY_PATH"] = f"{lib_path}:{existing}" if existing else lib_path
                    logger.info(f"Added {lib_path} to DYLD_LIBRARY_PATH for espeak-ng")
                break


def _analyze_phoneme_sync(audio_file: Path) -> list[tuple[int, MouthPosition]]:
    """Synchronous phoneme analysis (called via to_thread)."""
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise ImportError(
            "Phoneme analysis requires faster-whisper. "
            "Install with: uv pip install -e '.[phoneme]'"
        ) from exc

    _ensure_espeak_library()

    try:
        from phonemizer.backend import EspeakBackend
        from phonemizer.separator import Separator
    except ImportError as exc:
        raise ImportError(
            "Phoneme analysis requires phonemizer. "
            "Install with: uv pip install -e '.[phoneme]'"
        ) from exc

    # Transcribe with word-level timestamps
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    segments, _info = model.transcribe(str(audio_file), word_timestamps=True)

    # Collect words with timing
    words_with_timing: list[tuple[str, float, float]] = []
    for segment in segments:
        if segment.words:
            for word in segment.words:
                words_with_timing.append((word.word.strip(), word.start, word.end))

    if not words_with_timing:
        logger.warning("No words detected in audio")
        return [(0, MouthPosition.C)]

    # Phonemize all words
    backend = EspeakBackend("en-us")
    separator = Separator(phone=" ", word=" | ")

    all_words = [w[0] for w in words_with_timing]
    phonemized = backend.phonemize(all_words, separator=separator, strip=True)

    # Build timeline
    timeline: list[tuple[int, MouthPosition]] = []

    for (_word, start, end), phones_str in zip(words_with_timing, phonemized, strict=False):
        phones = [p.strip() for p in phones_str.replace("|", "").split() if p.strip()]
        if not phones:
            continue

        # Distribute phonemes evenly across the word duration
        duration = end - start
        phone_duration = duration / len(phones) if phones else duration

        for j, phone in enumerate(phones):
            time_ms = int((start + j * phone_duration) * 1000)
            position = _phoneme_to_position(phone)
            timeline.append((time_ms, position))

    # Sort by time and add closing position at the end
    timeline.sort(key=lambda x: x[0])
    if timeline:
        last_time = timeline[-1][0]
        timeline.append((last_time + 100, MouthPosition.C))

    logger.info(f"Phoneme analysis: {len(timeline)} events from {audio_file.name}")
    return timeline


def _phoneme_to_position(phoneme: str) -> MouthPosition:
    """Map a single IPA phoneme to a mouth position.

    Tries exact match first, then single-character fallback.
    """
    if phoneme in PHONEME_TO_MOUTH:
        return PHONEME_TO_MOUTH[phoneme]
    # Try first character for multi-character phonemes
    if len(phoneme) > 1 and phoneme[0] in PHONEME_TO_MOUTH:
        return PHONEME_TO_MOUTH[phoneme[0]]
    return MouthPosition.N  # Default to neutral for unknown phonemes
