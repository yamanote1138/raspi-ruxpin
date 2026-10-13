"""Tests for AudioPlayer pieces that don't need audio hardware."""

from pathlib import Path

import pytest

from backend.hardware.audio_player import AudioPlayer


def _player(tmp_path: Path, **kwargs: str | int) -> AudioPlayer:
    return AudioPlayer(tts_output_dir=tmp_path, **kwargs)  # type: ignore[arg-type]


@pytest.mark.unit
def test_tts_cache_path_is_stable(tmp_path: Path) -> None:
    assert _player(tmp_path)._tts_cache_path("hello") == _player(tmp_path)._tts_cache_path("hello")


@pytest.mark.unit
def test_tts_cache_path_depends_on_text(tmp_path: Path) -> None:
    player = _player(tmp_path)

    assert player._tts_cache_path("hello") != player._tts_cache_path("goodbye")


@pytest.mark.unit
@pytest.mark.parametrize(
    "change",
    [
        {"mac_voice": "Samantha"},
        {"tts_voice": "en-us+m7"},
        {"tts_engine": "piper"},
        {"tts_speed": 200},
        {"tts_pitch": 10},
    ],
)
def test_tts_cache_path_depends_on_voice_settings(
    tmp_path: Path, change: dict[str, str | int]
) -> None:
    assert _player(tmp_path)._tts_cache_path("hello") != _player(
        tmp_path, **change
    )._tts_cache_path("hello")
