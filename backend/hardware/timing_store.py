"""Timing data cache for audio analysis results.

Manages cached timing CSV files in the data/timing/ directory.
Each CSV maps time offsets (in milliseconds) to MouthPosition codes,
avoiding re-analysis of the same audio file.
"""

import csv
import logging
from pathlib import Path

from backend.core.enums import MouthPosition, SyncMode

logger = logging.getLogger(__name__)


class TimingStore:
    """Manages cached timing data for audio files.

    Timing CSVs are stored alongside audio files in a timing/ subdirectory.
    Format: header line "time_ms,position", then rows like "280,M".

    Attributes:
        timing_dir: Root directory for timing CSVs.
    """

    def __init__(self, timing_dir: Path) -> None:
        self.timing_dir = timing_dir
        self.timing_dir.mkdir(parents=True, exist_ok=True)

    def _csv_path(self, audio_file: Path, method: SyncMode) -> Path:
        """Get the CSV path for a given audio file and analysis method."""
        stem = audio_file.stem
        suffix = "amp" if method == SyncMode.AMPLITUDE else "phn"
        return self.timing_dir / f"{stem}_{suffix}.csv"

    async def get_or_analyze(
        self,
        audio_file: Path,
        method: SyncMode,
    ) -> list[tuple[int, MouthPosition]]:
        """Load cached timing data or analyze fresh.

        Args:
            audio_file: Path to the audio file.
            method: Analysis method to use.

        Returns:
            List of (time_ms, MouthPosition) tuples.
        """
        csv_path = self._csv_path(audio_file, method)

        # Try cache first
        if csv_path.exists():
            cached = await self.load(csv_path)
            if cached:
                logger.info(f"Loaded cached timing: {csv_path.name} ({len(cached)} entries)")
                return cached

        # Analyze fresh
        from backend.hardware.audio_analyzer import (
            analyze_wav_amplitude,
            analyze_wav_phoneme,
        )

        if method == SyncMode.AMPLITUDE:
            timeline = await analyze_wav_amplitude(audio_file)
        else:
            timeline = await analyze_wav_phoneme(audio_file)

        # Cache result
        await self.save(csv_path, timeline)
        logger.info(f"Cached timing: {csv_path.name} ({len(timeline)} entries)")
        return timeline

    async def load(self, csv_path: Path) -> list[tuple[int, MouthPosition]]:
        """Load timing data from a CSV file.

        Args:
            csv_path: Path to the CSV file.

        Returns:
            List of (time_ms, MouthPosition) tuples.
        """
        import asyncio

        return await asyncio.to_thread(self._load_sync, csv_path)

    async def save(
        self, csv_path: Path, timeline: list[tuple[int, MouthPosition]]
    ) -> None:
        """Save timing data to a CSV file.

        Args:
            csv_path: Path to write the CSV.
            timeline: Timing data to save.
        """
        import asyncio

        await asyncio.to_thread(self._save_sync, csv_path, timeline)

    @staticmethod
    def _load_sync(csv_path: Path) -> list[tuple[int, MouthPosition]]:
        """Synchronous CSV load."""
        timeline: list[tuple[int, MouthPosition]] = []
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header != ["time_ms", "position"]:
                logger.warning(f"Unexpected CSV header in {csv_path}: {header}")
                return []
            for row in reader:
                if len(row) >= 2:
                    try:
                        time_ms = int(row[0])
                        position = MouthPosition(row[1])
                        timeline.append((time_ms, position))
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Skipping invalid CSV row {row}: {e}")
        return timeline

    @staticmethod
    def _save_sync(
        csv_path: Path, timeline: list[tuple[int, MouthPosition]]
    ) -> None:
        """Synchronous CSV save."""
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["time_ms", "position"])
            for time_ms, position in timeline:
                writer.writerow([time_ms, position.value])
