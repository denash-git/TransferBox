from __future__ import annotations
from rich.console import Console

from core.models.config import AppConfig
from core.services.backup_service import BackupService
from tui.components.menu import ArrowMenu, MenuItem
from tui.components.dialogs import read_secret, confirm_dialog, pause_prompt
from tui.components.layout import get_block_padding

console = Console(highlight=False)


class BackupScreen:
    def __init__(self, backup_service: BackupService, config: AppConfig):
        self.backup_service = backup_service
        self.config = config

    def show(self):
        while True:
            backups = self.backup_service.list_backups()
            has_pwd = bool(self.config.backup_password)
            pwd_status = "задан" if has_pwd else "не задан"

            items = [
                MenuItem(id="create_backup", label="Создать бэкап настроек", icon="💾"),
                MenuItem(id="set_password", label=f"Пароль шифрования ({pwd_status})", icon="🔒"),
                MenuItem(id="restore", label="Восстановить из последнего бэкапа", icon="📦"),
                MenuItem(id="list", label=f"Список архивов ({len(backups)})", icon="📋"),
                MenuItem(id="back", label="Назад в главное меню", icon="◀️"),
            ]

            menu = ArrowMenu(
                title="💾 Резервное копирование и Восстановление",
                subtitle=f"Шифрование: {pwd_status.upper()} | Архивов: {len(backups)}",
                items=items,
            )
            choice = menu.show()

            if choice in ("back", None):
                break
            elif choice == "create_backup":
                pwd = self.config.backup_password or None
                ok, path = self.backup_service.create_backup(password=pwd)
                if ok:
                    console.print(f"\n{get_block_padding()}[bold green]✓ Бэкап успешно создан:[/bold green]")
                    console.print(f"{get_block_padding()}[cyan]{path}[/cyan]")
                else:
                    console.print(f"\n{get_block_padding()}[bold red]Ошибка создания бэкапа: {path}[/bold red]")
                pause_prompt()
            elif choice == "set_password":
                console.print()
                new_pwd = read_secret("Введите новый пароль для бэкапов (Enter для очистки):")
                self.config.backup_password = new_pwd
                console.print(f"\n{get_block_padding()}[bold green]✓ Пароль обновлен.[/bold green]")
                pause_prompt()
            elif choice == "restore":
                latest = self.backup_service.get_latest_backup()
                if not latest:
                    console.print(f"\n{get_block_padding()}[bold yellow]Нет доступных бэкапов для восстановления.[/bold yellow]")
                    pause_prompt()
                    continue

                if confirm_dialog(f"Восстановить конфигурацию из {latest}?"):
                    pwd = self.config.backup_password or None
                    ok, msg = self.backup_service.restore_backup(latest, password=pwd)
                    if not ok and "паролем" in msg.lower():
                        input_pwd = read_secret("Введите пароль для архива:")
                        ok, msg = self.backup_service.restore_backup(latest, password=input_pwd)

                    if ok:
                        console.print(f"\n{get_block_padding()}[bold green]✓ {msg}[/bold green]")
                    else:
                        console.print(f"\n{get_block_padding()}[bold red]✗ {msg}[/bold red]")
                    pause_prompt()
            elif choice == "list":
                console.print(f"\n{get_block_padding()}[bold white]Сохраненные бэкапы:[/bold white]")
                for b in backups[:10]:
                    tag = " [bold purple][PRE-UPDATE][/bold purple]" if b["is_pre_update"] else ""
                    console.print(f"{get_block_padding()}• [cyan]{b['filename']}[/cyan] ({b['size_kb']} KB, {b['mtime']}){tag}")
                console.print()
                pause_prompt()
