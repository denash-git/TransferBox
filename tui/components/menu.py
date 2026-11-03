from __future__ import annotations
import sys
import os
import shutil
import re
from typing import List, Optional, Dict, Any, Tuple

BLOCK_WIDTH = 60
DOUBLE_LINE = "═" * BLOCK_WIDTH
SINGLE_LINE = "─" * BLOCK_WIDTH

# ANSI Colors
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
C_YELLOW_BG = f"{ESC}[43;30m"
C_RED_BG = f"{ESC}[41;37m"
C_CLEAR_LINE = f"{ESC}[K"
C_CLEAR_SCREEN = f"{ESC}[2J{ESC}[H"
C_HOME = f"{ESC}[H"
C_HIDE_CURSOR = f"{ESC}[?25l"
C_SHOW_CURSOR = f"{ESC}[?25h"
C_ENTER_ALT_SCREEN = f"{ESC}[?1049h"
C_EXIT_ALT_SCREEN = f"{ESC}[?1049l"


def strip_ansi(text: str) -> str:
    """Removes ANSI escape codes from string for accurate width calculation."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def get_terminal_size() -> Tuple[int, int]:
    cols, rows = shutil.get_terminal_size((80, 24))
    return cols, rows


def read_key() -> str:
    """Reads a single keypress cross-platform with non-blocking escape parsing."""
    if sys.platform != "win32":
        import termios
        import tty
        import select
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                # Check for escape sequence
                r, _, _ = select.select([sys.stdin], [], [], 0.05)
                if r:
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
                    elif ch2 == "O":
                        ch3 = sys.stdin.read(1)
                        if ch3 == "A":
                            return "up"
                        elif ch3 == "B":
                            return "down"
                return "escape"
            elif ch in ("\r", "\n"):
                return "enter"
            elif ch in ("q", "Q"):
                return "q"
            elif ch == "0":
                return "0"
            elif ch in ("k", "w", "W"):
                return "up"
            elif ch in ("j", "s", "S"):
                return "down"
            return ch
        except (KeyboardInterrupt, EOFError):
            return "escape"
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
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
            elif ch == b"0":
                return "0"
            elif ch in (b"k", b"w", b"W"):
                return "up"
            elif ch in (b"j", b"s", b"S"):
                return "down"
            return ch.decode("latin1", errors="ignore")
        except Exception:
            return "escape"


def select_menu(
    title: str,
    options: List[str],
    show_status: bool = False,
    status_dict: Optional[Dict[str, str]] = None,
) -> int:
    """
    Renders the authentic TransferBox menu with arrow navigation,
    centered in both dimensions on the 60-character block grid.
    Returns the index of selected option, or -1 on exit/cancel.
    """
    if not options:
        return -1

    if not sys.stdin.isatty():
        return len(options) - 1

    active_idx = 0

    # Enter alternate screen buffer & hide cursor
    sys.stdout.write(f"{C_ENTER_ALT_SCREEN}{C_HIDE_CURSOR}{C_CLEAR_SCREEN}")
    sys.stdout.flush()

    try:
        while True:
            cols, rows = get_terminal_size()
            pad_x = max(2, (cols - BLOCK_WIDTH) // 2)
            pad = " " * pad_x

            lines: List[str] = []

            # ─── HEADER ───────────────────────────────────────────────────────
            lines.append(f"{pad}{C_BLUE}{DOUBLE_LINE}{C_RESET}")
            lines.append(f"{pad}{C_YELLOW}{title.center(BLOCK_WIDTH)}{C_RESET}")

            # Status block (only for main menu)
            if show_status and status_dict:
                lines.append(f"{pad}{C_BLUE}{SINGLE_LINE}{C_RESET}")
                domain = status_dict.get("domain", "не задан")
                fqdn = status_dict.get("fqdn", "")
                lines.append(f"{pad}  {C_WHITE}Домен:        {C_BOLD}{domain}{C_RESET}")
                if fqdn:
                    lines.append(f"{pad}  {C_WHITE}FQDN VPS:     {C_BOLD}{fqdn}{C_RESET}")
                lines.append(f"{pad}{C_BLUE}{SINGLE_LINE}{C_RESET}")

                # Services dots
                caddy_str = status_dict.get("caddy", "")
                singbox_str = status_dict.get("singbox", "")
                mieru_str = status_dict.get("mieru", "")
                netbird_str = status_dict.get("netbird", "")
                bbr_str = status_dict.get("bbr", "")
                ssh_str = status_dict.get("ssh", f"{C_GREEN}включен{C_RESET}")
                sec_str = status_dict.get("security", f"{C_GREEN}активна{C_RESET}")

                lines.append(f"{pad}  {C_WHITE}TCP BBR:      {bbr_str}{C_RESET}")
                lines.append(f"{pad}  {C_WHITE}Caddy:        {caddy_str}{C_RESET}")
                lines.append(f"{pad}  {C_WHITE}sing-box:     {singbox_str}{C_RESET}")
                if mieru_str:
                    lines.append(f"{pad}  {C_WHITE}Mieru:        {mieru_str}{C_RESET}")
                if netbird_str:
                    lines.append(f"{pad}  {C_WHITE}NetBird:      {netbird_str}{C_RESET}")
                lines.append(f"{pad}  {C_WHITE}SSH пароль:   {ssh_str}{C_RESET}")
                lines.append(f"{pad}  {C_WHITE}Защита:       {sec_str}{C_RESET}")
                lines.append(f"{pad}{C_BLUE}{DOUBLE_LINE}{C_RESET}")
            else:
                lines.append(f"{pad}{C_BLUE}{SINGLE_LINE}{C_RESET}")

            # ─── MENU ITEMS ──────────────────────────────────────────────────
            clean_opts = [strip_ansi(o) for o in options]
            max_opt_len = max(len(c) for c in clean_opts) if clean_opts else 30
            content_width = max(max_opt_len, 30)
            if content_width > BLOCK_WIDTH - 6:
                content_width = BLOCK_WIDTH - 6

            for i, opt in enumerate(options):
                clean_opt = clean_opts[i]
                is_active = (i == active_idx)
                is_back = clean_opt in ("Назад", "Отмена", "Выход")
                is_danger = "Удалить" in clean_opt or "Пересоздать" in clean_opt

                # Empty line between items for spacious layout
                if i != 0:
                    lines.append(f"{pad}")

                # Extra empty line before Back / Exit
                if is_back and i != 0 and len(options) > 2:
                    lines.append(f"{pad}")

                pad_len = max(0, content_width - len(clean_opt))
                
                if is_back:
                    p_left = pad_len // 2
                    p_right = pad_len - p_left
                    text_row = f"{' ' * p_left}{clean_opt}{' ' * p_right}"
                    if is_active:
                        lines.append(f"{pad}{C_YELLOW_BG}  {text_row}  {C_RESET}")
                    else:
                        lines.append(f"{pad}{C_YELLOW}  {text_row}  {C_RESET}")
                else:
                    text_row = f"{clean_opt}{' ' * pad_len}"
                    if is_active:
                        if is_danger:
                            lines.append(f"{pad}{C_RED_BG}  {text_row}  {C_RESET}")
                        else:
                            lines.append(f"{pad}{C_REVERSE}  {text_row}  {C_RESET}")
                    else:
                        if is_danger:
                            lines.append(f"{pad}{C_RED}  {opt}  {C_RESET}")
                        else:
                            lines.append(f"{pad}  {opt}  {C_RESET}")

            # ─── FOOTER ───────────────────────────────────────────────────────
            lines.append(f"{pad}{C_BLUE}{SINGLE_LINE}{C_RESET}")
            hint = "↑↓ / W/S — выбор   Enter — выбрать   q — назад   0 — Выход"
            lines.append(f"{pad}{C_DIM}{hint.center(BLOCK_WIDTH)}{C_RESET}")

            # Vertical Centering (Top padding)
            total_lines_count = len(lines)
            top_pad = max(0, (rows - total_lines_count - 1) // 2)

            buf = [C_HOME]
            for _ in range(top_pad):
                buf.append(f"{C_CLEAR_LINE}\n")
            for line in lines:
                buf.append(f"{line}{C_CLEAR_LINE}\n")
            buf.append(f"{ESC}[J")

            sys.stdout.write("".join(buf))
            sys.stdout.flush()

            # Read user key
            key = read_key()
            if key == "up":
                active_idx = (active_idx - 1) % len(options)
            elif key == "down":
                active_idx = (active_idx + 1) % len(options)
            elif key == "enter":
                return active_idx
            elif key == "0":
                # Quick exit
                for idx, o in enumerate(clean_opts):
                    if o == "Выход":
                        return idx
                return -1
            elif key in ("escape", "q"):
                # Back / Cancel / Exit
                for idx, o in enumerate(clean_opts):
                    if o in ("Назад", "Отмена", "Выход"):
                        return idx
                return -1

    finally:
        sys.stdout.write(f"{C_SHOW_CURSOR}{C_EXIT_ALT_SCREEN}")
        sys.stdout.flush()
