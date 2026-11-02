from __future__ import annotations
from typing import Optional
from rich.console import Console

from core.models.user import ProtocolType
from core.models.config import AppConfig
from core.services.user_service import UserService
from tui.components.menu import ArrowMenu, MenuItem
from tui.components.dialogs import read_input, confirm_dialog, pause_prompt
from tui.components.layout import get_block_padding

console = Console(highlight=False)


class UsersScreen:
    def __init__(self, user_service: UserService, config: AppConfig):
        self.user_service = user_service
        self.config = config

    def show(self):
        while True:
            users = self.user_service.load_users(force_reload=True)
            user_items = []
            for u in users:
                status_dot = "●" if u.enabled else "○"
                extra = f"{status_dot} {u.protocol.value.upper()}"
                user_items.append(MenuItem(
                    id=f"user_{u.nickname}",
                    label=f"  {u.nickname}",
                    extra=extra,
                ))

            menu_items = [
                MenuItem(id="add_user", label="[+] Добавить пользователя"),
            ]
            menu_items.extend(user_items)
            menu_items.append(MenuItem(id="back", label="Назад в главное меню"))

            menu = ArrowMenu(
                title="Управление пользователями",
                subtitle=f"Всего пользователей: {len(users)}",
                items=menu_items,
            )
            choice = menu.show()

            if choice in ("back", None):
                break
            elif choice == "add_user":
                self._add_user_flow()
            elif choice and choice.startswith("user_"):
                nick = choice.replace("user_", "", 1).strip()
                self._user_card_flow(nick)

    def _add_user_flow(self):
        console.print()
        nick = read_input("Имя нового пользователя:")
        if not nick:
            return

        if self.user_service.get_user_by_name(nick):
            console.print(f"\n{get_block_padding()}[bold red]Ошибка: Пользователь '{nick}' уже существует![/bold red]")
            pause_prompt()
            return

        proto_menu = ArrowMenu(
            title="Выбор протокола",
            subtitle=f"Пользователь: {nick}",
            items=[
                MenuItem(id="vless", label="VLESS (WebSocket / gRPC / XHTTP)"),
                MenuItem(id="naive", label="NaiveProxy (HTTPS)"),
                MenuItem(id="mieru", label="Mieru (mita)"),
                MenuItem(id="back", label="Отмена"),
            ]
        )
        proto_choice = proto_menu.show()
        if proto_choice in ("back", None):
            return

        try:
            proto = ProtocolType(proto_choice)
            new_user = self.user_service.add_user(nick, proto)
            console.print(f"\n{get_block_padding()}[bold green]✓ Пользователь '{nick}' успешно создан![/bold green]")
            link = self.user_service.build_client_link(new_user, self.config)
            console.print(f"{get_block_padding()}[dim]Ссылка подключения:[/dim]\n{get_block_padding()}[cyan]{link}[/cyan]\n")
        except Exception as e:
            console.print(f"\n{get_block_padding()}[bold red]Ошибка создания пользователя: {e}[/bold red]")

        pause_prompt()

    def _user_card_flow(self, nickname: str):
        while True:
            user = self.user_service.get_user_by_name(nickname)
            if not user:
                break

            status_str = "● активен" if user.enabled else "○ отключен"
            toggle_label = "Отключить доступ" if user.enabled else "Включить доступ"

            card_menu = ArrowMenu(
                title=f"Карточка: {user.nickname}",
                subtitle=f"{user.protocol.value.upper()} | {status_str}",
                items=[
                    MenuItem(id="show_link", label="Показать ссылку подключения"),
                    MenuItem(id="toggle", label=toggle_label),
                    MenuItem(id="delete", label="Удалить пользователя"),
                    MenuItem(id="back", label="Назад к списку"),
                ]
            )
            action = card_menu.show()

            if action in ("back", None):
                break
            elif action == "show_link":
                link = self.user_service.build_client_link(user, self.config)
                console.print(f"\n{get_block_padding()}[bold white]Ссылка подключения ({user.protocol.value}):[/bold white]")
                console.print(f"{get_block_padding()}[cyan]{link}[/cyan]\n")
                if user.protocol == ProtocolType.MIERU:
                    json_cfg = self.user_service.build_mieru_json_config(user, self.config)
                    console.print(f"{get_block_padding()}[dim]Mieru JSON Config:[/dim]")
                    console.print(f"{get_block_padding()}{json_cfg}\n")
                pause_prompt()
            elif action == "toggle":
                self.user_service.toggle_user(user.nickname)
            elif action == "delete":
                if confirm_dialog(f"Удалить пользователя '{user.nickname}'?"):
                    self.user_service.delete_user(user.nickname)
                    console.print(f"\n{get_block_padding()}[bold green]Пользователь удален.[/bold green]")
                    pause_prompt()
                    break
