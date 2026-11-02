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
    frame = menu._render_frame(cols=80, rows=24)

    # Verify 60-char lines
    assert "═" * 60 in frame
    assert "─" * 60 in frame
    # Verify NO numbers like [1] or 1.
    assert "[1]" not in frame
    assert "1." not in frame
    assert "[2]" not in frame
    # Verify labels and status are present
    assert "Пользователи" in frame
    assert "Настройки протоколов" in frame
    assert "test.com" in frame
    assert "●" in frame
