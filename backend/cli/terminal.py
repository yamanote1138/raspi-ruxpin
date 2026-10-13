"""Terminal utilities: ANSI colors and raw-mode keypress input.

Ported from ruxpin-cli's audio_sync_cli.py with async support added.
"""

import asyncio
import sys
import termios
import tty


class Colors:
    """ANSI color codes and formatting helpers for terminal output."""

    # Primary colors
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RED = "\033[91m"

    # Secondary colors
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"

    # Text formatting
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    @staticmethod
    def header(text: str) -> str:
        """Format header text in bold green."""
        return f"{Colors.BOLD}{Colors.GREEN}{text}{Colors.RESET}"

    @staticmethod
    def separator(char: str = "=", width: int = 60) -> str:
        """Format a separator line in gray."""
        return f"{Colors.GRAY}{char * width}{Colors.RESET}"

    @staticmethod
    def highlight(text: str) -> str:
        """Format highlighted/selected text in cyan."""
        return f"{Colors.CYAN}{text}{Colors.RESET}"

    @staticmethod
    def prompt(text: str) -> str:
        """Format prompt text in yellow."""
        return f"{Colors.YELLOW}{text}{Colors.RESET}"

    @staticmethod
    def success(text: str) -> str:
        """Format success message with green checkmark."""
        return f"{Colors.GREEN}✓ {text}{Colors.RESET}"

    @staticmethod
    def warning(text: str) -> str:
        """Format warning message with yellow icon."""
        return f"{Colors.YELLOW}⚠ {text}{Colors.RESET}"

    @staticmethod
    def error(text: str) -> str:
        """Format error message with red icon."""
        return f"{Colors.RED}✗ {text}{Colors.RESET}"

    @staticmethod
    def info(text: str) -> str:
        """Format info text in blue."""
        return f"{Colors.BLUE}{text}{Colors.RESET}"


def getch() -> str:
    """Get a single character from stdin without echo.

    Handles ESC key vs arrow keys using VMIN/VTIME:
    - Standalone ESC returns after 100ms timeout.
    - Arrow keys (ESC sequences) are read as complete sequences.
    """
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch: str = sys.stdin.read(1)

        if ch == "\x1b":
            # Use 100ms timeout to distinguish ESC from arrow sequences
            new_settings: list[int | list[bytes | int]] = termios.tcgetattr(fd)
            cc = new_settings[6]
            assert isinstance(cc, list)
            cc[termios.VMIN] = 0
            cc[termios.VTIME] = 1
            termios.tcsetattr(fd, termios.TCSANOW, new_settings)

            next_chars: str = sys.stdin.read(2)
            if next_chars:
                ch += next_chars

        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


async def agetch() -> str:
    """Async wrapper around getch() — runs in a thread to avoid blocking."""
    return await asyncio.to_thread(getch)


def clear_screen() -> None:
    """Clear the terminal screen and move cursor to top-left."""
    print("\033[2J\033[H", end="")
