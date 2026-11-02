from __future__ import annotations
from rich.console import Console

from core.models.config import AppConfig
from core.services.service_manager import ServiceManager
from tui.components.menu import ArrowMenu, MenuItem
from tui.components.dialogs import read_input, pause_prompt
from tui.components.layout import get_block_padding

console = Console(highlight=False)


class BotScreen:
    def __init__(self, service_mgr: ServiceManager, config: AppConfig, env_save_callback=None):
        self.service_mgr = service_mgr
        self.config = config
        self.env_save_callback = env_save_callback

    def show(self):
        while True:
            is_active = self.service_mgr.executor.is_service_active("transferbox-bot")
            status_str = "● активен" if is_active else "○ отключен"
            toggle_action = "Остановить бота" if is_active else "Запустить бота"

            token_masked = f"{self.config.tg_bot_token[:6]}...{self.config.tg_bot_token[-4:]}" if self.config.tg_bot_token else "не задан"
            chat_id_val = self.config.tg_chat_id or "не задан"

            items = [
                MenuItem(id="set_token", label=f"Токен бота: {token_masked}"),
                MenuItem(id="set_chat_id", label=f"Chat ID администратора: {chat_id_val}"),
                MenuItem(id="toggle_bot", label=toggle_action),
                MenuItem(id="restart_bot", label="Перезапустить службу бота"),
                MenuItem(id="back", label="Назад в главное меню"),
            ]

            menu = ArrowMenu(
                title="Управление Telegram-ботом",
                subtitle=f"Статус службы: {status_str}",
                items=items,
            )
            choice = menu.show()

            if choice in ("back", None):
                break
            elif choice == "set_token":
                console.print()
                tok = read_input("Введите токен Telegram бота (от @BotFather):")
                if tok:
                    self.config.tg_bot_token = tok
                    if self.env_save_callback:
                        self.env_save_callback(self.config)
                    console.print(f"\n{get_block_padding()}[bold green]✓ Токен бота сохранен.[/bold green]")
                    pause_prompt()
            elif choice == "set_chat_id":
                console.print()
                cid = read_input("Введите Chat ID администратора:")
                if cid:
                    self.config.tg_chat_id = cid
                    if self.env_save_callback:
                        self.env_save_callback(self.config)
                    console.print(f"\n{get_block_padding()}[bold green]✓ Chat ID сохранен.[/bold green]")
                    pause_prompt()
            elif choice == "toggle_bot":
                act = "stop" if is_active else "start"
                ok = self.service_mgr.control_bot(act)
                console.print(f"\n{get_block_padding()}[bold {'green' if ok else 'red'}]Служба бота: {act} -> {'Успех' if ok else 'Ошибка'}[/bold {'green' if ok else 'red'}]")
                pause_prompt()
            elif choice == "restart_bot":
                ok = self.service_mgr.control_bot("restart")
                console.print(f"\n{get_block_padding()}[bold {'green' if ok else 'red'}]Служба бота перезапущена: {'Успех' if ok else 'Ошибка'}[/bold {'green' if ok else 'red'}]")
                pause_prompt()
