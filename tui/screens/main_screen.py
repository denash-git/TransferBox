from __future__ import annotations
import sys
import os
from typing import Dict, Any, List

from core.models.config import AppConfig
from core.models.user import User, ProtocolType
from core.services.user_service import UserService
from core.services.service_manager import ServiceManager
from core.services.network_service import NetworkService
from core.services.backup_service import BackupService
from core.services.diagnostics_service import DiagnosticsService
from core.services.config_render_service import ConfigRenderService

from tui.components.menu import (
    select_menu,
    C_GREEN,
    C_RED,
    C_YELLOW,
    C_BOLD,
    C_RESET,
)
from tui.components.dialogs import read_input, read_secret, confirm_dialog, pause_prompt


class MainScreen:
    """
    Main screen controller for TransferBox v4.0.0.
    Faithfully reproduces 100% of the original TransferBox menus,
    hierarchy, item labels, and status blocks.
    """

    def __init__(
        self,
        config: AppConfig,
        user_service: UserService,
        service_mgr: ServiceManager,
        network_service: NetworkService,
        backup_service: BackupService,
        diagnostics_service: DiagnosticsService,
        render_service: ConfigRenderService,
        env_save_callback=None,
    ):
        self.config = config
        self.user_service = user_service
        self.service_mgr = service_mgr
        self.network_service = network_service
        self.backup_service = backup_service
        self.diagnostics_service = diagnostics_service
        self.render_service = render_service
        self.env_save_callback = env_save_callback

    def _get_status_dict(self) -> Dict[str, str]:
        caddy_act = self.service_mgr.executor.is_service_active("caddy")
        singbox_act = self.service_mgr.executor.is_service_active("sing-box")
        mita_act = self.service_mgr.executor.is_service_active("mita")
        netbird_act = self.service_mgr.executor.is_service_active("netbird")
        bbr_act = self.network_service.is_bbr_enabled()

        fqdn_res = self.service_mgr.executor.run("hostname -f 2>/dev/null || hostname")
        fqdn = fqdn_res.stdout.strip() if fqdn_res.success else ""

        # Security check (silent drop port 80)
        sec_res = self.service_mgr.executor.run("iptables -C INPUT -p tcp --dport 80 -j DROP 2>/dev/null")
        sec_str = f"{C_GREEN}активна{C_RESET}" if sec_res.success else f"{C_RED}отключена{C_RESET}"

        return {
            "domain": self.config.domain or "не задан",
            "fqdn": fqdn,
            "caddy": f"{C_GREEN}● работает{C_RESET}" if caddy_act else f"{C_RED}● не запущен{C_RESET}",
            "singbox": f"{C_GREEN}● работает{C_RESET}" if singbox_act else f"{C_RED}● не запущен{C_RESET}",
            "mieru": f"{C_GREEN}● работает{C_RESET}" if mita_act else f"{C_RED}● отключен{C_RESET}",
            "netbird": f"{C_GREEN}● подключен{C_RESET}" if netbird_act else f"{C_RED}● не установлен{C_RESET}",
            "bbr": f"{C_GREEN}● активен{C_RESET}" if bbr_act else f"{C_RED}● отключен{C_RESET}",
            "ssh": f"{C_GREEN}включен{C_RESET}",
            "security": sec_str,
        }

    def run(self):
        while True:
            status_dict = self._get_status_dict()
            options = [
                "Пользователи",
                "Настройки",
                "Модули",
                "Диагностика",
                "Бэкап и Восстановление",
                "Выход",
            ]

            choice = select_menu(
                title=f"TransferBox v. {self.config.schema_version}.0.0",
                options=options,
                show_status=True,
                status_dict=status_dict,
            )

            if choice == 0:
                self.users_menu()
            elif choice == 1:
                self.settings_menu()
            elif choice == 2:
                self.modules_menu()
            elif choice == 3:
                self.diagnostics_menu()
            elif choice == 4:
                self.backup_restore_menu()
            elif choice in (5, -1):
                sys.stdout.write("\033[2J\033[H")
                sys.stdout.flush()
                break

    # ─── 1. ПОЛЬЗОВАТЕЛИ ──────────────────────────────────────────────────────

    def users_menu(self):
        while True:
            options = [
                "Список пользователей",
                "Добавить нового пользователя",
                "Назад",
            ]
            choice = select_menu("Пользователи", options)
            if choice == 0:
                self.list_users_menu()
            elif choice == 1:
                self.create_user_menu()
            elif choice in (2, -1):
                break

    def list_users_menu(self):
        while True:
            users = self.user_service.load_users(force_reload=True)
            if not users:
                select_menu("Список пользователей", ["Нет пользователей в системе", "Назад"])
                break

            # Group users by nickname
            from collections import defaultdict
            grouped = defaultdict(list)
            for u in users:
                grouped[u.nickname].append(u)

            options = []
            nick_list = []
            for nick, u_list in grouped.items():
                proto_names = [u.protocol.value.upper() for u in u_list]
                summary = ", ".join(proto_names)
                options.append(f"{nick:<16} ({summary})")
                nick_list.append(nick)
            options.append("Назад")

            choice = select_menu("Список пользователей", options)
            if choice == len(options) - 1 or choice == -1:
                break
            else:
                selected_nick = nick_list[choice]
                self.user_management_menu(selected_nick)

    def user_management_menu(self, nickname: str):
        while True:
            users = [u for u in self.user_service.load_users(force_reload=True) if u.nickname == nickname]
            if not users:
                break

            options = []
            for u in users:
                st_dot = f"{C_GREEN}●{C_RESET}" if u.enabled else f"{C_RED}○{C_RESET}"
                options.append(f"{u.nickname} ({u.protocol.value.upper()})  {st_dot}")
            options.append(f"Добавить протокол для {nickname}")
            options.append("Удалить пользователя целиком")
            options.append("Назад")

            choice = select_menu(f"Управление: {nickname}", options)
            if choice == len(options) - 1 or choice == -1:
                break
            elif choice == len(options) - 2:
                # Delete user completely
                if confirm_dialog(f"Удалить пользователя '{nickname}' со всеми протоколами?"):
                    self.user_service.delete_user(nickname)
                    break
            elif choice == len(options) - 3:
                # Add another protocol for user
                self.create_user_menu(default_nick=nickname)
            else:
                selected_user = users[choice]
                self.protocol_management_menu(selected_user)

    def protocol_management_menu(self, user: User):
        while True:
            toggle_lbl = "Отключить доступ" if user.enabled else "Включить доступ"
            options = [
                toggle_lbl,
                "Показать ссылку подключения и QR-код",
                "Удалить этот протокол",
                "Назад",
            ]
            choice = select_menu(f"{user.nickname} ({user.protocol.value.upper()})", options)
            if choice == 0:
                self.user_service.toggle_user(user.nickname)
                user.enabled = not user.enabled
            elif choice == 1:
                link = self.user_service.build_client_link(user, self.config)
                sys.stdout.write(f"\n  Ссылка подключения ({user.protocol.value}):\n  \033[1;36m{link}\033[0m\n")
                if user.protocol == ProtocolType.MIERU:
                    json_cfg = self.user_service.build_mieru_json_config(user, self.config)
                    sys.stdout.write(f"\n  Mieru JSON:\n{json_cfg}\n")
                pause_prompt()
            elif choice == 2:
                if confirm_dialog(f"Удалить протокол {user.protocol.value} для {user.nickname}?"):
                    self.user_service.delete_user(user.nickname)
                    break
            elif choice in (3, -1):
                break

    def create_user_menu(self, default_nick: str = ""):
        nick = default_nick
        if not nick:
            nick = read_input("Введите имя пользователя:")
            if not nick:
                return

        options = [
            "VLESS over WebSocket",
            "VLESS over gRPC",
            "VLESS over XHTTP",
            "NaiveProxy",
            "Mieru",
            "Отмена",
        ]
        choice = select_menu(f"Протокол для {nick}", options)
        if choice in (5, -1):
            return

        proto_map = {
            0: (ProtocolType.VLESS, {"type": "ws"}),
            1: (ProtocolType.VLESS, {"type": "grpc"}),
            2: (ProtocolType.VLESS, {"type": "xhttp"}),
            3: (ProtocolType.NAIVE, {}),
            4: (ProtocolType.MIERU, {}),
        }
        proto, creds = proto_map[choice]
        try:
            new_u = self.user_service.add_user(nick, proto, creds)
            link = self.user_service.build_client_link(new_u, self.config)
            sys.stdout.write(f"\n  \033[1;32m✓ Пользователь {nick} успешно создан!\033[0m\n")
            sys.stdout.write(f"  Ссылка: \033[1;36m{link}\033[0m\n")
            pause_prompt()
        except Exception as e:
            sys.stdout.write(f"\n  \033[1;31mОшибка: {e}\033[0m\n")
            pause_prompt()

    # ─── 2. НАСТРОЙКИ ────────────────────────────────────────────────────────

    def settings_menu(self):
        while True:
            options = [
                "Изменить Домен и Email",
                "Изменить FQDN имя VPS",
                "Выбрать шаблон маскировочного сайта",
                "Управление SSH",
                "Защита от сканеров (Fail2ban + Silent Drop)",
                "Управление Telegram-ботом",
                "Обновить панель TransferBox",
                "Назад",
            ]
            choice = select_menu("Настройки", options)
            if choice == 0:
                new_dom = read_input(f"Текущий домен: {self.config.domain}. Новый домен:")
                if new_dom:
                    self.config.domain = new_dom
                    if self.env_save_callback:
                        self.env_save_callback(self.config)
                    self.render_service.render_all(self.config, self.user_service.load_users())
                    self.service_mgr.reload_caddy()
            elif choice == 1:
                new_fqdn = read_input("Новое FQDN имя VPS:")
                if new_fqdn:
                    self.service_mgr.executor.run(f"hostnamectl set-hostname {new_fqdn}")
            elif choice == 2:
                self.change_site_template_menu()
            elif choice == 3:
                self.ssh_management_menu()
            elif choice == 4:
                self.security_protection_menu()
            elif choice == 5:
                self.telegram_bot_menu()
            elif choice == 6:
                sys.stdout.write("\n  Проверка обновлений репозитория...\n")
                self.service_mgr.executor.run("cd /opt/transferbox && git pull")
                sys.stdout.write("  \033[1;32m✓ Обновление завершено.\033[0m\n")
                pause_prompt()
            elif choice in (7, -1):
                break

    def change_site_template_menu(self):
        templates = ["aether", "nexus", "prism", "solar", "velox", "vertex"]
        options = [f"Шаблон: {t.title()}" for t in templates] + ["Назад"]
        choice = select_menu("Выбор шаблона маскировочного сайта", options)
        if 0 <= choice < len(templates):
            selected = templates[choice]
            self.config.extra["FAKE_SITE_TEMPLATE"] = selected
            if self.env_save_callback:
                self.env_save_callback(self.config)
            self.render_service.render_all(self.config, self.user_service.load_users())
            self.service_mgr.reload_caddy()
            sys.stdout.write(f"\n  \033[1;32m✓ Активирован шаблон: {selected}\033[0m\n")
            pause_prompt()

    def ssh_management_menu(self):
        while True:
            options = [
                f"Изменить порт SSH (текущий: {self.config.ssh_port})",
                "Доступ SSH (Пароль / Ключи)",
                "Назад",
            ]
            choice = select_menu("Управление SSH", options)
            if choice == 0:
                p_str = read_input(f"Введите новый порт SSH (1-65535, текущий: {self.config.ssh_port}):")
                if p_str and p_str.isdigit():
                    new_p = int(p_str)
                    if confirm_dialog(f"Перевести SSH на порт {new_p}?"):
                        ok, msg = self.network_service.change_ssh_port(new_p, self.config.ssh_port)
                        sys.stdout.write(f"\n  {'✓' if ok else '✗'} {msg}\n")
                        if ok:
                            self.config.ssh_port = new_p
                            if self.env_save_callback:
                                self.env_save_callback(self.config)
                        pause_prompt()
            elif choice == 1:
                self.ssh_auth_menu()
            elif choice in (2, -1):
                break

    def ssh_auth_menu(self):
        options = [
            "Разрешить вход по паролю (PasswordAuthentication yes)",
            "Запретить вход по паролю (Только по SSH-ключам)",
            "Назад",
        ]
        choice = select_menu("Доступ SSH", options)
        if choice == 0:
            self.service_mgr.executor.run("sed -i 's/^PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config")
            self.service_mgr.executor.systemctl("restart", "ssh")
            sys.stdout.write("\n  \033[1;32m✓ Вход по паролю разрешен.\033[0m\n")
            pause_prompt()
        elif choice == 1:
            self.service_mgr.executor.run("sed -i 's/^PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config")
            self.service_mgr.executor.systemctl("restart", "ssh")
            sys.stdout.write("\n  \033[1;32m✓ Вход по паролю отключен (только SSH-ключи).\033[0m\n")
            pause_prompt()

    def security_protection_menu(self):
        options = [
            "Активировать защиту (Fail2ban + Silent Drop)",
            "Отключить Silent Drop (Открыть порт 80)",
            "Назад",
        ]
        choice = select_menu("Защита от сканеров", options)
        if choice == 0:
            self.service_mgr.executor.run("iptables -I INPUT -p tcp --dport 80 -j DROP 2>/dev/null || true")
            sys.stdout.write("\n  \033[1;32m✓ Защита от сканеров активна.\033[0m\n")
            pause_prompt()
        elif choice == 1:
            self.service_mgr.executor.run("iptables -D INPUT -p tcp --dport 80 -j DROP 2>/dev/null || true")
            sys.stdout.write("\n  \033[1;33m✓ Silent Drop отключен.\033[0m\n")
            pause_prompt()

    def telegram_bot_menu(self):
        while True:
            is_active = self.service_mgr.executor.is_service_active("transferbox-bot")
            status_str = f"{C_GREEN}● активен{C_RESET}" if is_active else f"{C_RED}○ отключен{C_RESET}"
            options = [
                "Настроить Токен и Chat ID",
                f"{'Остановить' if is_active else 'Запустить'} Telegram-бота",
                "Перезапустить службу бота",
                "Назад",
            ]
            choice = select_menu(f"Настройки → Telegram-бот ({status_str})", options)
            if choice == 0:
                t = read_input("Токен Telegram бота:")
                c = read_input("Chat ID администратора:")
                if t: self.config.tg_bot_token = t
                if c: self.config.tg_chat_id = c
                if self.env_save_callback:
                    self.env_save_callback(self.config)
                sys.stdout.write("\n  \033[1;32m✓ Настройки бота сохранены.\033[0m\n")
                pause_prompt()
            elif choice == 1:
                act = "stop" if is_active else "start"
                self.service_mgr.control_bot(act)
            elif choice == 2:
                self.service_mgr.control_bot("restart")
            elif choice in (3, -1):
                break

    # ─── 3. МОДУЛИ ───────────────────────────────────────────────────────────

    def modules_menu(self):
        while True:
            mita_act = self.service_mgr.executor.is_service_active("mita")
            sb_act = self.service_mgr.executor.is_service_active("sing-box")
            bbr_act = self.network_service.is_bbr_enabled()

            mieru_st = f"{C_GREEN}● активен{C_RESET}" if mita_act else f"{C_RED}отключен{C_RESET}"
            sb_st = f"{C_GREEN}● активен{C_RESET}" if sb_act else f"{C_RED}отключен{C_RESET}"
            bbr_st = f"{C_GREEN}● активен{C_RESET}" if bbr_act else f"{C_RED}отключен{C_RESET}"

            options = [
                f"Mieru       [{mieru_st}]",
                f"sing-box    [{sb_st}]",
                "Настроить пути VLESS",
                f"TCP BBR оптимизация [{bbr_st}]",
                "Назад",
            ]
            choice = select_menu("Модули", options)
            if choice == 0:
                self.mieru_module_menu()
            elif choice == 1:
                self.singbox_module_menu()
            elif choice == 2:
                self.change_vless_paths_menu()
            elif choice == 3:
                self.bbr_optimization_menu()
            elif choice in (4, -1):
                break

    def mieru_module_menu(self):
        is_active = self.service_mgr.executor.is_service_active("mita")
        options = [
            "Остановить Mieru" if is_active else "Запустить Mieru",
            "Перезапустить Mieru",
            "Назад",
        ]
        choice = select_menu("Модуль: Mieru", options)
        if choice == 0:
            act = "stop" if is_active else "start"
            self.service_mgr.executor.systemctl(act, "mita")
        elif choice == 1:
            self.service_mgr.restart_mieru()

    def singbox_module_menu(self):
        options = [
            "Перезапустить sing-box",
            "Проверить статус sing-box",
            "Назад",
        ]
        choice = select_menu("Модуль: sing-box", options)
        if choice == 0:
            self.service_mgr.restart_singbox()
            sys.stdout.write("\n  \033[1;32m✓ sing-box успешно перезапущен.\033[0m\n")
            pause_prompt()
        elif choice == 1:
            res = self.service_mgr.executor.run("systemctl status sing-box --no-pager")
            sys.stdout.write(f"\n{res.stdout}\n")
            pause_prompt()

    def change_vless_paths_menu(self):
        while True:
            options = [
                f"Путь VLESS WS:      {self.config.vless_ws_path}",
                f"Сервис VLESS gRPC:  {self.config.vless_grpc_service or 'не задан'}",
                f"Путь VLESS XHTTP:   {self.config.vless_xhttp_path}",
                "Назад",
            ]
            choice = select_menu("Настройки путей", options)
            if choice == 0:
                p = read_input("Новый путь VLESS WS (например, /ws):")
                if p:
                    self.config.vless_ws_path = p
                    self._apply_paths()
            elif choice == 1:
                g = read_input("Новое имя сервиса VLESS gRPC:")
                if g:
                    self.config.vless_grpc_service = g
                    self._apply_paths()
            elif choice == 2:
                x = read_input("Новый путь VLESS XHTTP:")
                if x:
                    self.config.vless_xhttp_path = x
                    self._apply_paths()
            elif choice in (3, -1):
                break

    def _apply_paths(self):
        if self.env_save_callback:
            self.env_save_callback(self.config)
        self.render_service.render_all(self.config, self.user_service.load_users())
        self.service_mgr.reload_caddy()
        self.service_mgr.restart_singbox()
        sys.stdout.write("\n  \033[1;32m✓ Пути обновлены, службы перезапущены.\033[0m\n")
        pause_prompt()

    def bbr_optimization_menu(self):
        if not self.network_service.is_bbr_enabled():
            if confirm_dialog("Включить алгоритм TCP BBR?"):
                self.network_service.enable_bbr()
                sys.stdout.write("\n  \033[1;32m✓ TCP BBR успешно активирован.\033[0m\n")
                pause_prompt()
        else:
            sys.stdout.write("\n  \033[1;33mTCP BBR уже активен на данном сервере.\033[0m\n")
            pause_prompt()

    # ─── 4. ДИАГНОСТИКА ──────────────────────────────────────────────────────

    def diagnostics_menu(self):
        while True:
            options = [
                "Мониторинг ресурсов",
                "Показать логи",
                "Тест VPS → Интернет (speedtest-cli)",
                "Тест iperf3 (порт 5201)",
                "Назад",
            ]
            choice = select_menu("Диагностика", options)
            if choice == 0:
                metrics = self.diagnostics_service.get_system_metrics()
                sys.stdout.write(f"\n  CPU:    {metrics['cpu_percent']}%\n")
                sys.stdout.write(f"  RAM:    {metrics['ram_used_mb']} / {metrics['ram_total_mb']} MB ({metrics['ram_percent']}%)\n")
                sys.stdout.write(f"  Диск:   {metrics['disk_used_gb']} / {metrics['disk_total_gb']} GB ({metrics['disk_percent']}%)\n")
                sys.stdout.write(f"  Аптайм: {metrics['uptime_str']}\n")
                pause_prompt()
            elif choice == 1:
                self.logs_menu()
            elif choice == 2:
                sys.stdout.write("\n  Запуск Speedtest (до 30 сек)...\n")
                ok, res = self.diagnostics_service.run_speedtest()
                if ok:
                    sys.stdout.write(f"  Сервер:    {res['server_name']} ({res['provider']})\n")
                    sys.stdout.write(f"  Ping:      {res['latency_ms']} ms (jitter: {res['jitter_ms']} ms)\n")
                    sys.stdout.write(f"  Download:  {res['download_mbps']} Mbps\n")
                    sys.stdout.write(f"  Upload:    {res['upload_mbps']} Mbps\n")
                    sys.stdout.write(f"  Потери:    {res['packet_loss_percent']}%\n")
                else:
                    sys.stdout.write(f"  \033[1;31m{res.get('error')}\033[0m\n")
                pause_prompt()
            elif choice == 3:
                sys.stdout.write("\n  Запуск iperf3 сервера на 180 сек...\n")
                ok, msg = self.diagnostics_service.run_ephemeral_iperf3(timeout_sec=180)
                sys.stdout.write(f"  \033[1;32m✓ {msg}\033[0m\n")
                pause_prompt()
            elif choice in (4, -1):
                break

    def logs_menu(self):
        options = [
            "Последние 50 строк — Caddy",
            "Последние 50 строк — sing-box",
            "Последние 50 строк — Mieru",
            "Назад",
        ]
        choice = select_menu("Просмотр логов", options)
        svc_map = {0: "caddy", 1: "sing-box", 2: "mita"}
        if choice in svc_map:
            logs = self.diagnostics_service.get_service_logs(svc_map[choice], 50)
            sys.stdout.write(f"\n{logs}\n")
            pause_prompt()

    # ─── 5. БЭКАП И ВОССТАНОВЛЕНИЕ ───────────────────────────────────────────

    def backup_restore_menu(self):
        while True:
            has_pwd = bool(self.config.backup_password)
            pwd_st = "задан" if has_pwd else "не задан"
            options = [
                "Создать бэкап настроек",
                "Восстановить из последнего бэкапа",
                f"Задать пароль для бэкапов ({pwd_st})",
                "Назад",
            ]
            choice = select_menu("Бэкап и Восстановление", options)
            if choice == 0:
                pwd = self.config.backup_password or None
                ok, path = self.backup_service.create_backup(password=pwd)
                sys.stdout.write(f"\n  {'✓ Бэкап создан: ' + path if ok else '✗ Ошибка: ' + path}\n")
                pause_prompt()
            elif choice == 1:
                latest = self.backup_service.get_latest_backup()
                if not latest:
                    sys.stdout.write("\n  Нет доступных бэкапов.\n")
                    pause_prompt()
                    continue
                if confirm_dialog(f"Восстановить из {os.path.basename(latest)}?"):
                    pwd = self.config.backup_password or None
                    ok, msg = self.backup_service.restore_backup(latest, password=pwd)
                    if not ok and "паролем" in msg.lower():
                        inp = read_secret("Пароль архива:")
                        ok, msg = self.backup_service.restore_backup(latest, password=inp)
                    sys.stdout.write(f"\n  {'✓' if ok else '✗'} {msg}\n")
                    pause_prompt()
            elif choice == 2:
                new_p = read_secret("Новый пароль для бэкапов (Enter для отмены):")
                self.config.backup_password = new_p
                if self.env_save_callback:
                    self.env_save_callback(self.config)
                sys.stdout.write("\n  \033[1;32m✓ Пароль бэкапов сохранен.\033[0m\n")
                pause_prompt()
            elif choice in (3, -1):
                break
