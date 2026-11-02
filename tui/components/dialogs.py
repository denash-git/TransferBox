from __future__ import annotations
import sys
import getpass
from .layout import get_block_padding, BLOCK_WIDTH


def read_input(prompt_text: str, default: str = "") -> str:
    """Prompt user for input anchored strictly at the 60-character block grid."""
    pad = get_block_padding(BLOCK_WIDTH)
    sys.stdout.write("\033[?25h")  # Ensure cursor is visible
    prompt_str = f"{pad}{prompt_text.strip()} "
    try:
        val = input(prompt_str)
        sys.stdout.write("\033[?25l")  # Hide cursor again
        return (val.strip() or default)
    except (KeyboardInterrupt, EOFError):
        sys.stdout.write("\033[?25l\n")
        return ""


def read_secret(prompt_text: str) -> str:
    """Prompt user for password with masked characters strictly on the grid."""
    pad = get_block_padding(BLOCK_WIDTH)
    sys.stdout.write("\033[?25h")
    prompt_str = f"{pad}{prompt_text.strip()} "
    try:
        val = getpass.getpass(prompt_str)
        sys.stdout.write("\033[?25l")
        return val.strip()
    except (KeyboardInterrupt, EOFError):
        sys.stdout.write("\033[?25l\n")
        return ""


def confirm_dialog(question: str) -> bool:
    """Prompt user for confirmation (y/N)."""
    val = read_input(f"{question} (д/Н): ")
    return val.strip().lower() in ("д", "y", "yes", "да", "1")


def pause_prompt():
    """Waits for Enter centered on the grid."""
    pad = get_block_padding(BLOCK_WIDTH)
    prompt_str = f"\n{pad}\033[2mНажмите Enter для продолжения...\033[0m"
    try:
        input(prompt_str)
    except (KeyboardInterrupt, EOFError):
        pass
