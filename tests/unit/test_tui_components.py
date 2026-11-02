import pytest
from tui.components.layout import BLOCK_WIDTH, DOUBLE_LINE, SINGLE_LINE, format_header_60
from tui.components.menu import MenuItem, ArrowMenu


def test_tui_layout_constants():
    assert BLOCK_WIDTH == 60
    assert len(DOUBLE_LINE) == 60
    assert len(SINGLE_LINE) == 60


def test_arrow_menu_formatting_no_numbers():
    items = [
        MenuItem(id="users", label="Управление пользователями", icon="👥"),
        MenuItem(id="protocols", label="Настройки протоколов", icon="⚡"),
        MenuItem(id="exit", label="Выход", icon="🚪"),
    ]
    menu = ArrowMenu(
        title="TransferBox v4.0",
        subtitle="Панель Управления",
        items=items,
    )
    formatted = menu._render_menu()
    text = "".join(part[1] for part in formatted)

    # Verify 60-char lines
    assert "═" * 60 in text
    assert "─" * 60 in text
    # Verify NO numbers like [1] or 1.
    assert "[1]" not in text
    assert "1." not in text
    assert "[2]" not in text
    # Verify icons and labels are present
    assert "👥 Управление пользователями" in text
    assert "⚡ Настройки протоколов" in text
