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


def test_arrow_menu_style_validity():
    from prompt_toolkit.styles import Style
    # Ensure style dictionary passes prompt_toolkit parsing without errors
    style = Style.from_dict({
        "border": "#38bdf8 bold",
        "divider": "#64748b",
        "title": "#ffffff bold",
        "subtitle": "#94a3b8 italic",
        "cursor": "#34d399 bold",
        "selected": "#ffffff bold bg:#1e293b",
        "unselected": "#cbd5e1",
        "hint": "#64748b italic",
    })
    assert style is not None
