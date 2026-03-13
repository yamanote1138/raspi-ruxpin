"""Interactive CLI menu for Raspi Ruxpin.

Provides a terminal-based interface for controlling the bear, playing audio,
TTS, and adjusting settings. Ported from ruxpin-cli's audio_sync_cli.py.
"""

import asyncio
import logging
import wave
from pathlib import Path

from mutagen.id3 import TIT2  # type: ignore[attr-defined]
from mutagen.wave import WAVE

from backend.cli.audio_quality import analyze_wav_quality
from backend.cli.selector import interactive_file_selector
from backend.cli.terminal import Colors, agetch, clear_screen
from backend.config import AppSettings
from backend.core.enums import SyncMode
from backend.hardware.audio_player import AudioPlayer
from backend.services.bear_service import BearService

logger = logging.getLogger(__name__)

# Grade-to-color mapping for quality scores
_GRADE_COLORS: dict[str, str] = {
    "Excellent": Colors.GREEN,
    "Good": Colors.CYAN,
    "Fair": Colors.YELLOW,
    "Poor": Colors.RED,
}


def _grade_color(grade: str) -> str:
    """Return the ANSI color code for a quality grade."""
    return _GRADE_COLORS.get(grade, Colors.RESET)


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
        while self._running:
            self._print_main_menu()

            key = await agetch()

            # ESC — quit
            if key == "\x1b":
                self._running = False
                print(f"\n{Colors.header('Goodbye!')}")
                return

            choice = key.upper()

            if choice == "P":
                await self._play_audio()
            elif choice == "T":
                await self._speak_text()
            elif choice == "M":
                await self._manage_sounds()
            elif choice == "S":
                await self._settings_menu()
            elif choice == "Q":
                self._running = False
                print(f"\n{Colors.header('Goodbye!')}")
            elif choice == "\x03":  # Ctrl+C
                raise KeyboardInterrupt
            else:
                pass  # Ignore invalid keys silently; menu redraws

    def _print_main_menu(self) -> None:
        """Print the main menu with colors and status."""
        clear_screen()

        mode = self.bear_service.sync_mode.value
        vol = self.bear_service.audio_player.volume
        connected = (
            f"{Colors.GREEN}yes{Colors.RESET}"
            if self.bear_service.arduino.connected
            else f"{Colors.RED}no{Colors.RESET}"
        )

        print(Colors.separator())
        print(f"   {Colors.header('Raspi Ruxpin CLI')}")
        print(Colors.separator())
        print()
        print(
            f"{Colors.GRAY}Settings: "
            f"{Colors.YELLOW}Mode={mode}{Colors.GRAY}, "
            f"{Colors.YELLOW}Vol={vol}%{Colors.GRAY}, "
            f"Arduino={connected}"
        )
        print()
        print(f"  {Colors.CYAN}P{Colors.RESET}. Play audio file")
        print(f"  {Colors.CYAN}T{Colors.RESET}. Speak text (TTS)")
        print(f"  {Colors.CYAN}M{Colors.RESET}. Manage sound files")
        print(f"  {Colors.CYAN}S{Colors.RESET}. Settings")
        print(f"  {Colors.CYAN}Q{Colors.RESET}. Quit (or ESC)")
        print()
        print(Colors.prompt("Select option: "), end="", flush=True)

    async def _play_audio(self) -> None:
        """Browse and play an audio file."""
        player = self.bear_service.audio_player
        wav_files = self._collect_wav_files(player)

        if not wav_files:
            print(Colors.warning(f"No .wav files found in {player.sounds_dir}"))
            await self._pause()
            return

        selected = await interactive_file_selector(
            wav_files, title_fn=AudioPlayer.read_wav_title
        )
        if selected is None:
            return

        print()
        print(f"{Colors.GREEN}>>> Playing: {Colors.CYAN}{selected.name}{Colors.RESET}")
        try:
            await self.bear_service.play_audio(selected.stem)
            print(Colors.success("Done."))
        except Exception as e:
            print(Colors.error(f"Error: {e}"))

        await self._pause()

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
        clear_screen()
        print(Colors.separator())
        print(f"   {Colors.header('Text-to-Speech')}")
        print(Colors.separator())
        print()

        text = await self._get_input(Colors.prompt("Enter text to speak: "))
        if not text.strip():
            return

        print(f"\n{Colors.GREEN}>>> Speaking: {Colors.CYAN}{text}{Colors.RESET}")
        try:
            await self.bear_service.speak(text)
            print(Colors.success("Done."))
        except Exception as e:
            print(Colors.error(f"Error: {e}"))

        await self._pause()

    async def _settings_menu(self) -> None:
        """Settings submenu with single-keypress navigation."""
        while True:
            clear_screen()

            mode = self.bear_service.sync_mode.value
            vol = self.bear_service.audio_player.volume
            blink = "on" if self.bear_service.blink_enabled else "off"

            print(Colors.separator())
            print(f"   {Colors.header('Settings & Configuration')}")
            print(Colors.separator())
            print()
            print(
                f"{Colors.GRAY}Current: "
                f"{Colors.YELLOW}Mode={mode}{Colors.GRAY}, "
                f"{Colors.YELLOW}Vol={vol}%{Colors.GRAY}, "
                f"{Colors.YELLOW}Blink={blink}{Colors.RESET}"
            )
            print()
            print(f"  {Colors.CYAN}V{Colors.RESET}. Set volume (current: {Colors.YELLOW}{vol}%{Colors.RESET})")
            print(f"  {Colors.CYAN}M{Colors.RESET}. Set sync mode (current: {Colors.YELLOW}{mode}{Colors.RESET})")
            print(f"  {Colors.CYAN}B{Colors.RESET}. Toggle blink ({Colors.YELLOW}{blink}{Colors.RESET})")
            print(f"  {Colors.CYAN}E{Colors.RESET}. Test eyes")
            print(f"  {Colors.CYAN}T{Colors.RESET}. Test mouth positions")
            print()
            print(f"  {Colors.CYAN}Q{Colors.RESET}. Back to main menu (or ESC)")
            print()
            print(Colors.prompt("Select option: "), end="", flush=True)

            key = await agetch()

            # ESC — back
            if key == "\x1b":
                return

            choice = key.upper()

            if choice == "Q":
                return
            elif choice == "V":
                await self._set_volume()
            elif choice == "M":
                await self._set_sync_mode()
            elif choice == "B":
                enabled = not self.bear_service.blink_enabled
                self.bear_service.set_blink_enabled(enabled)
                print(f"\n{Colors.success(f'Blink {'enabled' if enabled else 'disabled'}')}")
                await self._pause()
            elif choice == "E":
                await self._test_eyes()
            elif choice == "T":
                await self._test_mouth()
            elif choice == "\x03":  # Ctrl+C
                raise KeyboardInterrupt

    async def _manage_sounds(self) -> None:
        """Sub-menu for sound file management."""
        while True:
            clear_screen()
            print(Colors.separator())
            print(f"   {Colors.header('Manage Sound Files')}")
            print(Colors.separator())
            print()
            print(f"  {Colors.CYAN}T{Colors.RESET}. Add/edit titles")
            print(f"  {Colors.CYAN}F{Colors.RESET}. Check file format")
            print(f"  {Colors.CYAN}A{Colors.RESET}. Audio quality analysis")
            print()
            print(f"  {Colors.CYAN}Q{Colors.RESET}. Back (or ESC)")
            print()
            print(Colors.prompt("Select option: "), end="", flush=True)

            key = await agetch()
            if key == "\x1b" or key.upper() == "Q":
                return
            if key.upper() == "T":
                await self._manage_titles()
            elif key.upper() == "F":
                await self._check_format()
            elif key.upper() == "A":
                await self._check_quality()
            elif key == "\x03":
                raise KeyboardInterrupt

    async def _manage_titles(self) -> None:
        """Browse and edit WAV file titles.

        Shows all WAV files (examples + user). Example files are read-only;
        user files can be edited.
        """
        player = self.bear_service.audio_player
        user_dir = player.sounds_dir / "user"
        all_wav_files = self._collect_wav_files(player)

        if not all_wav_files:
            print(Colors.warning("No WAV files found."))
            await self._pause()
            return

        # Only user/ files are editable
        user_files = [f for f in all_wav_files if f.parent == user_dir]
        untitled = [w for w in user_files if not AudioPlayer.read_wav_title(w)]

        while True:
            # Offer "title all untitled" option if applicable
            if untitled:
                clear_screen()
                print(Colors.separator())
                print(f"   {Colors.header('Sound Titles')}")
                print(Colors.separator())
                print()
                print(
                    f"  {Colors.YELLOW}{len(untitled)}{Colors.RESET} user file(s) without titles."
                )
                print()
                print(f"  {Colors.CYAN}A{Colors.RESET}. Title all untitled user files")
                print(f"  {Colors.CYAN}S{Colors.RESET}. Browse all files")
                print(f"  {Colors.CYAN}Q{Colors.RESET}. Back (or ESC)")
                print()
                print(Colors.prompt("Select option: "), end="", flush=True)

                key = await agetch()
                if key == "\x1b" or key.upper() == "Q":
                    return
                if key.upper() == "A":
                    for wav in untitled:
                        title = await self._prompt_title(wav)
                        if title is not None:
                            self._write_wav_title(wav, title)
                    # Refresh untitled list
                    untitled = [w for w in user_files if not AudioPlayer.read_wav_title(w)]
                    continue
                if key.upper() != "S":
                    continue

            # Label: "stem — title" with [example] or [no title] markers
            def _title_label(path: Path) -> str | None:
                title = AudioPlayer.read_wav_title(path)
                if path.parent != user_dir:
                    return f"{title} [example]" if title else "[example]"
                return title if title else "[no title]"

            selected = await interactive_file_selector(
                all_wav_files, prompt="Sound Titles", title_fn=_title_label
            )
            if selected is None:
                return

            # Example files: view only
            if selected.parent != user_dir:
                clear_screen()
                title = AudioPlayer.read_wav_title(selected)
                print()
                print(f"  File: {Colors.CYAN}{selected.stem}{Colors.RESET}")
                if title:
                    print(f"  Title: {Colors.GREEN}{title}{Colors.RESET}")
                else:
                    print(f"  {Colors.GRAY}No title set.{Colors.RESET}")
                print(f"\n  {Colors.GRAY}Example files are read-only.{Colors.RESET}")
                await self._pause()
                continue

            # User files: edit
            title = await self._prompt_title(selected)
            if title is not None:
                self._write_wav_title(selected, title)
                # Refresh untitled list
                untitled = [w for w in user_files if not AudioPlayer.read_wav_title(w)]

    async def _check_format(self) -> None:
        """Check format of individual or all user WAV files."""
        player = self.bear_service.audio_player
        user_dir = player.sounds_dir / "user"
        user_files = sorted(user_dir.glob("*.wav")) if user_dir.is_dir() else []
        all_wav_files = self._collect_wav_files(player)

        if not all_wav_files:
            print(Colors.warning("No WAV files found."))
            await self._pause()
            return

        # Offer scan-all option if user files exist
        if user_files:
            clear_screen()
            print(Colors.separator())
            print(f"   {Colors.header('Check File Format')}")
            print(Colors.separator())
            print()
            print(f"  {Colors.CYAN}A{Colors.RESET}. Scan all user files ({len(user_files)})")
            print(f"  {Colors.CYAN}S{Colors.RESET}. Select a single file")
            print(f"  {Colors.CYAN}Q{Colors.RESET}. Back (or ESC)")
            print()
            print(Colors.prompt("Select option: "), end="", flush=True)

            key = await agetch()
            if key == "\x1b" or key.upper() == "Q":
                return
            if key.upper() == "A":
                await self._scan_all_formats(user_files)
                return
            if key.upper() != "S":
                return

        selected = await interactive_file_selector(
            all_wav_files, prompt="Check File Format", title_fn=AudioPlayer.read_wav_title
        )
        if selected is None:
            return

        clear_screen()
        print(Colors.separator())
        print(f"   {Colors.header('File Format')}")
        print(Colors.separator())
        print()
        self._print_wav_format(selected, verbose=True)
        await self._pause()

    async def _scan_all_formats(self, wav_files: list[Path]) -> None:
        """Scan all WAV files and report a summary with any issues."""
        clear_screen()
        print(Colors.separator())
        print(f"   {Colors.header('User Sound File Scan')}")
        print(Colors.separator())
        print()

        issues: list[tuple[Path, list[str]]] = []
        rates: set[int] = set()
        depths: set[int] = set()
        total_duration = 0.0

        for wav in wav_files:
            file_warnings = self._get_wav_warnings(wav)
            if file_warnings is None:
                issues.append((wav, ["Cannot read WAV file"]))
                continue

            warnings, frame_rate, bit_depth, duration = file_warnings
            rates.add(frame_rate)
            depths.add(bit_depth)
            total_duration += duration

            if warnings:
                issues.append((wav, warnings))
            else:
                title = AudioPlayer.read_wav_title(wav)
                label = f"{wav.stem} — {title}" if title else wav.stem
                print(f"  {Colors.GREEN}✓{Colors.RESET} {label}")

        # Print issues
        if issues:
            print()
            for wav, warnings in issues:
                title = AudioPlayer.read_wav_title(wav)
                label = f"{wav.stem} — {title}" if title else wav.stem
                print(f"  {Colors.RED}✗{Colors.RESET} {label}")
                for w in warnings:
                    print(f"    {Colors.YELLOW}⚠ {w}{Colors.RESET}")

        # Summary
        print()
        print(Colors.separator("-"))
        print(
            f"  Scanned {Colors.WHITE}{len(wav_files)}{Colors.RESET} files, "
            f"total duration {Colors.WHITE}{total_duration:.1f}s{Colors.RESET}"
        )
        rates_str = ", ".join(f"{r} Hz" for r in sorted(rates))
        depths_str = ", ".join(f"{d}-bit" for d in sorted(depths))
        print(f"  Sample rates: {Colors.WHITE}{rates_str}{Colors.RESET}")
        print(f"  Bit depths:   {Colors.WHITE}{depths_str}{Colors.RESET}")
        if issues:
            print(f"\n  {Colors.YELLOW}{len(issues)} file(s) with warnings.{Colors.RESET}")
        else:
            print(f"\n  {Colors.success('All files compatible.')}")

        await self._pause()

    async def _check_quality(self) -> None:
        """Analyze audio quality of individual or all WAV files."""
        player = self.bear_service.audio_player
        all_wav_files = self._collect_wav_files(player)

        if not all_wav_files:
            print(Colors.warning("No WAV files found."))
            await self._pause()
            return

        clear_screen()
        print(Colors.separator())
        print(f"   {Colors.header('Audio Quality Analysis')}")
        print(Colors.separator())
        print()
        print(f"  {Colors.CYAN}A{Colors.RESET}. Scan all files ({len(all_wav_files)})")
        print(f"  {Colors.CYAN}S{Colors.RESET}. Select a single file")
        print(f"  {Colors.CYAN}Q{Colors.RESET}. Back (or ESC)")
        print()
        print(Colors.prompt("Select option: "), end="", flush=True)

        key = await agetch()
        if key == "\x1b" or key.upper() == "Q":
            return
        if key.upper() == "A":
            await self._scan_all_quality(all_wav_files)
            return
        if key.upper() != "S":
            return

        selected = await interactive_file_selector(
            all_wav_files, prompt="Audio Quality", title_fn=AudioPlayer.read_wav_title
        )
        if selected is None:
            return

        clear_screen()
        print(Colors.separator())
        print(f"   {Colors.header('Audio Quality')}")
        print(Colors.separator())
        print()
        self._print_wav_quality(selected)
        await self._pause()

    async def _scan_all_quality(self, wav_files: list[Path]) -> None:
        """Scan all WAV files and report quality scores."""
        clear_screen()
        print(Colors.separator())
        print(f"   {Colors.header('Audio Quality Scan')}")
        print(Colors.separator())
        print()

        scores: list[int] = []
        grade_counts: dict[str, int] = {"Excellent": 0, "Good": 0, "Fair": 0, "Poor": 0}
        poor_files: list[str] = []

        for wav in wav_files:
            title = AudioPlayer.read_wav_title(wav)
            label = f"{wav.stem} — {title}" if title else wav.stem

            try:
                report = analyze_wav_quality(wav)
                color = _grade_color(report.grade)
                print(
                    f"  {color}{report.score:3d}/100 {report.grade:<9s}{Colors.RESET} {label}"
                )
                scores.append(report.score)
                grade_counts[report.grade] += 1
                if report.grade == "Poor":
                    poor_files.append(wav.stem)
            except Exception as e:
                print(f"  {Colors.RED}  err  {Colors.RESET} {label} — {e}")

        # Summary
        print()
        print(Colors.separator("-"))
        print(f"  Scanned {Colors.WHITE}{len(wav_files)}{Colors.RESET} files")

        if scores:
            avg_score = sum(scores) // len(scores)
            print(f"  Avg score:  {Colors.WHITE}{avg_score}/100{Colors.RESET}")
            grade_parts: list[str] = []
            for grade_name in ("Excellent", "Good", "Fair", "Poor"):
                count = grade_counts[grade_name]
                if count > 0:
                    color = _grade_color(grade_name)
                    grade_parts.append(f"{color}{count} {grade_name}{Colors.RESET}")
            print(f"  Grades:     {', '.join(grade_parts)}")

        if poor_files:
            print(
                f"\n  {Colors.YELLOW}⚠ Poor quality: "
                f"{', '.join(poor_files)}{Colors.RESET}"
            )

        await self._pause()

    @staticmethod
    def _print_wav_quality(wav: Path) -> None:
        """Print quality analysis for a single WAV file."""
        print(f"  File:  {Colors.CYAN}{wav.name}{Colors.RESET}")

        title = AudioPlayer.read_wav_title(wav)
        if title:
            print(f"  Title: {Colors.GREEN}{title}{Colors.RESET}")
        print()

        try:
            report = analyze_wav_quality(wav)
            color = _grade_color(report.grade)
            print(f"  Score: {color}{report.score}/100 {report.grade}{Colors.RESET}")
            print()
            for comment in report.comments:
                print(f"    • {comment}")
            print()
            print(
                f"  {Colors.GRAY}Peak amplitude:   "
                f"{report.peak_amplitude:.3f}{Colors.RESET}"
            )
            print(
                f"  {Colors.GRAY}Mean RMS:         "
                f"{report.rms_mean:.4f}{Colors.RESET}"
            )
            print(
                f"  {Colors.GRAY}Noise floor:      "
                f"{report.noise_floor:.4f}{Colors.RESET}"
            )
            print(
                f"  {Colors.GRAY}SNR:              "
                f"{report.snr_db:.1f} dB{Colors.RESET}"
            )
            print(
                f"  {Colors.GRAY}Crest factor:     "
                f"{report.crest_factor_db:.1f} dB{Colors.RESET}"
            )
            print(
                f"  {Colors.GRAY}Position variety: "
                f"{report.position_variety}/7{Colors.RESET}"
            )
            print(
                f"  {Colors.GRAY}Activity:         "
                f"{report.activity_percent:.0f}%{Colors.RESET}"
            )
        except Exception as e:
            print(Colors.error(f"Could not analyze: {e}"))

    @staticmethod
    def _get_wav_warnings(wav: Path) -> tuple[list[str], int, int, float] | None:
        """Read a WAV file and return any compatibility warnings.

        Returns:
            Tuple of (warnings, frame_rate, bit_depth, duration), or None on read error.
        """
        compatible_rates = {16000, 22050}
        try:
            with wave.open(str(wav), "rb") as wf:
                channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                frame_rate = wf.getframerate()
                n_frames = wf.getnframes()
                duration = n_frames / frame_rate if frame_rate > 0 else 0.0
                bit_depth = sample_width * 8

                warnings: list[str] = []
                if frame_rate not in compatible_rates:
                    warnings.append(f"Sample rate {frame_rate} Hz (expected 16000 or 22050)")
                if channels != 1:
                    ch_label = "stereo" if channels == 2 else f"{channels}ch"
                    warnings.append(f"{ch_label} (mono required)")
                if bit_depth != 16:
                    warnings.append(f"{bit_depth}-bit (16-bit expected)")
                return warnings, frame_rate, bit_depth, duration
        except Exception:
            return None

    @staticmethod
    def _print_wav_format(wav: Path, *, verbose: bool = False) -> None:
        """Print format details for a single WAV file."""
        print(f"  File:   {Colors.CYAN}{wav.name}{Colors.RESET}")
        print(f"  Path:   {Colors.GRAY}{wav.parent}{Colors.RESET}")

        title = AudioPlayer.read_wav_title(wav)
        if title:
            print(f"  Title:  {Colors.GREEN}{title}{Colors.RESET}")

        file_size = wav.stat().st_size
        if file_size >= 1024 * 1024:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
        else:
            size_str = f"{file_size / 1024:.1f} KB"
        print(f"  Size:   {Colors.YELLOW}{size_str}{Colors.RESET}")
        print()

        try:
            with wave.open(str(wav), "rb") as wf:
                channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                frame_rate = wf.getframerate()
                n_frames = wf.getnframes()
                duration = n_frames / frame_rate if frame_rate > 0 else 0.0

                ch_label = "mono" if channels == 1 else "stereo" if channels == 2 else f"{channels}ch"
                bit_depth = sample_width * 8

                print(f"  Codec:       {Colors.WHITE}PCM (WAV){Colors.RESET}")
                print(f"  Channels:    {Colors.WHITE}{channels} ({ch_label}){Colors.RESET}")
                print(f"  Bit depth:   {Colors.WHITE}{bit_depth}-bit{Colors.RESET}")
                print(f"  Sample rate: {Colors.WHITE}{frame_rate} Hz{Colors.RESET}")
                print(f"  Duration:    {Colors.WHITE}{duration:.2f}s{Colors.RESET}")
                if verbose:
                    print(f"  Frames:      {Colors.GRAY}{n_frames:,}{Colors.RESET}")

                # Compatibility notes
                compatible_rates = {16000, 22050}
                warnings_found = False
                print()
                if frame_rate not in compatible_rates:
                    print(Colors.warning(
                        f"Sample rate is {frame_rate} Hz "
                        f"(expected 16000 or 22050 Hz)"
                    ))
                    warnings_found = True
                if channels != 1:
                    print(Colors.warning(f"File is {ch_label} (mono required)"))
                    warnings_found = True
                if bit_depth != 16:
                    print(Colors.warning(f"Bit depth is {bit_depth}-bit (16-bit expected)"))
                    warnings_found = True
                if not warnings_found:
                    print(Colors.success("Format is compatible."))

        except wave.Error as e:
            print(Colors.error(f"Cannot read WAV: {e}"))
        except Exception as e:
            print(Colors.error(f"Error: {e}"))

    async def _prompt_title(self, wav: Path) -> str | None:
        """Prompt the user for a title for the given WAV file.

        Returns:
            The title string, or None if skipped.
        """
        current = AudioPlayer.read_wav_title(wav)
        if current:
            print(f"\n  File: {Colors.CYAN}{wav.stem}{Colors.RESET}")
            print(f"  Current title: {Colors.GREEN}{current}{Colors.RESET}")
        else:
            print(f"\n  File: {Colors.CYAN}{wav.stem}{Colors.RESET}")
            print(f"  {Colors.GRAY}No title set.{Colors.RESET}")

        title = await self._get_input(Colors.prompt("  New title (enter to skip): "))
        if not title.strip():
            return None
        return title.strip()

    @staticmethod
    def _write_wav_title(wav: Path, title: str) -> None:
        """Write a title to a WAV file's ID3 metadata."""
        try:
            w = WAVE(str(wav))  # type: ignore[no-untyped-call]
            if w.tags is None:
                w.add_tags()  # type: ignore[no-untyped-call]
            assert w.tags is not None
            w.tags.delall("TIT2")
            w.tags.add(TIT2(encoding=3, text=[title]))
            w.save()
            print(Colors.success(f"Saved: {wav.stem} — {title}"))
        except Exception as e:
            print(Colors.error(f"Error writing title: {e}"))

    async def _set_volume(self) -> None:
        """Set volume level."""
        print()
        current = self.bear_service.audio_player.volume
        print(Colors.info(f"Current volume: {current}%"))
        level_str = await self._get_input(Colors.prompt("Volume (0-90): "))
        try:
            level = int(level_str)
            await self.bear_service.set_volume(level)
            print(Colors.success(f"Volume set to {level}%"))
        except ValueError:
            print(Colors.error("Invalid number."))
        except Exception as e:
            print(Colors.error(f"Error: {e}"))
        await self._pause()

    async def _set_sync_mode(self) -> None:
        """Switch sync mode via single keypress."""
        print()
        print(f"\n  {Colors.CYAN}1{Colors.RESET}. Amplitude (Pi pre-analyzes WAV)")
        print(f"  {Colors.CYAN}2{Colors.RESET}. Phoneme (Pi Whisper + phonemizer)")
        print(f"  {Colors.CYAN}3{Colors.RESET}. Realtime (Arduino ADC)")
        print()
        print(Colors.prompt("Select mode: "), end="", flush=True)

        key = await agetch()
        print()

        if key == "1":
            await self.bear_service.set_sync_mode(SyncMode.AMPLITUDE)
            print(Colors.success("Mode: amplitude"))
        elif key == "2":
            await self.bear_service.set_sync_mode(SyncMode.PHONEME)
            print(Colors.success("Mode: phoneme"))
        elif key == "3":
            await self.bear_service.set_sync_mode(SyncMode.REALTIME)
            print(Colors.success("Mode: realtime"))
        else:
            print(Colors.warning("Cancelled."))

        await self._pause()

    async def _test_eyes(self) -> None:
        """Test eye movements."""
        print()
        print(Colors.info("Testing eyes..."))
        print("  Opening eyes...")
        await self.bear_service.arduino.open_eyes()
        await asyncio.sleep(1.0)
        print("  Closing eyes...")
        await self.bear_service.arduino.close_eyes()
        await asyncio.sleep(0.5)
        print("  Blinking...")
        await self.bear_service.arduino.blink_eyes()
        await asyncio.sleep(1.0)
        print("  Opening eyes...")
        await self.bear_service.arduino.open_eyes()
        print(Colors.success("Done."))
        await self._pause()

    async def _test_mouth(self) -> None:
        """Cycle through all 7 mouth positions."""
        from backend.core.enums import MouthPosition

        print()
        print(Colors.info("Testing mouth positions..."))
        for pos in MouthPosition:
            print(f"  Position: {Colors.CYAN}{pos.value}{Colors.RESET}")
            await self.bear_service.arduino.set_mouth_position(pos)
            await asyncio.sleep(0.5)

        await self.bear_service.arduino.set_mouth_position(MouthPosition.C)
        print(Colors.success("Done."))
        await self._pause()

    @staticmethod
    async def _get_input(prompt: str) -> str:
        """Get user input without blocking the event loop."""
        return await asyncio.to_thread(input, prompt)

    @staticmethod
    async def _pause() -> None:
        """Wait for the user to press any key."""
        print()
        print(Colors.prompt("Press any key to continue..."), end="", flush=True)
        await agetch()
