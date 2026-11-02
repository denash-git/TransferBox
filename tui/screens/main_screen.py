from __future__ import annotations
import sys
from rich.console import Console

from core.models.config import AppConfig
from core.models.service import ServiceStatus
from core.services.user_service import UserService
from core.services.service_manager import ServiceManager
from core.services.network_service import NetworkService
from core.services.backup_service import BackupService

from tui.components.menu import ArrowMenu, MenuItem
from tui.components.layout import get_block_padding
from .users_screen import UsersScreen
from .services_screen import ServicesScreen
from .backup_screen import BackupScreen
from .settings_screen import SettingsScreen

console = Console(highlight=False)


class MainScreen:
    def __init__(
        self,
        config: AppConfig,
        user_service: UserService,
        service_mgr: ServiceManager,
        network_service: NetworkService,
        backup_service: BackupService,
    ):
        self.config = config
        self.user_service = user_service
        self.service_mgr = service_mgr
        self.network_service = network_service
        self.backup_service = backup_service

        self.users_screen = UsersScreen(self.user_service, self.config)
        self.services_screen = ServicesScreen(self.service_mgr)
        self.backup_screen = BackupScreen(self.backup_service, self.config)
        self.settings_screen = SettingsScreen(self.network_service, self.config)

    def _get_status_lines(self) -> list[str]:
        # Services status
        caddy_status = self.service_mgr.get_service_status("caddy")
        singbox_status = self.service_mgr.get_service_status("sing-box")
        mieru_status = self.service_mgr.get_service_status("mita")

        def dot(st: ServiceStatus) -> str:
            color = "green" if st.is_healthy else "red"
            return f"[{color}]● {st.display_label}[/{color}]"

        lines = [
            f" [bold]Домен:[/bold] {self.config.domain}  [bold]IP:[/bold] {self.config.server_ip}",
            f" Caddy: {dot(caddy_status)}  Sing-Box: {dot(singbox_status)}  Mieru: {dot(mieru_status)}",
        ]
        return lines

    def run(self):
        while True:
            users_count = len(self.user_service.load_users())
            info_lines = self._get_status_lines()

            items = [
                MenuItem(
                    id="users",
                    label="Управление пользователями",
                    icon="👥",
                    extra=f"({users_count} активных)",
                ),
                MenuItem(
                    id="services",
                    label="Состояние служб & Управление",
                    icon="⚙️",
                ),
                MenuItem(
                    id="backup",
                    label="Резервное копирование и Восстановление",
                    icon="💾",
                ),
                MenuItem(
                    id="settings",
                    label="Системные настройки (SSH, BBR)",
                    icon="🛡️",
                ),
                MenuItem(
                    id="exit",
                    label="Завершить работу",
                    icon="🚪",
                ),
            ]

            menu = ArrowMenu(
                title="📦 TransferBox v4.0.0 (Python Edition)",
                subtitle="Панель Управления Прокси & VPN",
                items=items,
                info_lines=info_lines,
            )

            choice = menu.show()

            if choice in ("exit", "back", None):
                console.print(f"\n{get_block_padding()}[dim]Выход из TransferBox. Хорошего дня![/dim]\n")
                break
            elif choice == "users":
                self.users_screen.show()
            elif choice == "services":
                self.services_screen.show()
            elif choice == "backup":
                self.backup_screen.show()
            elif choice == "settings":
                self.settings_screen.show()
