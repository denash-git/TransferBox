import pytest
from tui.components.layout import BLOCK_WIDTH, DOUBLE_LINE, SINGLE_LINE
from tui.components.menu import MenuItem, ArrowMenu, StatusLine


def test_tui_layout_constants():
    assert BLOCK_WIDTH == 60
    assert len(DOUBLE_LINE) == 60
    assert len(SINGLE_LINE) == 60


def test_arrow_menu_formatting_no_numbers():
    items = [
        MenuItem(id="users", label="Пользователи"),
        MenuItem(id="protocols", label="Настройки протоколов"),
        MenuItem(id="exit", label="Выход"),
    ]
    status_lines = [
        StatusLine(label="Домен:", value="test.com"),
        StatusLine(label="Caddy:", value="активен", dot_color="green"),
    ]
    menu = ArrowMenu(
        title="TransferBox v4.0.0",
        subtitle="Панель Управления",
        items=items,
        status_lines=status_lines,
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
    # Verify labels and status are present
    assert "Пользователи" in text
    assert "Настройки протоколов" in text
    assert "test.com" in text
    assert "● " in text


def test_arrow_menu_style_validity():
    from prompt_toolkit.styles import Style
    style = Style.from_dict({
        "border": "ansiblue bold",
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
    assert style is not None
