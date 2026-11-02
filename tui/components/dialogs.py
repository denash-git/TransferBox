from __future__ import annotations
from typing import Optional
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.formatted_text import FormattedText
from rich.console import Console

from .layout import get_block_padding, BLOCK_WIDTH, SINGLE_LINE, DOUBLE_LINE

console = Console(highlight=False)


def read_input(prompt_text: str, default: str = "") -> str:
    """Prompt user for input anchored strictly at the 60-character block grid."""
    pad = get_block_padding(BLOCK_WIDTH)
    formatted_prompt = FormattedText([
        ("", f"{pad}"),
        ("class:prompt_lbl", f"{prompt_text.strip()} "),
    ])
    try:
        val = prompt(formatted_prompt, default=default)
        return val.strip()
    except (KeyboardInterrupt, EOFError):
        return ""


def read_secret(prompt_text: str) -> str:
    """Prompt user for password with masked characters (***) strictly on the grid."""
    pad = get_block_padding(BLOCK_WIDTH)
    formatted_prompt = FormattedText([
        ("", f"{pad}"),
        ("class:prompt_lbl", f"{prompt_text.strip()} "),
    ])
    try:
        val = prompt(formatted_prompt, is_password=True)
        return val.strip()
    except (KeyboardInterrupt, EOFError):
        return ""


def confirm_dialog(question: str) -> bool:
    """Prompt user for confirmation (y/N)."""
    val = read_input(f"{question} (д/Н): ")
    return val.strip().lower() in ("д", "y", "yes", "да", "1")


def pause_prompt():
    """Waits for any key press centered on the grid."""
    pad = get_block_padding(BLOCK_WIDTH)
    formatted_prompt = FormattedText([
        ("", f"{pad}"),
        ("class:dim", "Нажмите Enter для продолжения..."),
    ])
    try:
        prompt(formatted_prompt)
    except (KeyboardInterrupt, EOFError):
        pass
