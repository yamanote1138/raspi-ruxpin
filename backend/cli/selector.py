"""Interactive arrow-key file selector for terminal use.

Provides a full-screen file selector with fuzzy search, arrow-key navigation,
windowed scrolling, and color-coded display. Ported from ruxpin-cli's
interactive_file_selector, adapted for async.
"""

from collections.abc import Callable
from pathlib import Path

from backend.cli.terminal import Colors, agetch, clear_screen


def _fuzzy_filter(query: str, items: list[Path], labels: dict[Path, str]) -> list[Path]:
    """Return items whose label contains query (case-insensitive)."""
    if not query:
        return list(items)
    q = query.lower()
    return [item for item in items if q in labels[item].lower()]


async def interactive_file_selector(
    files: list[Path],
    prompt: str = "Select Audio File",
    title_fn: Callable[[Path], str | None] | None = None,
) -> Path | None:
    """Arrow-key file selector with fuzzy search and windowed scrolling.

    Args:
        files: List of file paths to choose from.
        prompt: Header text displayed at the top.
        title_fn: Optional callable that returns a display title for a file.

    Returns:
        Selected Path, or None if cancelled.
    """
    if not files:
        print("No files available.")
        return None

    # Build display labels: "stem — title" or just "stem"
    labels: dict[Path, str] = {}
    for f in files:
        title = title_fn(f) if title_fn else None
        labels[f] = f"{f.stem} — {title}" if title else f.stem

    search_query = ""
    selected_idx = 0
    filtered = list(files)

    while True:
        clear_screen()

        # Header
        print(Colors.separator())
        print(f"   {Colors.header(prompt)}")
        print(Colors.separator())
        print()
        print(
            f"{Colors.GRAY}Type to search, ↑/↓ to select, "
            f"Enter to confirm, ESC or 'q' to cancel{Colors.RESET}"
        )
        print()
        print(f"{Colors.prompt('Search:')} {Colors.CYAN}{search_query}_{Colors.RESET}")
        print(Colors.separator("-"))

        # Show filtered results in a 15-item window
        if not filtered:
            print(f"\n  {Colors.GRAY}No matches found{Colors.RESET}")
        else:
            window_size = 15
            display_start = max(0, selected_idx - window_size // 2)
            display_end = min(len(filtered), display_start + window_size)
            # Adjust start if we're near the end
            if display_end - display_start < window_size:
                display_start = max(0, display_end - window_size)

            for i in range(display_start, display_end):
                f = filtered[i]
                label = labels[f]
                file_size = f.stat().st_size / 1024

                if i == selected_idx:
                    prefix = f"{Colors.CYAN}→ "
                    name = f"{Colors.BOLD}{label}{Colors.RESET}"
                    print(f"{prefix}{name:<54} {Colors.YELLOW}{file_size:>6.1f} KB{Colors.RESET}")
                else:
                    print(f"  {label:<45} {Colors.GRAY}{file_size:>6.1f} KB{Colors.RESET}")

        print()
        print(f"{Colors.GRAY}Showing {len(filtered)} of {len(files)} files{Colors.RESET}")

        # Get key
        key = await agetch()

        # ESC (standalone) — cancel
        if key == "\x1b":
            return None

        # Arrow keys
        if key == "\x1b[A":  # Up
            if filtered and selected_idx > 0:
                selected_idx -= 1
        elif key == "\x1b[B":  # Down
            if filtered and selected_idx < len(filtered) - 1:
                selected_idx += 1

        # Enter — select
        elif key in ("\r", "\n"):
            if filtered:
                return filtered[selected_idx]
            return None

        # Backspace — delete search char
        elif key in ("\x7f", "\x08"):
            if search_query:
                search_query = search_query[:-1]
                filtered = _fuzzy_filter(search_query, files, labels)
                selected_idx = min(selected_idx, max(0, len(filtered) - 1))

        # Ctrl+C — raise
        elif key == "\x03":
            raise KeyboardInterrupt

        # q/Q — cancel (only when not mid-search)
        elif key.lower() == "q" and not search_query:
            return None

        # Printable character — append to search
        elif len(key) == 1 and key.isprintable():
            search_query += key
            filtered = _fuzzy_filter(search_query, files, labels)
            selected_idx = 0
