from __future__ import annotations
import sys
import os
import shutil
from dataclasses import dataclass
from typing import List, Optional

BLOCK_WIDTH = 60
DOUBLE_LINE = "═" * BLOCK_WIDTH
SINGLE_LINE = "─" * BLOCK_WIDTH

# ANSI Escape Sequences
ESC = "\033"
C_RESET = f"{ESC}[0m"
C_BOLD = f"{ESC}[1m"
C_DIM = f"{ESC}[2m"
C_BLUE = f"{ESC}[1;34m"
C_YELLOW = f"{ESC}[1;33m"
C_GREEN = f"{ESC}[1;32m"
C_RED = f"{ESC}[1;31m"
C_WHITE = f"{ESC}[1;37m"
C_REVERSE = f"{ESC}[7m"
C_CLEAR_LINE = f"{ESC}[K"
C_CLEAR_SCREEN = f"{ESC}[2J{ESC}[H"
C_HOME = f"{ESC}[H"
C_HIDE_CURSOR = f"{ESC}[?25l"
C_SHOW_CURSOR = f"{ESC}[?25h"
C_ENTER_ALT_SCREEN = f"{ESC}[?1049h"
C_EXIT_ALT_SCREEN = f"{ESC}[?1049l"


def get_terminal_size() -> tuple[int, int]:
    cols, rows = shutil.get_terminal_size((80, 24))
    return cols, rows


def read_key() -> str:
    """Reads a single keypress cross-platform (Linux termios / Windows msvcrt)."""
    if sys.platform != "win32":
        import termios
        import tty
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                # Check for escape sequence
                ch2 = sys.stdin.read(1)
                if ch2 == "[":
                    ch3 = sys.stdin.read(1)
                    if ch3 == "A":
                        return "up"
                    elif ch3 == "B":
                        return "down"
                    elif ch3 == "C":
                        return "right"
                    elif ch3 == "D":
                        return "left"
                return "escape"
            elif ch in ("\r", "\n"):
                return "enter"
            elif ch in ("q", "Q"):
                return "q"
            elif ch == "k":
                return "up"
            elif ch == "j":
                return "down"
            return ch
        except (KeyboardInterrupt, EOFError):
            return "escape"
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    else:
        import msvcrt
        try:
            ch = msvcrt.getch()
            if ch in (b"\x00", b"\xe0"):
                ch2 = msvcrt.getch()
                if ch2 == b"H":
                    return "up"
                elif ch2 == b"P":
                    return "down"
            elif ch in (b"\r", b"\n"):
                return "enter"
            elif ch == b"\x1b":
                return "escape"
            elif ch in (b"q", b"Q"):
                return "q"
            elif ch == b"k":
                return "up"
            elif ch == b"j":
                return "down"
            return ch.decode("latin1", errors="ignore")
        except Exception:
            return "escape"


@dataclass
class MenuItem:
    id: str
    label: str
    extra: str = ""


@dataclass
class StatusLine:
    label: str
    value: str
    dot_color: Optional[str] = None  # "green", "red", "yellow"


class ArrowMenu:
    """
    Spacious, centered, flicker-free terminal menu for TransferBox.
    - True horizontal AND vertical centering on screen.
    - Uses alternate screen buffer (in-place redraws, never scrolls down).
    - Authentic TransferBox visual grid: 60 chars, blue borders, yellow title, green/red dots.
    - Comfortable spacing between items with inverted bar highlight.
    """

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        items: Optional[List[MenuItem]] = None,
        status_lines: Optional[List[StatusLine]] = None,
    ):
        self.title = title
        self.subtitle = subtitle
        self.items = items or []
        self.status_lines = status_lines or []
        self.selected_index = 0

    def _render_frame(self, cols: int, rows: int) -> str:
        pad_x = max(2, (cols - BLOCK_WIDTH) // 2)
        pad = " " * pad_x

        lines = []

        # Header
        lines.append(f"{pad}{C_BLUE}{DOUBLE_LINE}{C_RESET}")
        lines.append(f"{pad}{C_YELLOW}{self.title.center(BLOCK_WIDTH)}{C_RESET}")
        if self.subtitle:
            lines.append(f"{pad}{C_DIM}{self.subtitle.center(BLOCK_WIDTH)}{C_RESET}")
        lines.append(f"{pad}{C_BLUE}{DOUBLE_LINE}{C_RESET}")

        # Status lines (if any)
        if self.status_lines:
            for s in self.status_lines:
                dot_str = ""
                if s.dot_color == "green":
                    dot_str = f"{C_GREEN}●{C_RESET} "
                elif s.dot_color == "red":
                    dot_str = f"{C_RED}●{C_RESET} "
                elif s.dot_color == "yellow":
                    dot_str = f"{C_YELLOW}●{C_RESET} "

                val_styled = f"{dot_str}{s.value}"
                lines.append(f"{pad}  {C_WHITE}{s.label:<14}{C_RESET}{val_styled}")
            lines.append(f"{pad}{C_BLUE}{SINGLE_LINE}{C_RESET}")

        # Menu items (Spacious layout with empty line separators)
        for idx, item in enumerate(self.items):
            is_active = (idx == self.selected_index)
            is_exit_item = item.id in ("exit", "back")

            # Add an extra separating empty line before "Назад" / "Выход"
            if is_exit_item and idx > 0 and len(self.items) > 2:
                lines.append(f"{pad}")

            avail_len = BLOCK_WIDTH - 6
            extra_len = len(item.extra)
            if extra_len > 0:
                spacing = max(1, avail_len - len(item.label) - extra_len)
                row_text = f"{item.label}{' ' * spacing}{item.extra}"
            else:
                row_text = f"{item.label:<{avail_len}}"

            if is_active:
                if is_exit_item:
                    # Highlight exit item in yellow reverse
                    lines.append(f"{pad}{C_YELLOW}{C_REVERSE} ›  {row_text}  {C_RESET}")
                else:
                    # Inverted white bar
                    lines.append(f"{pad}{C_REVERSE} ›  {row_text}  {C_RESET}")
            else:
                lines.append(f"{pad}     {row_text}  ")

            # Subtle breathing space between normal items if menu is not overly long
            if idx < len(self.items) - 1 and not is_exit_item and len(self.items) <= 6:
                lines.append(f"{pad}")

        # Footer
        lines.append(f"{pad}{C_BLUE}{SINGLE_LINE}{C_RESET}")
        hint = "[↑/↓] Навигация  [Enter] Выбор"
        lines.append(f"{pad}{C_DIM}{hint.center(BLOCK_WIDTH)}{C_RESET}")

        # Vertical Centering (Top padding)
        total_content_height = len(lines)
        top_margin = max(1, (rows - total_content_height) // 2)

        output_parts = [C_HOME]
        for _ in range(top_margin):
            output_parts.append(f"{C_CLEAR_LINE}\n")

        for line in lines:
            output_parts.append(f"{line}{C_CLEAR_LINE}\n")

        # Clear remaining bottom lines
        output_parts.append(f"{ESC}[J")
        return "".join(output_parts)

    def show(self) -> Optional[str]:
        if not self.items:
            return None

        # Non-interactive check (e.g. piped or test environment)
        if not sys.stdin.isatty():
            return "exit"

        # Enter alternate screen buffer & hide cursor
        sys.stdout.write(f"{C_ENTER_ALT_SCREEN}{C_HIDE_CURSOR}{C_CLEAR_SCREEN}")
        sys.stdout.flush()

        try:
            while True:
                cols, rows = get_terminal_size()
                frame = self._render_frame(cols, rows)
                sys.stdout.write(frame)
                sys.stdout.flush()

                key = read_key()
                if key == "up":
                    self.selected_index = (self.selected_index - 1) % len(self.items)
                elif key == "down":
                    self.selected_index = (self.selected_index + 1) % len(self.items)
                elif key == "enter":
                    return self.items[self.selected_index].id
                elif key in ("escape", "q"):
                    return "back" if any(i.id == "back" for i in self.items) else "exit"
        finally:
            # Always restore terminal screen & cursor on exit
            sys.stdout.write(f"{C_SHOW_CURSOR}{C_EXIT_ALT_SCREEN}")
            sys.stdout.flush()
