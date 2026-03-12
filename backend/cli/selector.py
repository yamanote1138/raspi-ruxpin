"""Interactive file selector for terminal use.

Provides a simple text-based file selection with filtering. Ported from
ruxpin-cli's interactive_file_selector, simplified for asyncio.
"""

import asyncio
from collections.abc import Callable
from pathlib import Path


async def interactive_file_selector(
    files: list[Path],
    prompt: str = "Select a file",
    title_fn: Callable[[Path], str | None] | None = None,
) -> Path | None:
    """Present a numbered list of files and let the user choose one.

    Supports filtering by typing a search string, or entering a number
    to select directly.

    Args:
        files: List of file paths to choose from.
        prompt: Header text.
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

    filtered = list(files)
    filter_text = ""

    while True:
        # Display filtered list
        print(f"\n--- {prompt} ---")
        if filter_text:
            print(f"  Filter: '{filter_text}'")

        display_files = filtered[:20]  # Show at most 20
        for i, f in enumerate(display_files, 1):
            print(f"  {i:3d}. {labels[f]}")

        if len(filtered) > 20:
            print(f"  ... and {len(filtered) - 20} more (type to filter)")

        print(f"  Total: {len(filtered)} files")
        print("  Enter number to select, text to filter, or 'q' to cancel")

        choice = await asyncio.to_thread(input, "> ")

        if choice.lower() in ("q", "quit", "cancel", ""):
            return None

        # Try as number
        try:
            idx = int(choice)
            if 1 <= idx <= len(display_files):
                return display_files[idx - 1]
            else:
                print("Number out of range.")
                continue
        except ValueError:
            pass

        # Use as filter (searches both stem and title)
        filter_text = choice.lower()
        filtered = [f for f in files if filter_text in labels[f].lower()]

        if not filtered:
            print(f"No matches for '{filter_text}'. Clearing filter.")
            filter_text = ""
            filtered = list(files)
