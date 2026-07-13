import subprocess
import urllib.request
import os
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from core.config_manager import load_env, save_env, get_current_ssh_port, change_ssh_port, remove_old_ssh_port_ufw
from bot.keyboards import settings_menu_keyboard, settings_back_keyboard, settings_update_keyboard, settings_backup_keyboard
from bot.backup import run_backup

router = Router()

class SettingsStates(StatesGroup):
    waiting_ssh_port = State()
    waiting_backup_time = State()

def update_cron_schedule(hour: int, minute: int, enabled: bool) -> tuple[bool, str]:
    cron_lines = [
        "*/5 * * * * root PYTHONPATH=/opt/transferbox /usr/bin/python3 /opt/transferbox/bot/check_services.py >/dev/null 2>&1",
        "0 0 * * * root PYTHONPATH=/opt/transferbox /usr/bin/python3 /opt/transferbox/bot/check_updates.py >/dev/null 2>&1"
    ]
    if enabled:
        cron_lines.append(f"{minute} {hour} * * * root PYTHONPATH=/opt/transferbox /usr/bin/python3 /opt/transferbox/bot/backup.py >/dev/null 2>&1")
        
    cron_content = "\n".join(cron_lines) + "\n"
    try:
        cron_path = "/etc/cron.d/transferbox-bot"
        with open(cron_path, "w", encoding="utf-8") as f:
            f.write(cron_content)
        os.chmod(cron_path, 0o644)
        return True, "Успешно"
    except Exception as e:
        return False, str(e)

def is_bbr_active() -> bool:
    try:
        res = subprocess.run(["sysctl", "net.ipv4.tcp_congestion_control"], capture_output=True, text=True)
        return "bbr" in res.stdout
    except Exception:
        return False

def toggle_bbr() -> tuple[bool, str]:
    active = is_bbr_active()
    if active:
        # Отключаем BBR
        res = subprocess.run(["sysctl", "-w", "net.ipv4.tcp_congestion_control=cubic"], capture_output=True)
        if res.returncode == 0:
            subprocess.run(["rm", "-f", "/etc/sysctl.d/99-transferbox-bbr.conf"], capture_output=True)
            subprocess.run(["sysctl", "--system"], capture_output=True)
            env = load_env()
            env['BBR_ENABLED'] = 'false'
            save_env(env)
            return True, "BBR оптимизация отключена (переключено на cubic)."
        else:
            return False, f"Ошибка отключения BBR: {res.stderr.decode()}"
    else:
        # Включаем BBR
        res_mod = subprocess.run(["modprobe", "tcp_bbr"], capture_output=True)
        if res_mod.returncode == 0:
            subprocess.run(["sysctl", "-w", "net.core.default_qdisc=fq"], capture_output=True)
            subprocess.run(["sysctl", "-w", "net.ipv4.tcp_congestion_control=bbr"], capture_output=True)
            with open("/etc/sysctl.d/99-transferbox-bbr.conf", "w") as f:
                f.write("net.core.default_qdisc=fq\nnet.ipv4.tcp_congestion_control=bbr\n")
            subprocess.run(["sysctl", "--system"], capture_output=True)
            env = load_env()
            env['BBR_ENABLED'] = 'true'
            save_env(env)
            return True, "BBR оптимизация успешно включена!"
        else:
            return False, "Ядро вашей системы не поддерживает BBR."

def check_panel_update() -> tuple[bool, str, str]:
    current_version = "неизвестно"
    try:
        with open("/opt/transferbox/transferbox", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("VERSION="):
                    current_version = line.split('"')[1]
                    break
    except Exception:
        pass
        
    try:
        url = "https://raw.githubusercontent.com/denash-git/TransferBox/main/transferbox"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            content = response.read().decode('utf-8')
            for line in content.split("\n"):
                if line.startswith("VERSION="):
                    latest_version = line.split('"')[1]
                    return latest_version != current_version, current_version, latest_version
    except Exception as e:
        return False, current_version, f"ошибка: {e}"
        
    return False, current_version, current_version

# ─── МЕНЮ НАСТРОЕК ───────────────────────────────────────────────────────────

@router.message(Command("settings"))
@router.callback_query(F.data == "settings:menu")
async def settings_menu_callback(event, state: FSMContext = None):
    if state:
        await state.clear()
        
    text = "⚙️ <b>Настройки системы</b>"
    bbr_active = is_bbr_active()
    
    if isinstance(event, CallbackQuery):
        try:
            await event.message.edit_text(text, reply_markup=settings_menu_keyboard(bbr_active), parse_mode="HTML")
        except Exception:
            await event.message.answer(text, reply_markup=settings_menu_keyboard(bbr_active), parse_mode="HTML")
            await event.message.delete()
        await event.answer()
    else:
        await event.answer(text, reply_markup=settings_menu_keyboard(bbr_active), parse_mode="HTML")

# ─── НАСТРОЙКИ: ИЗМЕНИТЬ ПОРТ SSH ─────────────────────────────────────────────

@router.callback_query(F.data == "settings:ssh_port")
async def settings_ssh_port_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_ssh_port)
    cur_port = get_current_ssh_port()
    
    text = (
        "🔑 <b>Изменение порта SSH</b>\n\n"
        f"Текущий порт SSH: <code>{cur_port}</code>\n\n"
        "Введите новый порт SSH (число от 1 до 65535) или нажмите кнопку отмены:"
    )
    await callback.message.edit_text(text, reply_markup=settings_back_keyboard(), parse_mode="HTML")
    await callback.answer()

@router.message(SettingsStates.waiting_ssh_port)
async def settings_ssh_port_msg(message: Message, state: FSMContext):
    port_str = message.text.strip()
    if not port_str.isdigit() or not (1 <= int(port_str) <= 65535):
        await message.answer("❌ Неверный формат порта! Порт должен быть числом от 1 до 65535. Введите еще раз:")
        return
        
    new_port = int(port_str)
    cur_port = get_current_ssh_port()
    
    if new_port == cur_port:
        await message.answer("Порт совпадает с текущим. Введите другое число или перейдите в меню:")
        return
        
    await state.clear()
    
    success, msg = change_ssh_port(new_port)
    if success:
        remove_old_ssh_port_ufw(cur_port)
        text = (
            f"✅ <b>Успешно!</b>\nПорт SSH изменен на <code>{new_port}</code>.\n\n"
            f"⚠️ <b>Внимание:</b> При следующем подключении не забудьте указать новый порт:\n"
            f"<code>ssh root@&lt;IP&gt; -p {new_port}</code>"
        )
    else:
        text = f"❌ <b>Ошибка изменения порта SSH:</b>\n\n<code>{msg}</code>"
        
    await message.answer(text, reply_markup=settings_back_keyboard(), parse_mode="HTML")

# ─── НАСТРОЙКИ: BBR ОПТИМИЗАЦИЯ ────────────────────────────────────────────────

@router.callback_query(F.data == "settings:bbr_toggle")
async def settings_bbr_toggle_callback(callback: CallbackQuery):
    success, msg = toggle_bbr()
    await callback.answer(msg, show_alert=True)
    
    # Обновляем клавиатуру настроек
    bbr_active = is_bbr_active()
    text = "⚙️ <b>Настройки системы</b>"
    await callback.message.edit_text(text, reply_markup=settings_menu_keyboard(bbr_active), parse_mode="HTML")

# ─── НАСТРОЙКИ: ПРОВЕРИТЬ ОБНОВЛЕНИЯ ──────────────────────────────────────────

@router.callback_query(F.data == "settings:check_updates")
async def settings_check_updates_callback(callback: CallbackQuery):
    await callback.message.edit_text("⏳ <b>Проверка обновлений панели...</b>", parse_mode="HTML")
    await callback.answer()
    
    has_update, current, latest = check_panel_update()
    if has_update:
        text = (
            "🔄 <b>Обновление панели</b>\n\n"
            f"Доступна новая версия: <code>{latest}</code> (ваша: <code>{current}</code>).\n\n"
            "Вы можете обновить панель прямо сейчас или через консольное меню сервера."
        )
    elif "ошибка" in latest:
        text = f"❌ <b>Не удалось проверить обновления:</b>\n\n<code>{latest}</code>"
    else:
        text = (
            "✅ <b>Обновление панели</b>\n\n"
            f"У вас установлена последняя версия панели: <code>{current}</code>."
        )
        
    await callback.message.edit_text(text, reply_markup=settings_update_keyboard(has_update), parse_mode="HTML")

# ─── НАСТРОЙКИ: ЗАПУСТИТЬ ОБНОВЛЕНИЕ ──────────────────────────────────────────

@router.callback_query(F.data == "settings:run_update")
async def settings_run_update_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        "⏳ <b>Обновление панели запущено...</b>\n\n"
        "Бот выполняет обновление файлов, миграцию базы данных и перезапуск служб. "
        "Это займет несколько секунд, после чего служба бота перезагрузится.",
        parse_mode="HTML"
    )
    await callback.answer()
    
    import subprocess
    import os
    subprocess.Popen(
        ["nohup", "python3", "/opt/transferbox/bot/run_update.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setpgrp if hasattr(os, "setpgrp") else None
    )

# ─── НАСТРОЙКИ: МЕНЮ БЭКАПОВ ──────────────────────────────────────────────────

# ─── НАСТРОЙКИ: МЕНЮ БЭКАПОВ ──────────────────────────────────────────────────

@router.callback_query(F.data == "settings:backup_menu")
async def settings_backup_menu_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    env = load_env()
    backup_enabled = env.get("BACKUP_ENABLED", "false").lower() == "true"
    password_set = bool(env.get("BACKUP_PASSWORD", "").strip())
    
    hour_str = env.get("BACKUP_HOUR")
    minute_str = env.get("BACKUP_MINUTE")
    
    if hour_str is None or minute_str is None:
        hour = 12
        minute = 0
        env["BACKUP_HOUR"] = str(hour)
        env["BACKUP_MINUTE"] = str(minute)
        save_env(env)
        update_cron_schedule(hour, minute, backup_enabled)
    else:
        hour = int(hour_str)
        minute = int(minute_str)
        
    status_text = "🟢 <b>Автобэкапы:</b> включены" if backup_enabled else "🔴 <b>Автобэкапы:</b> отключены"
    time_info = f"⏰ <b>Время автобэкапа:</b> <code>{hour:02d}:{minute:02d}</code> каждый день.\n" if backup_enabled else ""
    
    text = (
        "💾 <b>Резервное копирование</b>\n\n"
        "Архивы бэкапов, отправляемые в Telegram, защищаются паролем, который вы задаете в TUI.\n\n"
        f"{status_text}\n"
        f"{time_info}"
    )
    if password_set:
        text += "\n🔐 <b>Пароль бэкапов:</b> задан"
    else:
        text += "\n⚠️ <b>Внимание:</b> Пароль для бэкапов не задан. Бэкапы отправляться не будут. Задайте его в TUI по SSH."
        
    await callback.message.edit_text(text, reply_markup=settings_backup_keyboard(backup_enabled), parse_mode="HTML")
    await callback.answer()

# ─── НАСТРОЙКИ: ПРЕКЛЮЧЕНИЕ АВТОБЭКАПОВ ──────────────────────────────────────

@router.callback_query(F.data == "settings:backup_toggle")
async def settings_backup_toggle_callback(callback: CallbackQuery):
    env = load_env()
    current_enabled = env.get("BACKUP_ENABLED", "false").lower() == "true"
    password_set = bool(env.get("BACKUP_PASSWORD", "").strip())
    new_enabled = not current_enabled
    
    env["BACKUP_ENABLED"] = "true" if new_enabled else "false"
    save_env(env)
    
    hour = int(env.get("BACKUP_HOUR", "12"))
    minute = int(env.get("BACKUP_MINUTE", "0"))
    
    success, err_msg = update_cron_schedule(hour, minute, new_enabled)
    
    if new_enabled:
        msg = "Автобэкапы успешно включены (в 12:00 по умолчанию)."
    else:
        msg = "Автобэкапы успешно отключены."
        
    await callback.answer(msg, show_alert=True)
    
    # Обновляем меню бэкапов
    status_text = "🟢 <b>Автобэкапы:</b> включены" if new_enabled else "🔴 <b>Автобэкапы:</b> отключены"
    time_info = f"⏰ <b>Время автобэкапа:</b> <code>{hour:02d}:{minute:02d}</code> каждый день.\n" if new_enabled else ""
    
    text = (
        "💾 <b>Резервное копирование</b>\n\n"
        "Архивы бэкапов, отправляемые в Telegram, защищаются паролем, который вы задаете в TUI.\n\n"
        f"{status_text}\n"
        f"{time_info}"
    )
    if password_set:
        text += "\n🔐 <b>Пароль бэкапов:</b> задан"
    else:
        text += "\n⚠️ <b>Внимание:</b> Пароль для бэкапов не задан. Бэкапы отправляться не будут. Задайте его в TUI по SSH."
        
    await callback.message.edit_text(text, reply_markup=settings_backup_keyboard(new_enabled), parse_mode="HTML")

# ─── НАСТРОЙКИ: БЭКАП СЕЙЧАС ──────────────────────────────────────────────────

@router.callback_query(F.data == "settings:backup_now")
async def settings_backup_now_callback(callback: CallbackQuery):
    env = load_env()
    backup_enabled = env.get("BACKUP_ENABLED", "false").lower() == "true"
    password_set = bool(env.get("BACKUP_PASSWORD", "").strip())
    
    if not password_set:
        await callback.answer("❌ Пароль для бэкапов не задан! Задайте его в TUI по SSH.", show_alert=True)
        return
        
    await callback.message.edit_text("⏳ <b>Создание и отправка резервной копии...</b>", parse_mode="HTML")
    await callback.answer()
    
    success, msg = run_backup()
    
    if success:
        text = (
            "✅ <b>Резервная копия успешно отправлена в этот чат!</b>\n\n"
            "Архив зашифрован вашим паролем бэкапов."
        )
    else:
        text = f"❌ <b>Ошибка резервного копирования:</b>\n\n<code>{msg}</code>"
        
    await callback.message.edit_text(text, reply_markup=settings_backup_keyboard(backup_enabled), parse_mode="HTML")

# ─── НАСТРОЙКИ: ИЗМЕНИТЬ ВРЕМЯ БЭКАПА ──────────────────────────────────────────

@router.callback_query(F.data == "settings:backup_change_time")
async def settings_backup_change_time_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_backup_time)
    env = load_env()
    hour = int(env.get("BACKUP_HOUR", "12"))
    minute = int(env.get("BACKUP_MINUTE", "0"))
    
    text = (
        "⏰ <b>Изменение времени автобэкапа</b>\n\n"
        f"Текущее время: <code>{hour:02d}:{minute:02d}</code>\n\n"
        "Введите новое время автоматического бэкапа в формате <code>ЧЧ:ММ</code> (например, <code>14:30</code> или <code>09:00</code>):"
    )
    await callback.message.edit_text(text, reply_markup=settings_back_keyboard(), parse_mode="HTML")
    await callback.answer()

@router.message(SettingsStates.waiting_backup_time)
async def settings_backup_time_msg(message: Message, state: FSMContext):
    time_str = message.text.strip()
    
    parts = time_str.split(":")
    if len(parts) != 2:
        await message.answer("❌ Неверный формат! Введите время в формате ЧЧ:ММ (например, 12:00 или 08:30):")
        return
        
    h_str, m_str = parts[0].strip(), parts[1].strip()
    if not h_str.isdigit() or not m_str.isdigit():
        await message.answer("❌ Неверный формат! Часы и минуты должны быть числами. Введите еще раз в формате ЧЧ:ММ:")
        return
        
    hour, minute = int(h_str), int(m_str)
    if not (0 <= hour <= 23) or not (0 <= minute <= 59):
        await message.answer("❌ Недопустимые значения времени! Часы должны быть от 0 до 23, минуты от 0 до 59. Введите еще раз:")
        return
        
    await state.clear()
    env = load_env()
    env["BACKUP_HOUR"] = str(hour)
    env["BACKUP_MINUTE"] = str(minute)
    save_env(env)
    
    backup_enabled = env.get("BACKUP_ENABLED", "false").lower() == "true"
    success, err_msg = update_cron_schedule(hour, minute, backup_enabled)
    
    if success:
        text = (
            "✅ <b>Время автобэкапа успешно изменено!</b>\n\n"
            f"Новое время: <code>{hour:02d}:{minute:02d}</code> каждый день."
        )
    else:
        text = f"❌ <b>Ошибка при изменении расписания cron:</b>\n\n<code>{err_msg}</code>"
        
    await message.answer(text, reply_markup=settings_backup_keyboard(backup_enabled), parse_mode="HTML")

