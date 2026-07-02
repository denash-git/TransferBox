#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
from core.config_manager import load_env, save_env, load_users, render_configs, validate_and_restart
from core.user_manager import add_user, delete_user, toggle_user, build_client_link, print_qr_code

# ANSI Colors
BLUE = '\033[1;34m'
GREEN = '\033[1;32m'
RED = '\033[1;31m'
YELLOW = '\033[1;33m'
CYAN = '\033[1;36m'
DIM = '\033[2m'
BOLD = '\033[1m'
RESET = '\033[0m'

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
    print(f"  {YELLOW}Caddy (фронтенд 443):{RESET} {get_service_status('caddy')}")
    print(f"  {YELLOW}sing-box (ядро прокси):{RESET} {get_service_status('sing-box')}")
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

def main_menu():
    while True:
        print_header("TransferBox — Панель Управления")
        print(f"  {CYAN}1){RESET} Список пользователей и ссылки подключения")
        print(f"  {CYAN}2){RESET} Добавить нового пользователя")
        print(f"  {CYAN}3){RESET} Включить / Выключить пользователя")
        print(f"  {CYAN}4){RESET} Удалить пользователя")
        print(f"  {CYAN}5){RESET} Настройки домена и маскировки")
        print(f"  {CYAN}6){RESET} Перезапустить службы и перечитать конфиги")
        print(f"  {CYAN}7){RESET} Показать логи (Caddy и sing-box)")
        print(f"\n  {DIM}00) Выход{RESET}\n")
        
        choice = get_menu_choice()
        if choice == "1":
            list_users_menu()
        elif choice == "2":
            create_user_menu()
        elif choice == "3":
            toggle_user_menu()
        elif choice == "4":
            delete_user_menu()
        elif choice == "5":
            settings_menu()
        elif choice == "6":
            apply_settings_menu()
        elif choice == "7":
            logs_menu()

def list_users_menu():
    print_header("Список пользователей")
    users = load_users()
    if not users:
        print("  Пользователей пока нет.")
        pause()
        return

    for idx, u in enumerate(users, 1):
        status = f"{GREEN}активен{RESET}" if u.get("enabled", True) else f"{RED}отключен{RESET}"
        protocol = u.get("protocol").upper()
        
        if protocol == "VLESS":
            details = f"type: {u.get('credentials', {}).get('type', 'ws')}"
        else:
            details = f"login: {u.get('credentials', {}).get('username')}"
            
        print(f"  {idx}) {BOLD}{u.get('nickname')}{RESET} [{protocol}] ({details}) — {status}")

    print("\n  Введите номер пользователя для показа ссылки подключения и QR-кода.")
    print(f"  {DIM}0) Назад{RESET}")
    
    choice = get_menu_choice()
    if choice == "0" or not choice:
        return
        
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(users):
            u = users[idx]
            link = build_client_link(u)
            print_header(f"Подключение: {u.get('nickname')}")
            print(f"  {YELLOW}Протокол:{RESET} {u.get('protocol').upper()}")
            print(f"  {YELLOW}Ссылка подключения:{RESET}\n  {CYAN}{link}{RESET}\n")
            print_qr_code(link)
            pause()
        else:
            print("  Неверный номер.")
            pause()
    except ValueError:
        print("  Пожалуйста, введите число.")
        pause()

def create_user_menu():
    print_header("Добавление пользователя")
    nickname = input("  Введите ник (имя) пользователя: ").strip()
    if not nickname:
        print("  Имя не может быть пустым.")
        pause()
        return

    print("\n  Выберите протокол:")
    print(f"  {CYAN}1){RESET} NaiveProxy")
    print(f"  {CYAN}2){RESET} VLESS over WebSocket")
    print(f"  {CYAN}3){RESET} VLESS over gRPC")
    print(f"  {CYAN}4){RESET} VLESS over XHTTP")
    print(f"\n  {DIM}0) Отмена{RESET}")
    
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
        print(f"\n  {GREEN}✓ Пользователь успешно добавлен!{RESET}")
        link = build_client_link(res)
        print(f"  {YELLOW}Ссылка:{RESET} {CYAN}{link}{RESET}")
        
        # Auto-apply configs
        print("\n  Обновляем конфигурацию служб...")
        render_configs()
        success, msg = validate_and_restart()
        if success:
            print(f"  {GREEN}Службы успешно перезапущены.{RESET}")
        else:
            print(f"  {RED}Ошибка перезапуска: {msg}{RESET}")
    else:
        print(f"\n  {RED}✗ Ошибка: {res}{RESET}")
        
    pause()

def toggle_user_menu():
    print_header("Включение/выключение пользователей")
    users = load_users()
    if not users:
        print("  Пользователей нет.")
        pause()
        return

    for idx, u in enumerate(users, 1):
        status = f"{GREEN}активен{RESET}" if u.get("enabled", True) else f"{RED}отключен{RESET}"
        print(f"  {idx}) {u.get('nickname')} — {status}")

    print(f"\n  Выберите номер пользователя для изменения статуса.")
    print(f"  {DIM}0) Назад{RESET}")
    
    choice = get_menu_choice()
    if choice == "0" or not choice:
        return
        
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(users):
            u = users[idx]
            new_state = not u.get("enabled", True)
            toggle_user(u.get("nickname"), new_state)
            
            print("\n  Перегенерируем конфигурацию...")
            render_configs()
            validate_and_restart()
            print(f"  {GREEN}✓ Статус изменен!{RESET}")
        else:
            print("  Неверный номер.")
    except ValueError:
        print("  Неверный формат ввода.")
    pause()

def delete_user_menu():
    print_header("Удаление пользователя")
    users = load_users()
    if not users:
        print("  Пользователей нет.")
        pause()
        return

    for idx, u in enumerate(users, 1):
        print(f"  {idx}) {u.get('nickname')} [{u.get('protocol').upper()}]")

    print(f"\n  Выберите номер пользователя для УДАЛЕНИЯ.")
    print(f"  {DIM}0) Назад{RESET}")
    
    choice = get_menu_choice()
    if choice == "0" or not choice:
        return
        
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(users):
            u = users[idx]
            confirm = input(f"  Вы уверены, что хотите удалить {u.get('nickname')}? [y/N]: ").strip().lower()
            if confirm == 'y':
                delete_user(u.get("nickname"))
                print("\n  Обновляем файлы настроек...")
                render_configs()
                validate_and_restart()
                print(f"  {GREEN}✓ Пользователь удален.{RESET}")
        else:
            print("  Неверный номер.")
    except ValueError:
        print("  Неверный формат.")
    pause()

def settings_menu():
    while True:
        env = load_env()
        print_header("Настройки сервера")
        print(f"  {YELLOW}1) Домен:{RESET} {env.get('DOMAIN', 'не задан')}")
        print(f"  {YELLOW}2) Email Let's Encrypt:{RESET} {env.get('ADMIN_EMAIL', 'не задан')}")
        print(f"  {YELLOW}3) Шаблон фейкового сайта:{RESET} {env.get('FAKE_SITE_TEMPLATE', 'techvision')}")
        print(f"  {YELLOW}4) Путь VLESS WebSocket:{RESET} {env.get('VLESS_WS_PATH', '/vless-ws')}")
        print(f"  {YELLOW}5) Сервис VLESS gRPC:{RESET} {env.get('VLESS_GRPC_SERVICE', 'vless-grpc')}")
        print(f"  {YELLOW}6) Путь VLESS XHTTP:{RESET} {env.get('VLESS_XHTTP_PATH', '/vless-xhttp')}")
        print(f"\n  {DIM}0) Назад{RESET}")
        
        choice = get_menu_choice()
        if choice == "0":
            return
        elif choice == "1":
            val = input("  Введите новый домен: ").strip()
            if val:
                env["DOMAIN"] = val
                save_env(env)
        elif choice == "2":
            val = input("  Введите email: ").strip()
            if val:
                env["ADMIN_EMAIL"] = val
                save_env(env)
        elif choice == "3":
            print("\n  Доступные шаблоны:")
            print("   - techvision (Технологичный сайт)")
            print("   - meridian (Бизнес / консалтинг)")
            print("   - northcraft (Креативное агентство)")
            val = input("  Введите имя шаблона: ").strip()
            if val in ["techvision", "meridian", "northcraft"]:
                env["FAKE_SITE_TEMPLATE"] = val
                save_env(env)
            else:
                print("  Неизвестный шаблон.")
                pause()
        elif choice == "4":
            val = input("  Введите путь (например, /my-secret-ws): ").strip()
            if val and val.startswith("/"):
                env["VLESS_WS_PATH"] = val
                save_env(env)
            else:
                print("  Путь должен начинаться со слэша /")
                pause()
        elif choice == "5":
            val = input("  Введите имя gRPC сервиса: ").strip()
            if val:
                env["VLESS_GRPC_SERVICE"] = val
                save_env(env)
        elif choice == "6":
            val = input("  Введите путь XHTTP (например, /my-xhttp): ").strip()
            if val and val.startswith("/"):
                env["VLESS_XHTTP_PATH"] = val
                save_env(env)
            else:
                print("  Путь должен начинаться со слэша /")
                pause()

def apply_settings_menu():
    print_header("Применение настроек")
    print("  Генерация новых файлов конфигурации...")
    try:
        render_configs()
        success, msg = validate_and_restart()
        if success:
            print(f"\n  {GREEN}✓ Все службы успешно переконфигурированы и перезапущены!{RESET}")
        else:
            print(f"\n  {RED}✗ Ошибка применения:{RESET}\n  {msg}")
    except Exception as e:
        print(f"\n  {RED}✗ Критическая ошибка:{RESET} {e}")
    pause()

def logs_menu():
    while True:
        print_header("Просмотр логов")
        print(f"  {CYAN}1){RESET} Последние 50 строк лога Caddy")
        print(f"  {CYAN}2){RESET} Последние 50 строк лога sing-box")
        print(f"  {CYAN}3){RESET} Следить за логом Caddy в реальном времени (Выход: Ctrl+C)")
        print(f"  {CYAN}4){RESET} Следить за логом sing-box в реальном времени (Выход: Ctrl+C)")
        print(f"\n  {DIM}0) Назад{RESET}")
        
        choice = get_menu_choice()
        if choice == "0":
            return
        elif choice == "1":
            print(f"\n{BLUE}--- Лог Caddy (50 строк) ---{RESET}\n")
            subprocess.run(["journalctl", "-u", "caddy", "-n", "50", "--no-pager"])
            pause()
        elif choice == "2":
            print(f"\n{BLUE}--- Лог sing-box (50 строк) ---{RESET}\n")
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

if __name__ == "__main__":
    if os.geteuid() != 0:
        print(f"{RED}Ошибка: этот скрипт должен быть запущен от имени root!{RESET}")
        sys.exit(1)
    main_menu()
