from __future__ import annotations
from rich.console import Console

from core.services.service_manager import ServiceManager
from tui.components.menu import ArrowMenu, MenuItem
from tui.components.dialogs import pause_prompt
from tui.components.layout import get_block_padding

console = Console(highlight=False)


class ServicesScreen:
    def __init__(self, service_mgr: ServiceManager):
        self.service_mgr = service_mgr

    def show(self):
        while True:
            services = self.service_mgr.get_all_services()
            items = []
            for s in services:
                dot = "●" if s.status.is_healthy else "●"
                extra = f"{dot} {s.status.display_label}"
                items.append(MenuItem(
                    id=f"service_{s.name}",
                    label=s.display_name,
                    extra=extra,
                ))

            items.extend([
                MenuItem(id="reload_caddy", label="Перезагрузить Caddy (Reload с валидацией)"),
                MenuItem(id="restart_singbox", label="Перезапустить Sing-Box"),
                MenuItem(id="restart_mieru", label="Перезапустить Mieru (mita)"),
                MenuItem(id="back", label="Назад в главное меню"),
            ])

            menu = ArrowMenu(
                title="Состояние системных служб",
                subtitle="Caddy, Sing-box, Mieru & Telegram Bot",
                items=items,
            )
            choice = menu.show()

            if choice in ("back", None):
                break
            elif choice == "reload_caddy":
                console.print(f"\n{get_block_padding()}[dim]Валидация Caddyfile и мягкий reload...[/dim]")
                if self.service_mgr.reload_caddy():
                    console.print(f"{get_block_padding()}[bold green]✓ Caddy успешно перезагружен без обрыва соединений![/bold green]")
                else:
                    console.print(f"{get_block_padding()}[bold red]✗ Ошибка конфигурации Caddyfile. Перезапуск отменен.[/bold red]")
                pause_prompt()
            elif choice == "restart_singbox":
                if self.service_mgr.restart_singbox():
                    console.print(f"\n{get_block_padding()}[bold green]✓ Sing-box успешно перезапущен.[/bold green]")
                else:
                    console.print(f"\n{get_block_padding()}[bold red]✗ Сбой перезапуска Sing-box.[/bold red]")
                pause_prompt()
            elif choice == "restart_mieru":
                if self.service_mgr.restart_mieru():
                    console.print(f"\n{get_block_padding()}[bold green]✓ Mieru успешно перезапущен.[/bold green]")
                else:
                    console.print(f"\n{get_block_padding()}[bold red]✗ Сбой перезапуска Mieru.[/bold red]")
                pause_prompt()
