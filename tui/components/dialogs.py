from __future__ import annotations
import sys
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style

from .layout import get_block_padding, BLOCK_WIDTH

INPUT_STYLE = Style.from_dict({
    "prompt": "bold #5599dd",
})


def read_input(prompt_text: str, default: str = "", is_password: bool = False) -> str:
    """Prompt user for input anchored at the 60-character block grid using prompt_toolkit."""
    pad = get_block_padding(BLOCK_WIDTH)
    prompt_str = f"{pad}{prompt_text.strip()} "
    try:
        val = prompt(
            prompt_str,
            default=default,
            is_password=is_password,
            style=INPUT_STYLE,
        )
        return val.strip()
    except (KeyboardInterrupt, EOFError):
        return ""


def read_secret(prompt_text: str) -> str:
    """Prompt user for password with masked characters on the grid."""
    return read_input(prompt_text, is_password=True)


def confirm_dialog(question: str) -> bool:
    """Prompt user for confirmation (д/Н)."""
    val = read_input(f"{question} (д/Н):")
    return val.strip().lower() in ("д", "y", "yes", "да", "1")


def pause_prompt():
    """Waits for Enter centered on the grid."""
    pad = get_block_padding(BLOCK_WIDTH)
    prompt_str = f"\n{pad}Нажмите Enter для продолжения... "
    try:
        prompt(prompt_str, style=INPUT_STYLE)
    except (KeyboardInterrupt, EOFError):
        pass
