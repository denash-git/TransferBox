from __future__ import annotations
from rich.console import Console

from core.models.config import AppConfig
from core.models.service import ServiceStatus
from core.services.user_service import UserService
from core.services.service_manager import ServiceManager
from core.services.network_service import NetworkService
from core.services.backup_service import BackupService
from core.services.diagnostics_service import DiagnosticsService

from tui.components.menu import ArrowMenu, MenuItem, StatusLine
from tui.components.layout import get_block_padding
from .users_screen import UsersScreen
from .services_screen import ServicesScreen
from .backup_screen import BackupScreen
from .settings_screen import SettingsScreen
from .diagnostics_screen import DiagnosticsScreen
from .bot_screen import BotScreen

console = Console(highlight=False)


class MainScreen:
    def __init__(
        self,
        config: AppConfig,
        user_service: UserService,
        service_mgr: ServiceManager,
        network_service: NetworkService,
        backup_service: BackupService,
        diagnostics_service: DiagnosticsService,
        env_save_callback=None,
    ):
        self.config = config
        self.user_service = user_service
        self.service_mgr = service_mgr
        self.network_service = network_service
        self.backup_service = backup_service
        self.diagnostics_service = diagnostics_service
        self.env_save_callback = env_save_callback

        self.users_screen = UsersScreen(self.user_service, self.config)
        self.services_screen = ServicesScreen(self.service_mgr)
        self.backup_screen = BackupScreen(self.backup_service, self.config)
        self.settings_screen = SettingsScreen(self.network_service, self.config)
        self.diagnostics_screen = DiagnosticsScreen(self.diagnostics_service)
        self.bot_screen = BotScreen(self.service_mgr, self.config, self.env_save_callback)

    def _get_status_lines(self) -> list[StatusLine]:
        caddy_st = self.service_mgr.get_service_status("caddy")
        singbox_st = self.service_mgr.get_service_status("sing-box")
        mieru_st = self.service_mgr.get_service_status("mita")
        bot_st = self.service_mgr.get_service_status("transferbox-bot")
        bbr_on = self.network_service.is_bbr_enabled()

        def dot_color(st: ServiceStatus) -> str:
            return "green" if st.is_healthy else "red"

        lines = [
            StatusLine(label="Домен:", value=self.config.domain),
            StatusLine(label="IP сервера:", value=self.config.server_ip),
            StatusLine(label="Caddy:", value=caddy_st.display_label, dot_color=dot_color(caddy_st)),
            StatusLine(label="sing-box:", value=singbox_st.display_label, dot_color=dot_color(singbox_st)),
            StatusLine(label="Mieru:", value=mieru_st.display_label, dot_color=dot_color(mieru_st)),
            StatusLine(label="Telegram Bot:", value=bot_st.display_label, dot_color=dot_color(bot_st)),
            StatusLine(label="TCP BBR:", value="активен" if bbr_on else "отключен", dot_color="green" if bbr_on else "red"),
        ]
        return lines

    def run(self):
        while True:
            users_count = len(self.user_service.load_users())
            status_lines = self._get_status_lines()

            items = [
                MenuItem(
                    id="users",
                    label="Пользователи",
                    extra=f"({users_count} активных)",
                ),
                MenuItem(
                    id="services",
                    label="Состояние служб & Управление",
                ),
                MenuItem(
                    id="bot",
                    label="Управление Telegram-ботом",
                ),
                MenuItem(
                    id="diagnostics",
                    label="Диагностика & Speedtest",
                ),
                MenuItem(
                    id="backup",
                    label="Бэкап и Восстановление",
                ),
                MenuItem(
                    id="settings",
                    label="Системные настройки (SSH, BBR)",
                ),
                MenuItem(
                    id="exit",
                    label="Выход",
                ),
            ]

            menu = ArrowMenu(
                title="TransferBox v4.0.0",
                subtitle="Панель Управления",
                items=items,
                status_lines=status_lines,
            )

            choice = menu.show()

            if choice in ("exit", "back", None):
                console.print(f"\n{get_block_padding()}[dim]Выход из TransferBox. До свидания![/dim]\n")
                break
            elif choice == "users":
                self.users_screen.show()
            elif choice == "services":
                self.services_screen.show()
            elif choice == "bot":
                self.bot_screen.show()
            elif choice == "diagnostics":
                self.diagnostics_screen.show()
            elif choice == "backup":
                self.backup_screen.show()
            elif choice == "settings":
                self.settings_screen.show()
