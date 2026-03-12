"""Standalone CLI entry point for Raspi Ruxpin.

Creates Arduino, AudioPlayer, TimingStore, and BearService directly
(no FastAPI) and runs the interactive CLI menu.
"""

import asyncio
import logging

from backend.cli.menu import RuxpinCLI
from backend.config import get_settings
from backend.hardware.arduino import ArduinoController
from backend.hardware.audio_player import AudioPlayer
from backend.hardware.timing_store import TimingStore
from backend.logging_config import setup_logging
from backend.services.bear_service import BearService

logger = logging.getLogger(__name__)


async def async_main() -> None:
    """Async entry point: wire up services and run CLI."""
    settings = get_settings()

    setup_logging(level="DEBUG" if settings.debug else "INFO")

    logger.info("Starting Raspi Ruxpin CLI...")

    # Create services
    arduino = ArduinoController(
        port=settings.serial.port,
        baud_rate=settings.serial.baud_rate,
        timeout=settings.serial.timeout,
        connect_timeout=settings.serial.connect_timeout,
        use_mock=settings.serial.use_mock,
    )

    audio_player = AudioPlayer(
        sample_rate=settings.audio.sample_rate,
        amplitude_threshold=settings.audio.amplitude_threshold,
        sounds_dir=settings.audio.sounds_dir,
        tts_output_dir=settings.tts.output_dir,
        tts_engine=settings.tts.engine,
        tts_voice=settings.tts.voice,
        tts_speed=settings.tts.speed,
        tts_pitch=settings.tts.pitch,
        start_volume=settings.audio.start_volume,
        alsa_device=settings.audio.device,
        alsa_card_index=settings.audio.card_index,
        alsa_mixer=settings.audio.mixer,
    )

    timing_store = TimingStore(timing_dir=settings.sync.timing_dir)

    bear_service = BearService(
        settings=settings,
        arduino=arduino,
        audio_player=audio_player,
        timing_store=timing_store,
    )

    try:
        await bear_service.start()
        logger.info("Bear service started")

        cli = RuxpinCLI(bear_service=bear_service, settings=settings)
        await cli.run()

    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        logger.info("Shutting down...")
        await bear_service.stop()
        logger.info("Goodbye.")


def main() -> None:
    """Synchronous entry point for console_scripts."""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
