from __future__ import annotations
import shutil
from typing import List
from rich.console import Console

console = Console(highlight=False)

BLOCK_WIDTH = 60
DOUBLE_LINE = "═" * BLOCK_WIDTH
SINGLE_LINE = "─" * BLOCK_WIDTH


def get_terminal_width() -> int:
    cols, _ = shutil.get_terminal_size((80, 24))
    return cols


def get_block_padding(block_width: int = BLOCK_WIDTH) -> str:
    cols = get_terminal_width()
    pad = (cols - block_width) // 2
    if pad < 2:
        pad = 2
    return " " * pad


def format_header_60(title: str, subtitle: str = "") -> List[str]:
    """Generates a strictly centered 60-character block header."""
    lines = [
        f"[bold sky_blue]{DOUBLE_LINE}[/bold sky_blue]",
        f"[bold white]{title.center(BLOCK_WIDTH)}[/bold white]",
    ]
    if subtitle:
        lines.append(f"[dim]{subtitle.center(BLOCK_WIDTH)}[/dim]")
    lines.append(f"[bold sky_blue]{DOUBLE_LINE}[/bold sky_blue]")
    return lines


def format_divider_60() -> str:
    return f"[dim]{SINGLE_LINE}[/dim]"
