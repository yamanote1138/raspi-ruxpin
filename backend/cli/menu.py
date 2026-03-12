"""Interactive CLI menu for Raspi Ruxpin.

Provides a terminal-based interface for controlling the bear, playing audio,
TTS, and adjusting settings. Ported from ruxpin-cli's audio_sync_cli.py.
"""

import asyncio
import logging
from pathlib import Path

from mutagen.id3 import TIT2
from mutagen.wave import WAVE

from backend.cli.selector import interactive_file_selector
from backend.config import AppSettings
from backend.core.enums import SyncMode
from backend.hardware.audio_player import AudioPlayer
from backend.services.bear_service import BearService

logger = logging.getLogger(__name__)


class RuxpinCLI:
    """Interactive terminal menu for bear control.

    Attributes:
        bear_service: The bear service instance.
        settings: Application settings.
    """

    def __init__(self, bear_service: BearService, settings: AppSettings) -> None:
        self.bear_service = bear_service
        self.settings = settings
        self._running = True

    async def run(self) -> None:
        """Run the main menu loop."""
        print("\n" + "=" * 50)
        print("  Raspi Ruxpin CLI")
        print("=" * 50)

        while self._running:
            self._print_main_menu()
            choice = await self._get_input("> ")

            if choice == "1":
                await self._play_audio()
            elif choice == "2":
                await self._speak_text()
            elif choice == "3":
                await self._settings_menu()
            elif choice in ("4", "q", "quit", "exit"):
                self._running = False
                print("Exiting...")
            else:
                print("Invalid choice.")

    def _print_main_menu(self) -> None:
        """Print the main menu."""
        mode = self.bear_service.sync_mode.value
        vol = self.bear_service.audio_player.volume
        connected = "yes" if self.bear_service.arduino.connected else "no"

        print(f"\n--- Main Menu [mode: {mode} | vol: {vol}% | arduino: {connected}] ---")
        print("  1. Play audio file")
        print("  2. Speak text (TTS)")
        print("  3. Settings")
        print("  4. Quit")

    async def _play_audio(self) -> None:
        """Browse and play an audio file."""
        player = self.bear_service.audio_player
        wav_files = self._collect_wav_files(player)

        if not wav_files:
            print(f"No .wav files found in {player.sounds_dir}")
            return

        selected = await interactive_file_selector(
            wav_files, title_fn=AudioPlayer.read_wav_title
        )
        if selected is None:
            return

        print(f"Playing: {selected.name}")
        try:
            await self.bear_service.play_audio(selected.stem)
            print("Done.")
        except Exception as e:
            print(f"Error: {e}")

    @staticmethod
    def _collect_wav_files(player: AudioPlayer) -> list[Path]:
        """Collect all WAV files from examples/ and user/ subdirectories."""
        wav_files: list[Path] = []
        for subdir in ("examples", "user"):
            subdir_path = player.sounds_dir / subdir
            if subdir_path.is_dir():
                wav_files.extend(sorted(subdir_path.glob("*.wav")))
        return wav_files

    async def _speak_text(self) -> None:
        """Get text input and speak it."""
        text = await self._get_input("Enter text to speak: ")
        if not text.strip():
            return

        print("Speaking...")
        try:
            await self.bear_service.speak(text)
            print("Done.")
        except Exception as e:
            print(f"Error: {e}")

    async def _settings_menu(self) -> None:
        """Settings submenu."""
        while True:
            mode = self.bear_service.sync_mode.value
            vol = self.bear_service.audio_player.volume

            print(f"\n--- Settings [mode: {mode} | vol: {vol}%] ---")
            print("  1. Set volume")
            print("  2. Set sync mode")
            print(f"  3. Toggle blink ({'on' if self.bear_service.blink_enabled else 'off'})")
            print("  4. Test eyes")
            print("  5. Test mouth positions")
            print("  6. Manage sound titles")
            print("  7. Back")

            choice = await self._get_input("> ")

            if choice == "1":
                await self._set_volume()
            elif choice == "2":
                await self._set_sync_mode()
            elif choice == "3":
                enabled = not self.bear_service.blink_enabled
                self.bear_service.set_blink_enabled(enabled)
                print(f"Blink {'enabled' if enabled else 'disabled'}")
            elif choice == "4":
                await self._test_eyes()
            elif choice == "5":
                await self._test_mouth()
            elif choice == "6":
                await self._manage_titles()
            elif choice in ("7", "b", "back"):
                break

    async def _manage_titles(self) -> None:
        """Manage WAV file titles in the user sounds directory."""
        player = self.bear_service.audio_player
        user_dir = player.sounds_dir / "user"

        if not user_dir.is_dir():
            print("No user sounds directory found.")
            return

        while True:
            wav_files = sorted(user_dir.glob("*.wav"))
            if not wav_files:
                print("No WAV files in user directory.")
                return

            # Show files with current titles
            untitled = []
            print("\n--- Sound Titles (user/) ---")
            for i, wav in enumerate(wav_files, 1):
                title = AudioPlayer.read_wav_title(wav)
                if title:
                    print(f"  {i:3d}. {wav.stem} — {title}")
                else:
                    print(f"  {i:3d}. {wav.stem} [no title]")
                    untitled.append(wav)

            if untitled:
                print(f"\n  {len(untitled)} file(s) without titles.")

            print("\n  Enter number to edit, 'a' to title all untitled, or 'q' to go back")
            choice = await self._get_input("> ")

            if choice.lower() in ("q", "quit", "back", ""):
                break

            if choice.lower() == "a":
                for wav in untitled:
                    title = await self._prompt_title(wav)
                    if title is not None:
                        self._write_wav_title(wav, title)
                continue

            try:
                idx = int(choice)
                if 1 <= idx <= len(wav_files):
                    wav = wav_files[idx - 1]
                    title = await self._prompt_title(wav)
                    if title is not None:
                        self._write_wav_title(wav, title)
                else:
                    print("Number out of range.")
            except ValueError:
                print("Invalid input.")

    async def _prompt_title(self, wav: Path) -> str | None:
        """Prompt the user for a title for the given WAV file.

        Returns:
            The title string, or None if skipped.
        """
        current = AudioPlayer.read_wav_title(wav)
        if current:
            print(f"\n  File: {wav.stem}")
            print(f"  Current title: {current}")
        else:
            print(f"\n  File: {wav.stem}")
            print("  No title set.")

        title = await self._get_input("  New title (enter to skip): ")
        if not title.strip():
            return None
        return title.strip()

    @staticmethod
    def _write_wav_title(wav: Path, title: str) -> None:
        """Write a title to a WAV file's ID3 metadata."""
        try:
            w = WAVE(str(wav))
            if w.tags is None:
                w.add_tags()
            w.tags.delall("TIT2")
            w.tags.add(TIT2(encoding=3, text=[title]))
            w.save()
            print(f"  Saved: {wav.stem} — {title}")
        except Exception as e:
            print(f"  Error writing title: {e}")

    async def _set_volume(self) -> None:
        """Set volume level."""
        level_str = await self._get_input("Volume (0-90): ")
        try:
            level = int(level_str)
            await self.bear_service.set_volume(level)
            print(f"Volume set to {level}%")
        except ValueError:
            print("Invalid number.")
        except Exception as e:
            print(f"Error: {e}")

    async def _set_sync_mode(self) -> None:
        """Switch sync mode."""
        print("  1. Amplitude (Arduino ADC)")
        print("  2. Phoneme (Pi pre-computed)")
        choice = await self._get_input("> ")

        if choice == "1":
            await self.bear_service.set_sync_mode(SyncMode.AMPLITUDE)
            print("Mode: amplitude")
        elif choice == "2":
            await self.bear_service.set_sync_mode(SyncMode.PHONEME)
            print("Mode: phoneme")

    async def _test_eyes(self) -> None:
        """Test eye movements."""
        print("Opening eyes...")
        await self.bear_service.arduino.open_eyes()
        await asyncio.sleep(1.0)
        print("Closing eyes...")
        await self.bear_service.arduino.close_eyes()
        await asyncio.sleep(0.5)
        print("Blinking...")
        await self.bear_service.arduino.blink_eyes()
        await asyncio.sleep(1.0)
        print("Opening eyes...")
        await self.bear_service.arduino.open_eyes()
        print("Done.")

    async def _test_mouth(self) -> None:
        """Cycle through all 7 mouth positions."""
        from backend.core.enums import MouthPosition

        for pos in MouthPosition:
            print(f"  Position: {pos.value}")
            await self.bear_service.arduino.set_mouth_position(pos)
            await asyncio.sleep(0.5)

        await self.bear_service.arduino.set_mouth_position(MouthPosition.C)
        print("Done.")

    @staticmethod
    async def _get_input(prompt: str) -> str:
        """Get user input without blocking the event loop."""
        return await asyncio.to_thread(input, prompt)
