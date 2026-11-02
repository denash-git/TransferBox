from __future__ import annotations
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Callable

from prompt_toolkit import Application
from prompt_toolkit.layout import Layout, HSplit, Window, ConditionalContainer
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML

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


STYLE = Style.from_dict({
    "border": "bold #5599dd",
    "title": "bold #ffcc00",
    "subtitle": "italic #888888",
    "item": "#ffffff",
    "item.selected": "reverse",
    "item.cursor": "bold #ffcc00",
    "extra": "#aaaaaa",
    "dot.green": "bold #00cc00",
    "dot.red": "bold #ff3333",
    "dot.yellow": "bold #ffcc00",
    "status.label": "bold #ffffff",
    "status.value": "#cccccc",
    "hint": "italic #666666",
    "divider": "#5599dd",
})


class ArrowMenu:
    """
    Flicker-free, smooth terminal menu using prompt_toolkit.
    - Alternate screen buffer (no scroll artifacts).
    - Differential redraw (only changed cells repaint).
    - 60-char centered grid with vertical centering.
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

    def _render_frame(self, cols: int, rows: int) -> str:
        """Render the menu as a plain-text frame (used by tests and for debugging)."""
        parts = []
        for _style, text in self._build_fragments():
            parts.append(text)
        return "".join(parts)

    def _build_fragments(self) -> list:
        """Build formatted text fragments for the entire frame."""
        frags = []

        # Header
        frags.append(("class:border", DOUBLE_LINE))
        frags.append(("", "\n"))
        frags.append(("class:title", self.title.center(BLOCK_WIDTH)))
        frags.append(("", "\n"))
        if self.subtitle:
            frags.append(("class:subtitle", self.subtitle.center(BLOCK_WIDTH)))
            frags.append(("", "\n"))
        frags.append(("class:border", DOUBLE_LINE))

        # Status lines
        if self.status_lines:
            frags.append(("", "\n"))
            for s in self.status_lines:
                dot = ""
                if s.dot_color == "green":
                    dot = "● "
                    frags.append(("class:dot.green", dot))
                elif s.dot_color == "red":
                    dot = "● "
                    frags.append(("class:dot.red", dot))
                elif s.dot_color == "yellow":
                    dot = "● "
                    frags.append(("class:dot.yellow", dot))
                else:
                    frags.append(("", "  "))

                frags.append(("class:status.label", f"{s.label:<14}"))
                frags.append(("class:status.value", s.value))
                frags.append(("", "\n"))
            frags.append(("class:divider", SINGLE_LINE))

        # Menu items
        frags.append(("", "\n"))
        for idx, item in enumerate(self.items):
            is_active = (idx == self.selected_index)
            is_exit_item = item.id in ("exit", "back")

            # Separator before exit/back
            if is_exit_item and idx > 0 and len(self.items) > 2:
                frags.append(("", "\n"))

            avail_len = BLOCK_WIDTH - 6
            extra_len = len(item.extra)
            if extra_len > 0:
                spacing = max(1, avail_len - len(item.label) - extra_len)
                row_text = f"{item.label}{' ' * spacing}{item.extra}"
            else:
                row_text = f"{item.label:<{avail_len}}"

            if is_active:
                frags.append(("class:item.selected", f" ›  {row_text}  "))
            else:
                frags.append(("class:item", f"     {row_text}  "))

            frags.append(("", "\n"))

            # Breathing space for short menus
            if idx < len(self.items) - 1 and not is_exit_item and len(self.items) <= 6:
                frags.append(("", "\n"))

        # Footer
        frags.append(("class:divider", SINGLE_LINE))
        frags.append(("", "\n"))
        hint = "↑/↓ Навигация  Enter Выбор"
        frags.append(("class:hint", hint.center(BLOCK_WIDTH)))

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

        body = Window(
            content=FormattedTextControl(self._build_fragments),
            wrap_lines=False,
            dont_extend_height=True,
            align="center",
        )

        layout = Layout(HSplit([body]))

        app = Application(
            layout=layout,
            key_bindings=kb,
            style=STYLE,
            full_screen=True,
            mouse_support=False,
        )

        app.run()
        return self._result
