from __future__ import annotations
import sys
import shutil
from dataclasses import dataclass
from typing import List, Optional

from prompt_toolkit import Application
from prompt_toolkit.layout import Layout, HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

BLOCK_WIDTH = 60
DOUBLE_LINE = "═" * BLOCK_WIDTH
SINGLE_LINE = "─" * BLOCK_WIDTH


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


# Bright ANSI 16-color palette + bold: maximum compatibility AND vivid look
# in every terminal (PowerShell, MobaXterm, PuTTY, Windows Terminal).
STYLE = Style.from_dict({
    "border": "bold ansiblue",
    "title": "bold ansiyellow",
    "subtitle": "bold ansibrightblack",
    "item": "bold ansiwhite",
    "item.selected": "bg:ansiblue fg:ansiwhite bold",
    "extra": "ansibrightblack",
    "dot.green": "bold ansigreen",
    "dot.red": "bold ansired",
    "dot.yellow": "bold ansiyellow",
    "status.label": "bold ansiwhite",
    "status.value": "ansiwhite",
    "hint": "ansibrightblack",
    "divider": "bold ansiblue",
})


class ArrowMenu:
    """
    Flicker-free, smooth terminal menu using prompt_toolkit.
    - Alternate screen buffer (no scroll artifacts).
    - Differential redraw (only changed cells repaint).
    - 60-char grid with EXPLICIT left padding computed from terminal width
      (guaranteed horizontal centering in every terminal emulator).
    - Vertical centering via flexible spacers above/below the content.
    - Arrow-key navigation with smooth highlight.
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
        self._result: Optional[str] = None

    @staticmethod
    def _get_pad() -> str:
        """Compute centering from prompt_toolkit's live terminal dimensions."""
        try:
            from prompt_toolkit.application.current import get_app
            cols = get_app().output.get_size().columns
        except Exception:
            cols, _ = shutil.get_terminal_size((80, 24))
        pad = (cols - BLOCK_WIDTH) // 2
        return " " * max(2, pad)

    def _render_frame(self, cols: int, rows: int) -> str:
        """Render the menu as a plain-text frame (used by tests and debugging)."""
        parts = []
        for _style, text in self._build_fragments():
            parts.append(text)
        return "".join(parts)

    def _build_fragments(self) -> list:
        """Build formatted text fragments for the entire frame.

        Every visual line is prefixed with an explicit pad computed from the
        CURRENT terminal width, so horizontal centering never depends on the
        terminal emulator's alignment quirks.
        """
        pad = self._get_pad()
        frags: list = []

        def line(parts: list) -> None:
            frags.append(("", pad))
            frags.extend(parts)
            frags.append(("", "\n"))

        # Header
        line([("class:border", DOUBLE_LINE)])
        line([("class:title", self.title.center(BLOCK_WIDTH))])
        if self.subtitle:
            line([("class:subtitle", self.subtitle.center(BLOCK_WIDTH))])
        line([("class:border", DOUBLE_LINE)])

        # Status lines
        if self.status_lines:
            line([])
            for s in self.status_lines:
                parts: list = []
                if s.dot_color == "green":
                    parts.append(("class:dot.green", "● "))
                elif s.dot_color == "red":
                    parts.append(("class:dot.red", "● "))
                elif s.dot_color == "yellow":
                    parts.append(("class:dot.yellow", "● "))
                else:
                    parts.append(("", "  "))
                parts.append(("class:status.label", f"{s.label:<14}"))
                parts.append(("class:status.value", s.value))
                line(parts)
            line([("class:divider", SINGLE_LINE)])

        # Menu items
        line([])
        for idx, item in enumerate(self.items):
            is_active = (idx == self.selected_index)
            is_exit_item = item.id in ("exit", "back")

            # Separator before exit/back
            if is_exit_item and idx > 0 and len(self.items) > 2:
                line([])

            avail_len = BLOCK_WIDTH - 6
            extra_len = len(item.extra)
            if extra_len > 0:
                spacing = max(1, avail_len - len(item.label) - extra_len)
                row_text = f"{item.label}{' ' * spacing}{item.extra}"
            else:
                row_text = f"{item.label:<{avail_len}}"

            if is_active:
                line([("class:item.selected", f" ›  {row_text}  ")])
            else:
                line([("class:item", f"    {row_text}  ")])

            # Breathing space for short menus
            if idx < len(self.items) - 1 and not is_exit_item and len(self.items) <= 6:
                line([])

        # Footer
        line([("class:divider", SINGLE_LINE)])
        hint = "↑/↓ Навигация  Enter Выбор"
        line([("class:hint", hint.center(BLOCK_WIDTH))])

        return frags

    def show(self) -> Optional[str]:
        if not self.items:
            return None

        if not sys.stdin.isatty():
            return "exit"

        self._result = None
        self.selected_index = 0

        kb = KeyBindings()

        @kb.add("up")
        @kb.add("k")
        def _up(event):
            self.selected_index = (self.selected_index - 1) % len(self.items)
            event.app.invalidate()

        @kb.add("down")
        @kb.add("j")
        def _down(event):
            self.selected_index = (self.selected_index + 1) % len(self.items)
            event.app.invalidate()

        @kb.add("enter")
        def _enter(event):
            self._result = self.items[self.selected_index].id
            event.app.exit()

        @kb.add("escape")
        @kb.add("q")
        def _quit(event):
            self._result = "back" if any(i.id == "back" for i in self.items) else "exit"
            event.app.exit()

        # Content window: horizontal padding is explicit inside fragments,
        # so no reliance on the emulator's align behavior.
        content_window = Window(
            content=FormattedTextControl(self._build_fragments),
            wrap_lines=False,
            dont_extend_height=True,
        )

        # Vertical centering: flexible spacers above and below
        layout = Layout(
            HSplit([
                Window(height=Dimension(weight=1)),   # top spacer
                content_window,                        # actual menu
                Window(height=Dimension(weight=1)),   # bottom spacer
            ])
        )

        app = Application(
            layout=layout,
            key_bindings=kb,
            style=STYLE,
            full_screen=True,
            mouse_support=False,
        )

        app.run()
        return self._result
