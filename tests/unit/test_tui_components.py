import pytest
from tui.components.menu import (
    BLOCK_WIDTH,
    DOUBLE_LINE,
    SINGLE_LINE,
    strip_ansi,
    select_menu,
)


def test_tui_layout_constants():
    assert BLOCK_WIDTH == 60
    assert len(DOUBLE_LINE) == 60
    assert len(SINGLE_LINE) == 60


def test_strip_ansi():
    raw = "\033[1;32m● активен\033[0m"
    assert strip_ansi(raw) == "● активен"


def test_select_menu_non_interactive():
    options = ["Пользователи", "Настройки", "Выход"]
    choice = select_menu("TransferBox v. 4.0.0", options)
    # In non-interactive mode returns the last option (Exit)
    assert choice == len(options) - 1
