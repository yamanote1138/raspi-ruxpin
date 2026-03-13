"""Tests for audio analysis pipeline."""

import struct
import wave
from pathlib import Path

import pytest

from backend.core.enums import MouthPosition
from backend.hardware.audio_analyzer import (
    AMPLITUDE_THRESHOLDS,
    amplitude_to_position,
    analyze_wav_amplitude,
)


@pytest.mark.unit
def test_amplitude_silence() -> None:
    """Silence should map to closed mouth."""
    assert amplitude_to_position(0.0) == MouthPosition.C


@pytest.mark.unit
def test_amplitude_very_quiet() -> None:
    """Very quiet should map to T (teeth together)."""
    assert amplitude_to_position(0.015) == MouthPosition.T


@pytest.mark.unit
def test_amplitude_quiet() -> None:
    """Quiet should map to S (slightly open)."""
    assert amplitude_to_position(0.04) == MouthPosition.S


@pytest.mark.unit
def test_amplitude_medium() -> None:
    """Medium should map to N (neutral)."""
    assert amplitude_to_position(0.06) == MouthPosition.N


@pytest.mark.unit
def test_amplitude_loud() -> None:
    """Loud should map to M (medium open)."""
    assert amplitude_to_position(0.09) == MouthPosition.M


@pytest.mark.unit
def test_amplitude_very_loud() -> None:
    """Very loud should map to L (large open)."""
    assert amplitude_to_position(0.15) == MouthPosition.L


@pytest.mark.unit
def test_amplitude_maximum() -> None:
    """Maximum should map to W (wide open)."""
    assert amplitude_to_position(0.2) == MouthPosition.W
    assert amplitude_to_position(1.0) == MouthPosition.W


@pytest.mark.unit
def test_threshold_boundaries() -> None:
    """Test exact threshold boundary values."""
    # At exactly each threshold, should match the threshold's position
    for threshold, expected_pos in AMPLITUDE_THRESHOLDS:
        result = amplitude_to_position(threshold)
        assert result == expected_pos, (
            f"At threshold {threshold}: expected {expected_pos}, got {result}"
        )


@pytest.mark.unit
def test_threshold_just_below() -> None:
    """Test values just below each threshold fall to the next position."""
    for i, (threshold, _) in enumerate(AMPLITUDE_THRESHOLDS[:-1]):
        just_below = threshold - 0.001
        result = amplitude_to_position(just_below)
        _, next_pos = AMPLITUDE_THRESHOLDS[i + 1]
        assert result == next_pos, (
            f"Just below {threshold}: expected {next_pos}, got {result}"
        )


def _create_test_wav(path: Path, samples: list[int], sample_rate: int = 16000) -> None:
    """Helper to create a test WAV file."""
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        data = struct.pack(f"<{len(samples)}h", *samples)
        wf.writeframes(data)


@pytest.mark.unit
async def test_analyze_silent_wav(tmp_path: Path) -> None:
    """Analyzing a silent WAV should return all C positions."""
    wav_file = tmp_path / "silence.wav"
    # 1 second of silence at 16kHz
    samples = [0] * 16000
    _create_test_wav(wav_file, samples)

    timeline = await analyze_wav_amplitude(wav_file)
    assert len(timeline) > 0
    for _time_ms, pos in timeline:
        assert pos == MouthPosition.C


@pytest.mark.unit
async def test_analyze_loud_wav(tmp_path: Path) -> None:
    """Analyzing a loud WAV should include open mouth positions."""
    wav_file = tmp_path / "loud.wav"
    # 0.5s of loud signal (alternating high/low)
    samples = []
    for i in range(8000):
        val = 20000 if i % 2 == 0 else -20000
        samples.append(val)
    _create_test_wav(wav_file, samples)

    timeline = await analyze_wav_amplitude(wav_file)
    assert len(timeline) > 0

    # At least some positions should be open
    open_positions = [pos for _, pos in timeline if pos != MouthPosition.C]
    assert len(open_positions) > 0


@pytest.mark.unit
async def test_analyze_timeline_ordered(tmp_path: Path) -> None:
    """Timeline should have monotonically increasing timestamps."""
    wav_file = tmp_path / "test.wav"
    samples = [int(10000 * (i % 100) / 100) for i in range(16000)]
    _create_test_wav(wav_file, samples)

    timeline = await analyze_wav_amplitude(wav_file)
    times = [t for t, _ in timeline]
    assert times == sorted(times)
