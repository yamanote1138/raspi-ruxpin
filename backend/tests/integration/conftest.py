"""Shared fixtures for integration tests."""

from pathlib import Path

import pytest

from backend.config import (
    AppSettings,
    AudioSettings,
    SerialSettings,
    SyncSettings,
    TTSSettings,
)
from backend.core.enums import SyncMode


@pytest.fixture
def integration_settings(tmp_path: Path) -> AppSettings:
    """Provide integration test settings with tmp_path directories."""
    sounds_dir = tmp_path / "sounds"
    sounds_dir.mkdir()
    (sounds_dir / "examples").mkdir()
    (sounds_dir / "user").mkdir()
    tts_dir = tmp_path / "tts"
    tts_dir.mkdir()
    timing_dir = tmp_path / "timing"
    timing_dir.mkdir()

    return AppSettings(
        environment="testing",
        debug=True,
        host="127.0.0.1",
        port=8080,
        audio=AudioSettings(
            sample_rate=16000,
            amplitude_threshold=500,
            sounds_dir=sounds_dir,
            start_volume=80,
            mixer="PCM",
        ),
        tts=TTSSettings(
            engine="espeak",
            output_dir=tts_dir,
            voice="en+m3",
            speed=125,
            pitch=50,
        ),
        serial=SerialSettings(
            port="/dev/mock",
            use_mock=True,
            connect_timeout=5.0,
        ),
        sync=SyncSettings(
            mode=SyncMode.AMPLITUDE,
            timing_dir=timing_dir,
        ),
    )
