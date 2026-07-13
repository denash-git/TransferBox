import subprocess
import urllib.request
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from core.config_manager import load_env, save_env, get_current_ssh_port, change_ssh_port, remove_old_ssh_port_ufw
from bot.keyboards import settings_menu_keyboard, settings_back_keyboard, settings_update_keyboard, settings_backup_keyboard
from bot.backup import run_backup, generate_random_password

router = Router()

class SettingsStates(StatesGroup):
    waiting_ssh_port = State()
    waiting_backup_password = State()

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
        res = subprocess.run("sysctl -w net.ipv4.tcp_congestion_control=cubic", shell=True, capture_output=True)
        if res.returncode == 0:
            subprocess.run("rm -f /etc/sysctl.d/99-transferbox-bbr.conf && sysctl --system", shell=True, capture_output=True)
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
            subprocess.run("sysctl -w net.core.default_qdisc=fq && sysctl -w net.ipv4.tcp_congestion_control=bbr", shell=True, capture_output=True)
            with open("/etc/sysctl.d/99-transferbox-bbr.conf", "w") as f:
                f.write("net.core.default_qdisc=fq\nnet.ipv4.tcp_congestion_control=bbr\n")
            subprocess.run("sysctl --system", shell=True, capture_output=True)
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

@router.callback_query(F.data == "settings:backup_menu")
async def settings_backup_menu_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    env = load_env()
    password = env.get("BACKUP_PASSWORD")
    if not password:
        password = generate_random_password()
        env["BACKUP_PASSWORD"] = password
        save_env(env)
        
    text = (
        "💾 <b>Резервное копирование</b>\n\n"
        "Архивы бэкапов защищены надежным шифрованием AES-256 (ZIP).\n\n"
        f"🔑 <b>Пароль шифрования бэкапов:</b>\n<code>{password}</code>\n\n"
        "⚠️ <b>Внимание:</b> Сохраните этот пароль! Без него распаковать файлы бэкапа не получится."
    )
    await callback.message.edit_text(text, reply_markup=settings_backup_keyboard(), parse_mode="HTML")
    await callback.answer()

# ─── НАСТРОЙКИ: БЭКАП СЕЙЧАС ──────────────────────────────────────────────────

@router.callback_query(F.data == "settings:backup_now")
async def settings_backup_now_callback(callback: CallbackQuery):
    await callback.message.edit_text("⏳ <b>Создание и отправка резервной копии...</b>", parse_mode="HTML")
    await callback.answer()
    
    success, msg = run_backup()
    env = load_env()
    password = env.get("BACKUP_PASSWORD", "")
    
    if success:
        text = (
            "✅ <b>Резервная копия успешно отправлена в этот чат!</b>\n\n"
            f"🔑 Пароль для распаковки: <code>{password}</code>"
        )
    else:
        text = f"❌ <b>Ошибка резервного копирования:</b>\n\n<code>{msg}</code>"
        
    await callback.message.edit_text(text, reply_markup=settings_backup_keyboard(), parse_mode="HTML")

# ─── НАСТРОЙКИ: ИЗМЕНИТЬ ПАРОЛЬ БЭКАПА ─────────────────────────────────────────

@router.callback_query(F.data == "settings:backup_change_pass")
async def settings_backup_change_pass_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_backup_password)
    text = (
        "🔑 <b>Смена пароля бэкапов</b>\n\n"
        "Введите новый пароль для шифрования бэкапов (от 6 до 32 символов, только английские буквы и цифры):"
    )
    await callback.message.edit_text(text, reply_markup=settings_back_keyboard(), parse_mode="HTML")
    await callback.answer()

@router.message(SettingsStates.waiting_backup_password)
async def settings_backup_password_msg(message: Message, state: FSMContext):
    new_pass = message.text.strip()
    # Проверка пароля на валидность
    if not (6 <= len(new_pass) <= 32) or not new_pass.isalnum():
        await message.answer("❌ Неверный пароль! Пароль должен содержать от 6 до 32 символов (только латинские буквы и цифры). Введите еще раз:")
        return
        
    await state.clear()
    env = load_env()
    env["BACKUP_PASSWORD"] = new_pass
    save_env(env)
    
    text = (
        f"✅ <b>Пароль бэкапов изменен!</b>\n\n"
        f"Новый пароль: <code>{new_pass}</code>\n\n"
        f"Все последующие бэкапы будут зашифрованы этим паролем."
    )
    await message.answer(text, reply_markup=settings_backup_keyboard(), parse_mode="HTML")
