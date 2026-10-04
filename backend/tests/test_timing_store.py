"""Tests for the timing cache."""

import os
from pathlib import Path

import pytest

from backend.core.enums import MouthPosition, SyncMode
from backend.hardware.timing_store import TimingStore


@pytest.fixture
def analyze_calls(monkeypatch: pytest.MonkeyPatch) -> list[Path]:
    """Replace the amplitude analyzer with a fake that records its calls."""
    calls: list[Path] = []

    async def fake_analyze(audio_file: Path) -> list[tuple[int, MouthPosition]]:
        calls.append(audio_file)
        return [(0, MouthPosition.C), (20, MouthPosition.W)]

    monkeypatch.setattr("backend.hardware.audio_analyzer.analyze_wav_amplitude", fake_analyze)
    return calls


@pytest.fixture
def audio_file(tmp_path: Path) -> Path:
    path = tmp_path / "clip.wav"
    path.write_bytes(b"not really audio")
    return path


@pytest.mark.unit
async def test_second_call_uses_cache(
    tmp_path: Path, audio_file: Path, analyze_calls: list[Path]
) -> None:
    store = TimingStore(tmp_path / "timing")

    await store.get_or_analyze(audio_file, SyncMode.AMPLITUDE)
    await store.get_or_analyze(audio_file, SyncMode.AMPLITUDE)

    assert len(analyze_calls) == 1


@pytest.mark.unit
async def test_replaced_audio_is_reanalyzed(
    tmp_path: Path, audio_file: Path, analyze_calls: list[Path]
) -> None:
    store = TimingStore(tmp_path / "timing")
    await store.get_or_analyze(audio_file, SyncMode.AMPLITUDE)

    # Same name, newer audio: the cached timing no longer matches the clip
    cached = tmp_path / "timing" / "clip_amp.csv"
    newer = cached.stat().st_mtime + 10
    os.utime(audio_file, (newer, newer))

    await store.get_or_analyze(audio_file, SyncMode.AMPLITUDE)

    assert len(analyze_calls) == 2


@pytest.mark.unit
async def test_older_audio_keeps_cache(
    tmp_path: Path, audio_file: Path, analyze_calls: list[Path]
) -> None:
    store = TimingStore(tmp_path / "timing")
    await store.get_or_analyze(audio_file, SyncMode.AMPLITUDE)

    cached = tmp_path / "timing" / "clip_amp.csv"
    older = cached.stat().st_mtime - 10
    os.utime(audio_file, (older, older))

    await store.get_or_analyze(audio_file, SyncMode.AMPLITUDE)

    assert len(analyze_calls) == 1
