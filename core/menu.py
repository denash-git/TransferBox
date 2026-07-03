#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
from core.config_manager import load_env, save_env, load_users, render_configs, validate_and_restart
from core.user_manager import add_user, delete_user, toggle_user, build_client_link, print_qr_code
import builtins

# Force unbuffered output for instant terminal updates over SSH
def print(*args, **kwargs):
    kwargs.setdefault('flush', True)
    builtins.print(*args, **kwargs)

# ANSI Colors
BLUE   = '\033[1;34m'
GREEN  = '\033[1;32m'
RED    = '\033[1;31m'
YELLOW = '\033[1;33m'
CYAN   = '\033[1;36m'
DIM    = '\033[2m'
BOLD   = '\033[1m'
RESET  = '\033[0m'

PROTOCOL_LABELS = {
    ("naive",  None):    "NaiveProxy",
    ("vless",  "ws"):    "VLESS over WebSocket",
    ("vless",  "grpc"):  "VLESS over gRPC",
    ("vless",  "xhttp"): "VLESS over XHTTP",
}

def protocol_label(user):
    proto = user.get("protocol")
    utype = user.get("credentials", {}).get("type")
    return PROTOCOL_LABELS.get((proto, utype), proto.upper())

def clear_screen():
    print('\033[2J\033[H', end='')

def pause():
    input(f"\n  {DIM}Нажмите Enter для продолжения...{RESET}")

def get_service_status(service_name):
    try:
        res = subprocess.run(["systemctl", "is-active", service_name], capture_output=True, text=True)
        status = res.stdout.strip()
        if status == "active":
            return f"{GREEN}● работает{RESET}"
        return f"{RED}● не запущен ({status}){RESET}"
    except Exception:
        return f"{DIM}● не установлен{RESET}"

def print_header(title):
    clear_screen()
    env = load_env()
    domain = env.get("DOMAIN", "не задан")
    width = 60
    print(f"{BLUE}═" * width + f"{RESET}")
    print(f"{BOLD}  {title:<56}{RESET}")
    print(f"{BLUE}─" * width + f"{RESET}")
    print(f"  {YELLOW}Домен:{RESET} {domain}")
    print(f"  {YELLOW}Caddy:{RESET} {get_service_status('caddy')}")
    print(f"  {YELLOW}sing-box:{RESET} {get_service_status('sing-box')}")
    print(f"{BLUE}═" * width + f"{RESET}\n")

def get_menu_choice(prompt="  Выбор: "):
    try:
        val = input(prompt).strip()
        if val == "00":
            print(f"\n  {DIM}До свидания!{RESET}\n")
            sys.exit(0)
        return val
    except (KeyboardInterrupt, EOFError):
        print(f"\n  {DIM}До свидания!{RESET}\n")
        sys.exit(0)

# ─── Главное меню ────────────────────────────────────────────────────────────

def main_menu():
    while True:
        print_header("TransferBox — Панель Управления")
        print(f"  {CYAN}1){RESET} Пользователи")
        print(f"  {CYAN}2){RESET} Настройки")
        print(f"  {CYAN}3){RESET} Перезапустить службы")
        print(f"  {CYAN}4){RESET} Показать логи")
        print(f"\n  {DIM}00) Выход{RESET}\n")

        choice = get_menu_choice()
        if choice == "1":
            users_menu()
        elif choice == "2":
            settings_menu()
        elif choice == "3":
            apply_settings_menu()
        elif choice == "4":
            logs_menu()

# ─── Меню пользователей ──────────────────────────────────────────────────────

def users_menu():
    while True:
        print_header("Пользователи")
        print(f"  {CYAN}1){RESET} Список пользователей")
        print(f"  {CYAN}2){RESET} Новый пользователь")
        print(f"\n  {DIM}0) Назад{RESET}\n")

        choice = get_menu_choice()
        if choice == "0":
            return
        elif choice == "1":
            list_users_menu()
        elif choice == "2":
            create_user_menu()

def list_users_menu():
    while True:
        print_header("Список пользователей")
        users = load_users()

        if not users:
            print("  Пользователей пока нет.")
            pause()
            return

        for idx, u in enumerate(users, 1):
            label  = protocol_label(u)
            status = f"{GREEN}активен{RESET}" if u.get("enabled", True) else f"{RED}отключен{RESET}"
            print(f"  {idx}) {BOLD}{u.get('nickname')}{RESET} ({label}) — {status}")

        print(f"\n  {DIM}0) Назад{RESET}\n")
        choice = get_menu_choice()

        if choice == "0" or not choice:
            return

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(users):
                user_action_menu(users[idx])
            else:
                print(f"  {RED}Неверный номер.{RESET}")
                pause()
        except ValueError:
            print(f"  {RED}Введите число.{RESET}")
            pause()

def user_action_menu(u):
    while True:
        print_header(f"Пользователь: {u.get('nickname')}")
        label  = protocol_label(u)
        active = u.get("enabled", True)
        status = f"{GREEN}активен{RESET}" if active else f"{RED}отключен{RESET}"

        print(f"  Протокол : {BOLD}{label}{RESET}")
        print(f"  Статус   : {status}\n")

        toggle_label = "Отключить" if active else "Включить"

        print(f"  {CYAN}1){RESET} Показать QR и ссылку")
        print(f"  {CYAN}2){RESET} {toggle_label}")
        print(f"  {CYAN}3){RESET} Удалить")
        print(f"\n  {DIM}0) Назад{RESET}\n")

        choice = get_menu_choice()

        if choice == "0":
            return
        elif choice == "1":
            show_qr_menu(u)
        elif choice == "2":
            new_state = not active
            toggle_user(u.get("nickname"), new_state)
            render_configs()
            validate_and_restart()
            word = f"{GREEN}включен{RESET}" if new_state else f"{RED}отключен{RESET}"
            print(f"\n  ✓ Пользователь {word}.")
            # reload local user state
            u["enabled"] = new_state
            pause()
        elif choice == "3":
            confirm = input(f"  Удалить {BOLD}{u.get('nickname')}{RESET}? [y/N]: ").strip().lower()
            if confirm == "y":
                delete_user(u.get("nickname"))
                render_configs()
                validate_and_restart()
                print(f"\n  {GREEN}✓ Пользователь удален.{RESET}")
                pause()
                return
            else:
                print(f"  {DIM}Отменено.{RESET}")
                pause()

def show_qr_menu(u):
    print_header(f"QR / Ссылка: {u.get('nickname')}")
    link = build_client_link(u)
    print(f"  {YELLOW}Протокол:{RESET} {protocol_label(u)}")
    print(f"  {YELLOW}Ссылка:{RESET}\n  {CYAN}{link}{RESET}\n")
    print_qr_code(link)
    pause()

# ─── Создание пользователя ───────────────────────────────────────────────────

def create_user_menu():
    print_header("Новый пользователь")
    nickname = input("  Ник пользователя: ").strip()
    if not nickname:
        print(f"  {RED}Имя не может быть пустым.{RESET}")
        pause()
        return

    print("\n  Выберите протокол:")
    print(f"  {CYAN}1){RESET} NaiveProxy")
    print(f"  {CYAN}2){RESET} VLESS over WebSocket")
    print(f"  {CYAN}3){RESET} VLESS over gRPC")
    print(f"  {CYAN}4){RESET} VLESS over XHTTP")
    print(f"\n  {DIM}0) Отмена{RESET}\n")

    choice = get_menu_choice()
    if choice == "1":
        ok, res = add_user(nickname, "naive")
    elif choice == "2":
        ok, res = add_user(nickname, "vless", "ws")
    elif choice == "3":
        ok, res = add_user(nickname, "vless", "grpc")
    elif choice == "4":
        ok, res = add_user(nickname, "vless", "xhttp")
    else:
        return

    if ok:
        link = build_client_link(res)
        print(f"\n  {GREEN}✓ Пользователь успешно добавлен!{RESET}")
        print(f"  {YELLOW}Ссылка:{RESET} {CYAN}{link}{RESET}\n")
        print_qr_code(link)

        print(f"\n  Обновляем конфигурацию...")
        render_configs()
        success, msg = validate_and_restart()
        if success:
            print(f"  {GREEN}Службы перезапущены.{RESET}")
        else:
            print(f"  {RED}Ошибка: {msg}{RESET}")
    else:
        print(f"\n  {RED}✗ Ошибка: {res}{RESET}")

    pause()

# ─── Настройки ───────────────────────────────────────────────────────────────

def get_current_singbox_version():
    try:
        res = subprocess.run(["sing-box", "version"], capture_output=True, text=True)
        for line in res.stdout.split("\n"):
            if "version" in line:
                parts = line.split("version")
                if len(parts) > 1:
                    return parts[1].strip().split()[0]
    except Exception:
        return "не установлен"
    return "неизвестно"

def get_latest_singbox_version():
    import urllib.request
    import json
    try:
        url = "https://api.github.com/repos/SagerNet/sing-box/releases/latest"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            tag_name = data.get("tag_name", "")
            return tag_name.lstrip("v")
    except Exception as e:
        return f"ошибка проверки ({e})"

def settings_menu():
    while True:
        env = load_env()
        print_header("Настройки")
        
        domain = env.get("DOMAIN", "не задан")
        email = env.get("ADMIN_EMAIL", "не задан (анонимный SSL)")
        if not email:
            email = "не задан (анонимный SSL)"
        template = env.get("FAKE_SITE_TEMPLATE", "aether")
        vless_ws = env.get("VLESS_WS_PATH", "/vless-ws")
        vless_grpc = env.get("VLESS_GRPC_SERVICE", "vless-grpc")
        vless_xhttp = env.get("VLESS_XHTTP_PATH", "/vless-xhttp")
        
        print(f"  {YELLOW}Текущая конфигурация:{RESET}")
        print(f"  • Домен:             {domain}")
        print(f"  • Email Let's Encrypt: {email}")
        print(f"  • Шаблон сайта:      {template}")
        print(f"  • Путь VLESS WS:     {vless_ws}")
        print(f"  • Сервис VLESS gRPC:  {vless_grpc}")
        print(f"  • Путь VLESS XHTTP:  {vless_xhttp}")
        print(f"{BLUE}─" * 60 + f"{RESET}\n")

        print(f"  {CYAN}1){RESET} Домен и Email")
        print(f"  {CYAN}2){RESET} Выбор шаблона сайта")
        print(f"  {CYAN}3){RESET} Настройки путей VLESS")
        print(f"  {CYAN}4){RESET} Обновление sing-box")
        print(f"  {CYAN}5){RESET} Бэкап и Восстановление")
        print(f"\n  {DIM}0) Назад{RESET}\n")
        
        choice = get_menu_choice()
        if choice == "0":
            return
        elif choice == "1":
            change_domain_email_menu()
        elif choice == "2":
            change_site_template_menu()
        elif choice == "3":
            change_vless_paths_menu()
        elif choice == "4":
            update_singbox_menu()
        elif choice == "5":
            backup_restore_menu()

def change_domain_email_menu():
    env = load_env()
    print_header("Настройки → Домен и Email")
    print(f"  Текущий домен: {env.get('DOMAIN', 'не задан')}")
    print(f"  Текущий Email: {env.get('ADMIN_EMAIL', 'не задан (анонимный SSL)') or 'не задан (анонимный SSL)'}")
    print(f"{BLUE}─" * 60 + f"{RESET}\n")
    
    new_domain = input("  Введите новый домен (или Enter для отмены): ").strip()
    new_domain = new_domain.replace(" ", "")
    changed = False
    if new_domain:
        env["DOMAIN"] = new_domain
        save_env(env)
        changed = True
        print(f"  {GREEN}✓ Домен изменен на {new_domain}{RESET}")
        
    print("\n  Для анонимного SSL (без почты) введите символ '-'")
    new_email = input("  Введите новый Email (или Enter для отмены): ").strip()
    new_email = new_email.replace(" ", "")
    if new_email == "-":
        env["ADMIN_EMAIL"] = ""
        save_env(env)
        changed = True
        print(f"  {GREEN}✓ Email удален (анонимный SSL активирован){RESET}")
    elif new_email:
        env["ADMIN_EMAIL"] = new_email
        save_env(env)
        changed = True
        print(f"  {GREEN}✓ Email изменен на {new_email}{RESET}")
        
    if changed:
        print("\n  Применяем настройки...")
        render_configs()
        success, msg = validate_and_restart()
        if success:
            print(f"  {GREEN}✓ Службы перезапущены и работают.{RESET}")
        else:
            print(f"  {RED}✗ Ошибка перезапуска: {msg}{RESET}")
    pause()

def change_site_template_menu():
    env = load_env()
    print_header("Настройки → Шаблон сайта")
    current = env.get("FAKE_SITE_TEMPLATE", "aether")
    print(f"  Текущий шаблон: {BOLD}{current}{RESET}\n")
    
    templates = {
        "1": ("aether", "Aether Resonance (Эфирный Резонанс)"),
        "2": ("nexus", "Quantum Nexus (Квантовый Нексус)"),
        "3": ("synapse", "Synaptic Dynamics (Синаптическая Динамика)"),
        "4": ("chronos", "Chronos Temporal (Хроно-Вектор)"),
        "5": ("stratum", "Stratum Synergy (Стратум Синергия)"),
    }
    
    for k, v in templates.items():
        print(f"  {CYAN}{k}){RESET} {v[1]}")
    print(f"\n  {DIM}0) Отмена{RESET}\n")
    
    choice = get_menu_choice()
    if choice in templates:
        name = templates[choice][0]
        env["FAKE_SITE_TEMPLATE"] = name
        save_env(env)
        print(f"\n  {GREEN}✓ Шаблон изменен на {name}{RESET}")
        print("  Применяем настройки...")
        render_configs()
        success, msg = validate_and_restart()
        if success:
            print(f"  {GREEN}✓ Caddy перезапущен с новым сайтом.{RESET}")
        else:
            print(f"  {RED}✗ Ошибка перезапуска: {msg}{RESET}")
    pause()

def change_vless_paths_menu():
    env = load_env()
    print_header("Настройки → Пути VLESS")
    print(f"  1) Путь VLESS WS:     {env.get('VLESS_WS_PATH', '/vless-ws')}")
    print(f"  2) Сервис VLESS gRPC:  {env.get('VLESS_GRPC_SERVICE', 'vless-grpc')}")
    print(f"  3) Путь VLESS XHTTP:  {env.get('VLESS_XHTTP_PATH', '/vless-xhttp')}")
    print(f"\n  {DIM}0) Назад{RESET}\n")
    
    choice = get_menu_choice()
    changed = False
    if choice == "1":
        val = input("  Введите путь WS (должен начинаться со слэша /): ").strip()
        if val and val.startswith("/"):
            env["VLESS_WS_PATH"] = val
            save_env(env)
            changed = True
        else:
            print(f"  {RED}Некорректный путь.{RESET}")
    elif choice == "2":
        val = input("  Введите имя gRPC сервиса: ").strip()
        if val:
            env["VLESS_GRPC_SERVICE"] = val
            save_env(env)
            changed = True
    elif choice == "3":
        val = input("  Введите путь XHTTP (должен начинаться со слэша /): ").strip()
        if val and val.startswith("/"):
            env["VLESS_XHTTP_PATH"] = val
            save_env(env)
            changed = True
        else:
            print(f"  {RED}Некорректный путь.{RESET}")
            
    if changed:
        print("\n  Применяем настройки...")
        render_configs()
        success, msg = validate_and_restart()
        if success:
            print(f"  {GREEN}✓ Службы перезапущены с новыми путями.{RESET}")
        else:
            print(f"  {RED}✗ Ошибка: {msg}{RESET}")
    pause()

def update_singbox_menu():
    print_header("Настройки → Обновление sing-box")
    print("  Получение информации о версиях...")
    current = get_current_singbox_version()
    latest = get_latest_singbox_version()
    
    print(f"\n  Текущая установленная версия: {BOLD}{current}{RESET}")
    print(f"  Последняя официальная версия: {BOLD}{latest}{RESET}\n")
    
    if current == latest:
        print(f"  {GREEN}✓ У вас уже установлена последняя официальная версия.{RESET}")
        print(f"  Хотите переустановить/принудительно обновить версию {latest}?")
    else:
        print(f"  {YELLOW}⚠ Доступно обновление до версии {latest}!{RESET}")
        
    confirm = input("  Продолжить обновление? [y/N]: ").strip().lower()
    if confirm == 'y':
        print(f"\n  [*] Запуск процесса обновления до версии {latest}...")
        try:
            arch_res = subprocess.run(["dpkg", "--print-architecture"], capture_output=True, text=True)
            arch = arch_res.stdout.strip()
            go_arch = "amd64"
            if arch == "arm64" or arch == "aarch64":
                go_arch = "arm64"
            
            deb_url = f"https://github.com/SagerNet/sing-box/releases/download/v{latest}/sing-box_{latest}_linux_{go_arch}.deb"
            deb_file = f"/tmp/sing-box_{latest}.deb"
            
            print(f"  * Скачивание {deb_url}...")
            import urllib.request
            urllib.request.urlretrieve(deb_url, deb_file)
            
            print("  * Установка deb-пакета...")
            res = subprocess.run(["dpkg", "-i", deb_file], capture_output=True, text=True)
            if res.returncode != 0:
                print(f"  {RED}✗ Ошибка установки dpkg: {res.stderr}{RESET}")
            else:
                print(f"  {GREEN}✓ sing-box успешно установлен/обновлен.{RESET}")
                
                print("  * Удаление временного файла...")
                if os.path.exists(deb_file):
                    os.remove(deb_file)
                
                print("  * Перезапуск службы sing-box...")
                subprocess.run(["systemctl", "daemon-reload"])
                subprocess.run(["systemctl", "restart", "sing-box"])
                
                log_ok = subprocess.run(["systemctl", "is-active", "sing-box"], capture_output=True, text=True).stdout.strip()
                if log_ok == "active":
                    print(f"  {GREEN}✓ Службы успешно перезапущены и проверены.{RESET}")
                else:
                    print(f"  {RED}✗ Служба sing-box не запустилась после обновления!{RESET}")
        except Exception as e:
            print(f"  {RED}✗ Ошибка при обновлении: {e}{RESET}")
    else:
        print("  Обновление отменено.")
    pause()

def backup_restore_menu():
    import tarfile
    import datetime
    
    while True:
        print_header("Настройки → Бэкап и Восстановление")
        print(f"  {CYAN}1){RESET} Создать бэкап настроек")
        print(f"  {CYAN}2){RESET} Восстановить настройки из файла")
        print(f"\n  {DIM}0) Назад{RESET}\n")
        
        choice = get_menu_choice()
        if choice == "0":
            return
        elif choice == "1":
            print_header("Создание резервной копии")
            backup_dir = "/opt/transferbox/backups"
            try:
                os.makedirs(backup_dir, exist_ok=True)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_filename = f"transferbox_backup_{timestamp}.tar.gz"
                backup_path = os.path.join(backup_dir, backup_filename)
                
                files_to_backup = []
                paths = ["/opt/transferbox/users.json", "/opt/transferbox/instance.env"]
                for p in paths:
                    if os.path.exists(p):
                        files_to_backup.append(p)
                
                if not files_to_backup:
                    print(f"\n  {RED}✗ Ошибка: Нет файлов настроек для резервного копирования!{RESET}")
                    pause()
                    continue
                
                with tarfile.open(backup_path, "w:gz") as tar:
                    for p in files_to_backup:
                        tar.add(p, arcname=os.path.basename(p))
                
                print(f"\n  {GREEN}✓ Бэкап успешно создан!{RESET}")
                print(f"  Файл сохранен: {BOLD}{backup_path}{RESET}")
                print("  Скачайте этот файл на свой компьютер для надежного хранения.")
            except Exception as e:
                print(f"\n  {RED}✗ Ошибка создания бэкапа: {e}{RESET}")
            pause()
            
        elif choice == "2":
            print_header("Восстановление из резервной копии")
            print("  Пожалуйста, укажите абсолютный путь к файлу резервной копии.")
            print("  Например: /opt/transferbox/backups/transferbox_backup_XXXXXXXX_XXXXXX.tar.gz")
            print(f"{BLUE}─" * 60 + f"{RESET}\n")
            
            backup_path = input("  Путь к файлу бэкапа (или Enter для отмены): ").strip()
            if not backup_path:
                continue
                
            if not os.path.exists(backup_path):
                print(f"\n  {RED}✗ Ошибка: Файл по указанному пути не найден!{RESET}")
                pause()
                continue
                
            confirm = input(f"  Вы уверены, что хотите переписать текущие настройки? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("  Операция отменена.")
                pause()
                continue
                
            print("\n  [*] Восстановление файлов...")
            try:
                with tarfile.open(backup_path, "r:gz") as tar:
                    tar.extractall(path="/opt/transferbox")
                
                print("  [*] Пересборка конфигураций и перезапуск служб...")
                render_configs()
                success, msg = validate_and_restart()
                if success:
                    print(f"\n  {GREEN}✓ Настройки успешно восстановлены и применены!{RESET}")
                    print("  Все службы запущены и функционируют на восстановленных данных.")
                else:
                    print(f"\n  {RED}✗ Ошибка при применении восстановленных настроек: {msg}{RESET}")
            except Exception as e:
                print(f"\n  {RED}✗ Ошибка при распаковке архива: {e}{RESET}")
            pause()

# ─── Применение настроек ─────────────────────────────────────────────────────

def apply_settings_menu():
    print_header("Перезапуск служб")
    print("  Генерация конфигураций и перезапуск...")
    try:
        render_configs()
        success, msg = validate_and_restart()
        if success:
            print(f"\n  {GREEN}✓ Службы успешно перезапущены!{RESET}")
        else:
            print(f"\n  {RED}✗ Ошибка:{RESET}\n  {msg}")
    except Exception as e:
        print(f"\n  {RED}✗ Критическая ошибка:{RESET} {e}")
    pause()

# ─── Логи ────────────────────────────────────────────────────────────────────

def logs_menu():
    while True:
        print_header("Просмотр логов")
        print(f"  {CYAN}1){RESET} Последние 50 строк — Caddy")
        print(f"  {CYAN}2){RESET} Последние 50 строк — sing-box")
        print(f"  {CYAN}3){RESET} Следить за логом Caddy (Ctrl+C — выход)")
        print(f"  {CYAN}4){RESET} Следить за логом sing-box (Ctrl+C — выход)")
        print(f"\n  {DIM}0) Назад{RESET}\n")

        choice = get_menu_choice()
        if choice == "0":
            return
        elif choice == "1":
            print(f"\n{BLUE}--- Caddy (50 строк) ---{RESET}\n")
            subprocess.run(["journalctl", "-u", "caddy", "-n", "50", "--no-pager"])
            pause()
        elif choice == "2":
            print(f"\n{BLUE}--- sing-box (50 строк) ---{RESET}\n")
            subprocess.run(["journalctl", "-u", "sing-box", "-n", "50", "--no-pager"])
            pause()
        elif choice == "3":
            try:
                subprocess.run(["journalctl", "-u", "caddy", "-f"])
            except KeyboardInterrupt:
                pass
        elif choice == "4":
            try:
                subprocess.run(["journalctl", "-u", "sing-box", "-f"])
            except KeyboardInterrupt:
                pass

# ─── Точка входа ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if os.geteuid() != 0:
        print(f"{RED}Ошибка: требуется запуск от root!{RESET}")
        sys.exit(1)
    main_menu()
