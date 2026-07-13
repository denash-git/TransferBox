import re
import os
import tempfile
import subprocess
import json
import urllib.request
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from core.config_manager import load_users, load_env, render_configs, validate_and_restart, build_client_link, build_mieru_singbox_json
from core.user_manager import add_user, delete_user, toggle_user
from bot.keyboards import (
    users_list_keyboard, user_info_keyboard, user_delete_confirm_keyboard,
    back_to_main_keyboard, proto_manage_keyboard, proto_delete_confirm_keyboard
)
from bot.alerts import send_photo

router = Router()

class AddUserStates(StatesGroup):
    waiting_nickname = State()
    waiting_protocol = State()
    waiting_type = State()

# ─── ВСПЛЫВАЮЩИЕ УВЕДОМЛЕНИЯ ОБ УСПЕХЕ ────────────────────────────────────────

async def notify_and_restart(callback: CallbackQuery, action_name: str, action_func, *args):
    await callback.message.edit_text(f"⏳ Применение изменений: {action_name}...", parse_mode="HTML")
    
    success, msg = action_func(*args)
    if success:
        render_configs()
        success_restart, msg_restart = validate_and_restart()
        if success_restart:
            await callback.answer("✓ Успешно выполнено!", show_alert=True)
        else:
            await callback.answer(f"⚠ Изменения внесены, но ошибка перезапуска: {msg_restart}", show_alert=True)
    else:
        await callback.answer(f"❌ Ошибка: {msg}", show_alert=True)

# ─── СПИСОК ПОЛЬЗОВАТЕЛЕЙ ────────────────────────────────────────────────────

@router.message(Command("users"))
@router.callback_query(F.data == "user:list")
async def list_users_callback(event, state: FSMContext):
    await state.clear()
    users = load_users()
    text = "👥 <b>Управление пользователями</b>"
    if isinstance(event, CallbackQuery):
        try:
            await event.message.edit_text(text, reply_markup=users_list_keyboard(users), parse_mode="HTML")
        except Exception:
            await event.message.answer(text, reply_markup=users_list_keyboard(users), parse_mode="HTML")
            await event.message.delete()
        await event.answer()
    else:
        await event.answer(text, reply_markup=users_list_keyboard(users), parse_mode="HTML")

# ─── ДЕТАЛИЗАЦИЯ ПОЛЬЗОВАТЕЛЯ (ПРОТОКОЛЫ) ────────────────────────────────────

@router.callback_query(F.data.startswith("user:info:"))
async def user_info_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    nick = callback.data.split(":")[2]
    users = load_users()
    user_protocols = [u for u in users if u.get("nickname") == nick]
    
    if not user_protocols:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return
        
    is_active = any(u.get("enabled", True) for u in user_protocols)
    
    text = f"👤 <b>Пользователь:</b> <code>{nick}</code>\n"
    text += f"          {'🟢 Активен' if is_active else '🔴 Отключен'}\n\n"
    text += "<b>Добавленные протоколы:</b>"
    
    await callback.message.edit_text(text, reply_markup=user_info_keyboard(nick, user_protocols), parse_mode="HTML")
    await callback.answer()

# ─── УПРАВЛЕНИЕ КОНКРЕТНЫМ ПРОТОКОЛОМ ────────────────────────────────────────

@router.callback_query(F.data.startswith("user:proto:manage:"))
async def user_proto_manage_callback(callback: CallbackQuery):
    _, _, _, nick, proto, utype = callback.data.split(":")
    utype_val = "" if utype == "none" else utype
    
    users = load_users()
    user_obj = next((u for u in users if u.get("nickname") == nick and u.get("protocol") == proto and u.get("credentials", {}).get("type", "") == utype_val), None)
    
    if not user_obj:
        await callback.answer("Протокол не найден.", show_alert=True)
        return
        
    enabled = user_obj.get("enabled", True)
    proto_lbl = f"{proto.upper()} {utype_val.upper()}".strip()
    
    text = (
        f"⚙️ <b>Управление протоколом</b>\n\n"
        f"Пользователь: <code>{nick}</code>\n"
        f"Конфигурация: <code>{proto_lbl}</code>\n"
        f"Статус: {'🟢 Включен' if enabled else '🔴 Выключен'}"
    )
    
    await callback.message.edit_text(text, reply_markup=proto_manage_keyboard(nick, proto, utype, enabled), parse_mode="HTML")
    await callback.answer()

# ─── ВКЛЮЧЕНИЕ / ВЫКЛЮЧЕНИЕ ПРОТОКОЛА ────────────────────────────────────────

@router.callback_query(F.data.startswith("user:proto:toggle:"))
async def user_proto_toggle_callback(callback: CallbackQuery):
    _, _, _, nick, proto, utype, val = callback.data.split(":")
    utype_val = "" if utype == "none" else utype
    enabled = val == "1"
    
    await notify_and_restart(callback, f"{'Включение' if enabled else 'Отключение'} протокола", toggle_user, nick, enabled, proto, utype_val)
    
    # Возвращаемся на экран протокола
    users = load_users()
    user_obj = next((u for u in users if u.get("nickname") == nick and u.get("protocol") == proto and u.get("credentials", {}).get("type", "") == utype_val), None)
    if user_obj:
        enabled = user_obj.get("enabled", True)
        proto_lbl = f"{proto.upper()} {utype_val.upper()}".strip()
        text = (
            f"⚙️ <b>Управление протоколом</b>\n\n"
            f"Пользователь: <code>{nick}</code>\n"
            f"Конфигурация: <code>{proto_lbl}</code>\n"
            f"Статус: {'🟢 Включен' if enabled else '🔴 Выключен'}"
        )
        await callback.message.edit_text(text, reply_markup=proto_manage_keyboard(nick, proto, utype, enabled), parse_mode="HTML")

# ─── УДАЛЕНИЕ ПРОТОКОЛА ──────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("user:proto:delete:confirm:"))
async def user_proto_delete_confirm_callback(callback: CallbackQuery):
    _, _, _, _, nick, proto, utype = callback.data.split(":")
    utype_val = "" if utype == "none" else utype
    proto_lbl = f"{proto.upper()} {utype_val.upper()}".strip()
    
    text = f"⚠️ Вы уверены, что хотите удалить протокол <code>{proto_lbl}</code> для пользователя <code>{nick}</code>?"
    await callback.message.edit_text(text, reply_markup=proto_delete_confirm_keyboard(nick, proto, utype), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("user:proto:delete:run:"))
async def user_proto_delete_run_callback(callback: CallbackQuery):
    _, _, _, _, _, nick, proto, utype = callback.data.split(":")
    utype_val = "" if utype == "none" else utype
    
    await notify_and_restart(callback, "Удаление протокола", delete_user, nick, proto, utype_val)
    
    # Возвращаемся в меню пользователя
    users = load_users()
    user_protocols = [u for u in users if u.get("nickname") == nick]
    if user_protocols:
        is_active = any(u.get("enabled", True) for u in user_protocols)
        text = f"👤 <b>Пользователь:</b> <code>{nick}</code>\n"
        text += f"Общий статус: {'🟢 Активен' if is_active else '🔴 Отключен'}\n\n"
        text += "<b>Доступные протоколы (кликните для управления):</b>"
        await callback.message.edit_text(text, reply_markup=user_info_keyboard(nick, user_protocols), parse_mode="HTML")
    else:
        # Если протоколов больше нет, возвращаемся к списку пользователей
        text = "👥 <b>Список пользователей:</b>\nВыберите пользователя для управления или добавьте нового."
        await callback.message.edit_text(text, reply_markup=users_list_keyboard(users), parse_mode="HTML")

# ─── ССЫЛКИ И QR-КОДЫ ПО ПРОТОКОЛУ ───────────────────────────────────────────

@router.callback_query(F.data.startswith("user:proto:links:"))
async def user_proto_links_callback(callback: CallbackQuery):
    _, _, _, nick, proto, utype = callback.data.split(":")
    utype_val = "" if utype == "none" else utype
    
    await callback.answer("⏳ Генерация QR-кодов...", show_alert=False)
    
    env = load_env()
    token = env.get("TG_BOT_TOKEN")
    chat_id = callback.from_user.id
    
    users = load_users()
    user_obj = next((u for u in users if u.get("nickname") == nick and u.get("protocol") == proto and u.get("credentials", {}).get("type", "") == utype_val), None)
    
    if not user_obj:
        await callback.message.answer("❌ Ошибка: Протокол не найден.")
        return
        
    link = build_client_link(user_obj, env=env)
    proto_lbl = f"{proto.upper()} {utype_val.upper()}".strip()
    
    # Отправляем ссылку текстом
    msg_text = f"🔑 <b>Подключение {nick} ({proto_lbl}):</b>\n\n<code>{link}</code>"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": msg_text,
        "parse_mode": "HTML"
    }
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            pass
    except Exception as e:
        print(f"[TG BOT] Error sending link: {e}")
        
    # Генерируем и отправляем QR
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        subprocess.run(["qrencode", "-o", tmp_path, link], check=True)
        send_photo(token, chat_id, tmp_path, caption=f"QR-код подключения для {nick} ({proto_lbl})")
    except Exception as e:
        print(f"[TG BOT] Error generating QR: {e}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
            
    # Если это Mieru, дополнительно прикрепляем конфиг Sing-box JSON и его QR
    if proto == "mieru":
        singbox_json = build_mieru_singbox_json(user_obj)
        msg_json = f"📄 <b>Sing-box JSON для {nick} (копировать в Karing):</b>\n\n<code>{singbox_json}</code>"
        
        payload["text"] = msg_json
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                pass
        except Exception as e:
            print(f"[TG BOT] Error sending Mieru JSON: {e}")
            
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path_json = tmp.name
        try:
            subprocess.run(["qrencode", "-o", tmp_path_json, singbox_json], check=True)
            send_photo(token, chat_id, tmp_path_json, caption=f"QR-код для Sing-box JSON ({nick})")
        except Exception as e:
            print(f"[TG BOT] Error generating Mieru JSON QR: {e}")
        finally:
            if os.path.exists(tmp_path_json):
                os.unlink(tmp_path_json)

# ─── ДОБАВЛЕНИЕ ПРОТОКОЛА ПОЛЬЗОВАТЕЛЮ ───────────────────────────────────────

@router.callback_query(F.data.startswith("user:proto:add:"))
async def user_proto_add_callback(callback: CallbackQuery, state: FSMContext):
    nick = callback.data.split(":")[3]
    await state.set_state(AddUserStates.waiting_protocol)
    await state.update_data(nickname=nick)
    
    users = load_users()
    user_protocols = [u for u in users if u.get("nickname") == nick]
    existing_protos = set(u.get("protocol") for u in user_protocols)
    existing_vless_types = set(u.get("credentials", {}).get("type", "") for u in user_protocols if u.get("protocol") == "vless")
    
    buttons = []
    if len(existing_vless_types) < 3:
        buttons.append([InlineKeyboardButton(text="VLESS", callback_data="user:new:proto:vless")])
    if "naive" not in existing_protos:
        buttons.append([InlineKeyboardButton(text="NaiveProxy", callback_data="user:new:proto:naive")])
    if "mieru" not in existing_protos:
        buttons.append([InlineKeyboardButton(text="Mieru", callback_data="user:new:proto:mieru")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data=f"user:info:{nick}")])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(f"👤 Пользователь: <code>{nick}</code>\n\nВыберите новый протокол:", reply_markup=kb, parse_mode="HTML")
    await callback.answer()

# ─── ССЫЛКИ ПОДПИСКИ ПОЛЬЗОВАТЕЛЯ ────────────────────────────────────────────

@router.callback_query(F.data.startswith("user:links:"))
async def user_send_links_callback(callback: CallbackQuery):
    nick = callback.data.split(":")[2]
    await callback.answer("⏳ Отправка ссылки подписки...", show_alert=False)
    
    env = load_env()
    token = env.get("TG_BOT_TOKEN")
    chat_id = callback.from_user.id
    domain = env.get("DOMAIN", "yourdomain.com")
    
    # Load users to find the correct sub_token
    users = load_users()
    sub_token = ""
    for u in users:
        if u.get("nickname") == nick:
            sub_token = u.get("sub_token", "")
            break
            
    if not sub_token:
        sub_token = nick
        
    sub_link = f"https://{domain}/sub/{sub_token}"
    
    msg_text = f"🌀 <b>Ссылка подписки для {nick}:</b>\n\n<code>{sub_link}</code>"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": msg_text,
        "parse_mode": "HTML"
    }
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            pass
    except Exception as e:
        print(f"[TG BOT] Error sending sub link: {e}")
        
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        subprocess.run(["qrencode", "-o", tmp_path, sub_link], check=True)
        send_photo(token, chat_id, tmp_path, caption=f"QR-код подписки для {nick}")
    except Exception as e:
        print(f"[TG BOT] Error sending sub QR: {e}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

# ─── УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЯ ───────────────────────────────────────────────────

@router.callback_query(F.data.startswith("user:delete:confirm:"))
async def user_delete_confirm_callback(callback: CallbackQuery):
    nick = callback.data.split(":")[3]
    text = f"⚠️ Вы уверены, что хотите удалить пользователя <code>{nick}</code> и все его протоколы?"
    await callback.message.edit_text(text, reply_markup=user_delete_confirm_keyboard(nick), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("user:delete:run:"))
async def user_delete_run_callback(callback: CallbackQuery):
    nick = callback.data.split(":")[3]
    
    await notify_and_restart(callback, "Удаление пользователя", delete_user, nick)
    
    # Возвращаемся к списку пользователей
    users = load_users()
    text = "👥 <b>Управление пользователями</b>"
    await callback.message.edit_text(text, reply_markup=users_list_keyboard(users), parse_mode="HTML")

# ─── ДОБАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯ (FSM) ───────────────────────────────────────────

@router.callback_query(F.data == "user:new:step1")
async def add_user_step1(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddUserStates.waiting_nickname)
    text = "➕ <b>Добавление нового пользователя</b>\n\nВведите никнейм пользователя (только английские буквы, цифры, дефис и подчеркивание):"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="user:list")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.message(AddUserStates.waiting_nickname)
async def add_user_nickname_msg(message: Message, state: FSMContext):
    nick = message.text.strip().lower()
    
    if not re.match(r"^[a-z0-9_-]+$", nick):
        await message.answer("❌ Неверный формат никнейма! Допускаются только буквы, цифры, дефис и подчеркивание. Введите еще раз:")
        return
        
    await state.update_data(nickname=nick)
    await state.set_state(AddUserStates.waiting_protocol)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VLESS", callback_data="user:new:proto:vless")],
        [InlineKeyboardButton(text="NaiveProxy", callback_data="user:new:proto:naive")],
        [InlineKeyboardButton(text="Mieru", callback_data="user:new:proto:mieru")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="user:list")]
    ])
    
    await message.answer(f"Никнейм: <code>{nick}</code>\n\nВыберите протокол:", reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("user:new:proto:"))
async def add_user_proto_callback(callback: CallbackQuery, state: FSMContext):
    proto = callback.data.split(":")[3]
    await state.update_data(protocol=proto)
    
    data = await state.get_data()
    nick = data["nickname"]
    
    if proto == "vless":
        await state.set_state(AddUserStates.waiting_type)
        users = load_users()
        user_protocols = [u for u in users if u.get("nickname") == nick]
        existing_vless_types = set(u.get("credentials", {}).get("type", "") for u in user_protocols if u.get("protocol") == "vless")
        
        vless_buttons = []
        if "ws" not in existing_vless_types:
            vless_buttons.append([InlineKeyboardButton(text="WebSocket (ws)", callback_data="user:new:type:ws")])
        if "grpc" not in existing_vless_types:
            vless_buttons.append([InlineKeyboardButton(text="gRPC", callback_data="user:new:type:grpc")])
        if "xhttp" not in existing_vless_types:
            vless_buttons.append([InlineKeyboardButton(text="HTTPUpgrade (xhttp)", callback_data="user:new:type:xhttp")])
            
        back_callback = f"user:info:{nick}" if load_users_exist(nick) else "user:list"
        vless_buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data=back_callback)])
        
        kb = InlineKeyboardMarkup(inline_keyboard=vless_buttons)
        await callback.message.edit_text(f"Никнейм: <code>{nick}</code>\nПротокол: <code>VLESS</code>\n\nВыберите тип транспорта:", reply_markup=kb, parse_mode="HTML")
    else:
        await state.update_data(type="")
        await show_confirm_creation(callback.message, nick, proto, "")
    await callback.answer()

@router.callback_query(F.data.startswith("user:new:type:"))
async def add_user_type_callback(callback: CallbackQuery, state: FSMContext):
    utype = callback.data.split(":")[3]
    await state.update_data(type=utype)
    
    data = await state.get_data()
    nick = data["nickname"]
    proto = data["protocol"]
    
    await show_confirm_creation(callback.message, nick, proto, utype)
    await callback.answer()

async def show_confirm_creation(message: Message, nick: str, proto: str, utype: str):
    proto_lbl = f"{proto.upper()} {utype.upper()}".strip()
    text = (
        "⚙️ <b>Подтверждение создания/добавления:</b>\n\n"
        f"Никнейм: <code>{nick}</code>\n"
        f"Протокол: <code>{proto_lbl}</code>\n\n"
        "Выполнить операцию?"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="user:new:confirm:yes"),
            InlineKeyboardButton(text="❌ Отмена", callback_data=f"user:info:{nick}" if load_users_exist(nick) else "user:list")
        ]
    ])
    await message.edit_text(text, reply_markup=kb, parse_mode="HTML")

def load_users_exist(nick: str) -> bool:
    users = load_users()
    return any(u.get("nickname") == nick for u in users)

@router.callback_query(F.data == "user:new:confirm:yes")
async def add_user_confirm_yes(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    
    nick = data["nickname"]
    proto = data["protocol"]
    utype = data.get("type", "")
    
    await callback.message.edit_text(f"⏳ Добавление конфигурации для <code>{nick}</code>...", parse_mode="HTML")
    
    add_user(nick, proto, utype if utype else "ws")
    render_configs()
    success, msg = validate_and_restart()
    
    if success:
        text = f"🎉 Конфигурация {proto.upper()} для пользователя <code>{nick}</code> успешно создана!\nСлужбы перезапущены."
        # Кнопки возврата к управлению этим пользователем
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="« Перейти к управлению пользователем", callback_data=f"user:info:{nick}")],
            [InlineKeyboardButton(text="« К списку пользователей", callback_data="user:list")]
        ])
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        text = f"❌ Изменения внесены, но произошла ошибка при перезапуске служб:\n<code>{msg}</code>"
        await callback.message.edit_text(text, reply_markup=back_to_main_keyboard(), parse_mode="HTML")
        
    await callback.answer()
