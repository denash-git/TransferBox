from __future__ import annotations
import shutil
from typing import List
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

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
        f"[bold yellow]{title.center(BLOCK_WIDTH)}[/bold yellow]",
    ]
    if subtitle:
        lines.append(f"[dim]{subtitle.center(BLOCK_WIDTH)}[/dim]")
    lines.append(f"[bold sky_blue]{DOUBLE_LINE}[/bold sky_blue]")
    return lines


def format_divider_60() -> str:
    return f"[sky_blue]{SINGLE_LINE}[/sky_blue]"


def print_panel(content: str, title: str = "", border_style: str = "sky_blue") -> None:
    """Print a rich Panel centered on the 60-char grid."""
    panel = Panel(
        content,
        title=title or None,
        width=BLOCK_WIDTH + 4,
        border_style=border_style,
        padding=(0, 1),
    )
    console.print(Align.center(panel))


def print_success(msg: str) -> None:
    pad = get_block_padding()
    console.print(f"{pad}[bold green]✓ {msg}[/bold green]")


def print_error(msg: str) -> None:
    pad = get_block_padding()
    console.print(f"{pad}[bold red]✗ {msg}[/bold red]")


def print_info(msg: str) -> None:
    pad = get_block_padding()
    console.print(f"{pad}[dim]{msg}[/dim]")
