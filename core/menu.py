#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
from core.config_manager import load_env, save_env, load_users, render_configs, validate_and_restart
from core.user_manager import add_user, delete_user, toggle_user, build_client_link, print_qr_code

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
        print(f"  {CYAN}2){RESET} Настройки домена и маскировки")
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

def settings_menu():
    while True:
        env = load_env()
        print_header("Настройки сервера")
        print(f"  {YELLOW}1) Домен:{RESET}           {env.get('DOMAIN', 'не задан')}")
        print(f"  {YELLOW}2) Email Let's Encrypt:{RESET} {env.get('ADMIN_EMAIL', 'не задан')}")
        print(f"  {YELLOW}3) Фейк-сайт:{RESET}       {env.get('FAKE_SITE_TEMPLATE', 'techvision')}")
        print(f"  {YELLOW}4) Путь VLESS WS:{RESET}   {env.get('VLESS_WS_PATH', '/vless-ws')}")
        print(f"  {YELLOW}5) Сервис gRPC:{RESET}     {env.get('VLESS_GRPC_SERVICE', 'vless-grpc')}")
        print(f"  {YELLOW}6) Путь VLESS XHTTP:{RESET} {env.get('VLESS_XHTTP_PATH', '/vless-xhttp')}")
        print(f"\n  {DIM}0) Назад{RESET}\n")

        choice = get_menu_choice()
        if choice == "0":
            return
        elif choice == "1":
            val = input("  Новый домен: ").strip()
            if val:
                env["DOMAIN"] = val
                save_env(env)
        elif choice == "2":
            val = input("  Email: ").strip()
            if val:
                env["ADMIN_EMAIL"] = val
                save_env(env)
        elif choice == "3":
            print("\n  Доступные шаблоны: techvision / meridian / northcraft")
            val = input("  Шаблон: ").strip()
            if val in ["techvision", "meridian", "northcraft"]:
                env["FAKE_SITE_TEMPLATE"] = val
                save_env(env)
            else:
                print(f"  {RED}Неизвестный шаблон.{RESET}")
                pause()
        elif choice == "4":
            val = input("  Путь WS (например /vless-ws): ").strip()
            if val and val.startswith("/"):
                env["VLESS_WS_PATH"] = val
                save_env(env)
            else:
                print(f"  {RED}Путь должен начинаться с /{RESET}")
                pause()
        elif choice == "5":
            val = input("  Имя gRPC сервиса: ").strip()
            if val:
                env["VLESS_GRPC_SERVICE"] = val
                save_env(env)
        elif choice == "6":
            val = input("  Путь XHTTP (например /vless-xhttp): ").strip()
            if val and val.startswith("/"):
                env["VLESS_XHTTP_PATH"] = val
                save_env(env)
            else:
                print(f"  {RED}Путь должен начинаться с /{RESET}")
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
