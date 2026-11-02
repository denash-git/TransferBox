from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Callable
import sys

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import Window, HSplit
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.formatted_text import FormattedText

from .layout import get_block_padding, BLOCK_WIDTH, DOUBLE_LINE, SINGLE_LINE


@dataclass
class MenuItem:
    id: str
    label: str
    icon: str = ""
    extra: str = ""


class ArrowMenu:
    """
    Arrow-key interactive menu (No numbers!)
    Navigated via Up/Down or k/j, Enter to select, Escape/q to exit.
    Strictly adheres to 60-character centered grid.
    """

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        items: Optional[List[MenuItem]] = None,
        info_lines: Optional[List[str]] = None,
    ):
        self.title = title
        self.subtitle = subtitle
        self.items = items or []
        self.info_lines = info_lines or []
        self.selected_index = 0
        self.result: Optional[str] = None

    def _render_menu(self) -> FormattedText:
        pad = get_block_padding(BLOCK_WIDTH)
        result: FormattedText = []

        # Clear screen marker & spacing
        result.append(("", "\n"))

        # Header 60 chars
        result.append(("", f"{pad}"))
        result.append(("class:border", f"{DOUBLE_LINE}\n"))
        result.append(("", f"{pad}"))
        result.append(("class:title", f"{self.title.center(BLOCK_WIDTH)}\n"))
        if self.subtitle:
            result.append(("", f"{pad}"))
            result.append(("class:subtitle", f"{self.subtitle.center(BLOCK_WIDTH)}\n"))
        result.append(("", f"{pad}"))
        result.append(("class:border", f"{DOUBLE_LINE}\n"))

        # Info lines (services, IP, status)
        if self.info_lines:
            for line in self.info_lines:
                result.append(("", f"{pad}{line}\n"))
            result.append(("", f"{pad}"))
            result.append(("class:divider", f"{SINGLE_LINE}\n"))

        # Items (No numbering!)
        for idx, item in enumerate(self.items):
            is_active = (idx == self.selected_index)
            icon_str = f"{item.icon} " if item.icon else ""
            main_text = f"{icon_str}{item.label}"

            # Calculate space between label and extra
            # Inner usable space is BLOCK_WIDTH - 4 chars for cursor and borders: 56 chars
            extra_len = len(item.extra)
            avail_len = BLOCK_WIDTH - 6
            if extra_len > 0:
                spacing = max(1, avail_len - len(main_text) - extra_len)
                row_str = f"{main_text}{' ' * spacing}{item.extra}"
            else:
                row_str = f"{main_text:<{avail_len}}"

            result.append(("", f"{pad}"))
            if is_active:
                result.append(("class:cursor", " › "))
                result.append(("class:selected", f"{row_str} \n"))
            else:
                result.append(("", "   "))
                result.append(("class:unselected", f"{row_str} \n"))

        # Footer divider & navigation hints
        result.append(("", f"{pad}"))
        result.append(("class:divider", f"{SINGLE_LINE}\n"))
        hint = " [↑/↓] Навигация  [Enter] Выбор"
        result.append(("", f"{pad}"))
        result.append(("class:hint", f"{hint}\n\n"))

        return result

    def show(self) -> Optional[str]:
        """Displays interactive menu and blocks until user presses Enter or Escape."""
        if not self.items:
            return None

        kb = KeyBindings()

        @kb.add("up")
        @kb.add("k")
        def _move_up(event):
            self.selected_index = (self.selected_index - 1) % len(self.items)

        @kb.add("down")
        @kb.add("j")
        def _move_down(event):
            self.selected_index = (self.selected_index + 1) % len(self.items)

        @kb.add("enter")
        def _select(event):
            self.result = self.items[self.selected_index].id
            event.app.exit(result=self.result)

        @kb.add("escape")
        @kb.add("q")
        def _exit(event):
            self.result = "back"
            event.app.exit(result="back")

        control = FormattedTextControl(text=self._render_menu)
        window = Window(content=control)
        layout = Layout(HSplit([window]))

        from prompt_toolkit.styles import Style
        style = Style.from_dict({
            "border": "#38bdf8 bold",     # sky-400
            "divider": "#64748b",         # slate-500
            "title": "#ffffff bold",
            "subtitle": "#94a3b8 italic",
            "cursor": "#34d399 bold",     # emerald-400
            "selected": "#ffffff bold bg:#1e293b", # slate-800 highlight
            "unselected": "#cbd5e1",
            "hint": "#64748b text-xs",
        })

        app = Application(
            layout=layout,
            key_bindings=kb,
            style=style,
            full_screen=False,
        )

        return app.run()
