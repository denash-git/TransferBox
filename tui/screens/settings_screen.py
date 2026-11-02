from __future__ import annotations
from rich.console import Console

from core.models.config import AppConfig
from core.services.network_service import NetworkService
from tui.components.menu import ArrowMenu, MenuItem
from tui.components.dialogs import read_input, confirm_dialog, pause_prompt
from tui.components.layout import get_block_padding

console = Console(highlight=False)


class SettingsScreen:
    def __init__(self, network_service: NetworkService, config: AppConfig):
        self.network_service = network_service
        self.config = config

    def show(self):
        while True:
            bbr_status = "ВКЛЮЧЕН" if self.network_service.is_bbr_enabled() else "ОТКЛЮЧЕН"
            bbr_dot = "●" if self.network_service.is_bbr_enabled() else "○"

            items = [
                MenuItem(id="change_ssh", label=f"Порт SSH (Текущий: {self.config.ssh_port})", icon="🛡️"),
                MenuItem(id="toggle_bbr", label=f"Ускорение сети BBR ({bbr_dot} {bbr_status})", icon="⚡"),
                MenuItem(id="back", label="Назад в главное меню", icon="◀️"),
            ]

            menu = ArrowMenu(
                title="⚙️ Системные настройки и Сеть",
                subtitle=f"SSH: {self.config.ssh_port} | BBR: {bbr_status}",
                items=items,
            )
            choice = menu.show()

            if choice in ("back", None):
                break
            elif choice == "change_ssh":
                console.print()
                new_port_str = read_input(f"Введите новый порт SSH (1-65535, текущий: {self.config.ssh_port}):")
                if not new_port_str or not new_port_str.isdigit():
                    console.print(f"\n{get_block_padding()}[bold red]Некорректный порт.[/bold red]")
                    pause_prompt()
                    continue

                new_port = int(new_port_str)
                if confirm_dialog(f"Сменить порт SSH с {self.config.ssh_port} на {new_port}?"):
                    console.print(f"\n{get_block_padding()}[dim]Применение настроек с контролем UFW и проверкой отката...[/dim]")
                    ok, msg = self.network_service.change_ssh_port(new_port, self.config.ssh_port)
                    if ok:
                        self.config.ssh_port = new_port
                        console.print(f"{get_block_padding()}[bold green]✓ {msg}[/bold green]")
                    else:
                        console.print(f"{get_block_padding()}[bold red]✗ {msg}[/bold red]")
                    pause_prompt()
            elif choice == "toggle_bbr":
                if not self.network_service.is_bbr_enabled():
                    if confirm_dialog("Включить алгоритм BBR?"):
                        if self.network_service.enable_bbr():
                            console.print(f"\n{get_block_padding()}[bold green]✓ BBR успешно активирован.[/bold green]")
                        else:
                            console.print(f"\n{get_block_padding()}[bold red]✗ Не удалось включить BBR.[/bold red]")
                        pause_prompt()
                else:
                    console.print(f"\n{get_block_padding()}[bold yellow]BBR уже активен на данном сервере.[/bold yellow]")
                    pause_prompt()
