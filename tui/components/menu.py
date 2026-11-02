from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple
import shutil

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import Window, HSplit
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style

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
    Strict 60-character block grid menu without broken emojis.
    Authentic TransferBox visual styling (Blue borders, Yellow header, Green/Red dots).
    Navigated via Up/Down or k/j, Enter to select, Escape/q to exit.
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
        self.result: Optional[str] = None

    def _render_menu(self) -> FormattedText:
        pad = get_block_padding(BLOCK_WIDTH)
        result: FormattedText = []

        result.append(("", "\n"))

        # Main Header (Double Line 60 chars)
        result.append(("", pad))
        result.append(("class:border", f"{DOUBLE_LINE}\n"))
        result.append(("", pad))
        result.append(("class:title", f"{self.title.center(BLOCK_WIDTH)}\n"))
        if self.subtitle:
            result.append(("", pad))
            result.append(("class:subtitle", f"{self.subtitle.center(BLOCK_WIDTH)}\n"))
        result.append(("", pad))
        result.append(("class:border", f"{DOUBLE_LINE}\n"))

        # Status lines (Services, Domain, IP)
        if self.status_lines:
            for s in self.status_lines:
                result.append(("", f"{pad}  "))
                result.append(("class:status_label", f"{s.label:<14}"))
                if s.dot_color:
                    result.append((f"class:dot_{s.dot_color}", "● "))
                result.append(("class:status_value", f"{s.value}\n"))
            result.append(("", pad))
            result.append(("class:divider", f"{SINGLE_LINE}\n"))

        # Menu items (No numbers, no broken emojis!)
        for idx, item in enumerate(self.items):
            is_active = (idx == self.selected_index)
            avail_len = BLOCK_WIDTH - 6
            extra_len = len(item.extra)

            if extra_len > 0:
                spacing = max(1, avail_len - len(item.label) - extra_len)
                row_str = f"{item.label}{' ' * spacing}{item.extra}"
            else:
                row_str = f"{item.label:<{avail_len}}"

            result.append(("", pad))
            if is_active:
                result.append(("class:cursor", " › "))
                result.append(("class:selected", f"{row_str} \n"))
            else:
                result.append(("", "   "))
                result.append(("class:unselected", f"{row_str} \n"))

        # Footer divider & navigation hints
        result.append(("", pad))
        result.append(("class:divider", f"{SINGLE_LINE}\n"))
        hint = " [↑/↓] Навигация  [Enter] Выбор"
        result.append(("", pad))
        result.append(("class:hint", f"{hint}\n\n"))

        return result

    def show(self) -> Optional[str]:
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

        style = Style.from_dict({
            "border": "ansiinteractive ansiblue bold",
            "divider": "ansiblue",
            "title": "ansiyellow bold",
            "subtitle": "ansibrightblack",
            "status_label": "ansiwhite bold",
            "status_value": "ansiwhite",
            "dot_green": "ansigreen bold",
            "dot_red": "ansired bold",
            "dot_yellow": "ansiyellow bold",
            "cursor": "ansigreen bold",
            "selected": "reverse bold",
            "unselected": "ansiwhite",
            "hint": "ansibrightblack",
        })

        app = Application(
            layout=layout,
            key_bindings=kb,
            style=style,
            full_screen=False,
        )

        try:
            return app.run()
        except (EOFError, KeyboardInterrupt):
            return "exit"
