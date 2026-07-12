import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from core.config_manager import load_users, load_env, render_configs, validate_and_restart
from core.user_manager import add_user, delete_user, toggle_user
from bot.keyboards import (
    users_list_keyboard, user_info_keyboard, user_delete_confirm_keyboard,
    back_to_main_keyboard
)
from bot.alerts import send_user_links

router = Router()

class AddUserStates(StatesGroup):
    waiting_nickname = State()
    waiting_protocol = State()
    waiting_type = State()

# ─── СПИСОК ПОЛЬЗОВАТЕЛЕЙ ────────────────────────────────────────────────────

@router.callback_query(F.data == "user:list")
async def list_users_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    users = load_users()
    text = "👥 <b>Список пользователей:</b>\nВыберите пользователя для управления или добавьте нового."
    try:
        await callback.message.edit_text(text, reply_markup=users_list_keyboard(users), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=users_list_keyboard(users), parse_mode="HTML")
        await callback.message.delete()
    await callback.answer()

# ─── ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ ───────────────────────────────────────────────

@router.callback_query(F.data.startswith("user:info:"))
async def user_info_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    nick = callback.data.split(":")[2]
    users = load_users()
    user_protocols = [u for u in users if u.get("nickname") == nick]
    
    if not user_protocols:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return
        
    is_enabled = any(u.get("enabled", True) for u in user_protocols)
    
    text = f"👤 <b>Пользователь:</b> <code>{nick}</code>\n"
    text += f"Статус: {'🟢 Активен' if is_enabled else '🔴 Отключен'}\n\n"
    text += "<b>Настроенные протоколы:</b>\n"
    
    for u in user_protocols:
        proto = u.get("protocol")
        ptype = u.get("credentials", {}).get("type", "")
        proto_lbl = f"{proto.upper()} {ptype.upper()}".strip()
        text += f"  • {proto_lbl}\n"
        
    await callback.message.edit_text(text, reply_markup=user_info_keyboard(nick, is_enabled), parse_mode="HTML")
    await callback.answer()

# ─── ВКЛЮЧЕНИЕ / ВЫКЛЮЧЕНИЕ ──────────────────────────────────────────────────

@router.callback_query(F.data.startswith("user:toggle:"))
async def user_toggle_callback(callback: CallbackQuery):
    _, _, nick, val = callback.data.split(":")
    enabled = val == "1"
    
    await callback.message.edit_text(f"⏳ {'Включение' if enabled else 'Отключение'} пользователя <code>{nick}</code>...", parse_mode="HTML")
    
    toggle_user(nick, enabled)
    render_configs()
    success, msg = validate_and_restart()
    
    if success:
        await callback.answer(f"Пользователь {nick} успешно {'включен' if enabled else 'выключен'}.", show_alert=True)
    else:
        await callback.answer(f"Ошибка перезапуска служб: {msg}", show_alert=True)
        
    # Возвращаемся на экран информации
    users = load_users()
    user_protocols = [u for u in users if u.get("nickname") == nick]
    is_enabled = any(u.get("enabled", True) for u in user_protocols)
    
    text = f"👤 <b>Пользователь:</b> <code>{nick}</code>\n"
    text += f"Статус: {'🟢 Активен' if is_enabled else '🔴 Отключен'}\n\n"
    text += "<b>Настроенные протоколы:</b>\n"
    for u in user_protocols:
        proto = u.get("protocol")
        ptype = u.get("credentials", {}).get("type", "")
        proto_lbl = f"{proto.upper()} {ptype.upper()}".strip()
        text += f"  • {proto_lbl}\n"
        
    await callback.message.edit_text(text, reply_markup=user_info_keyboard(nick, is_enabled), parse_mode="HTML")

# ─── УДАЛЕНИЕ ────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("user:delete:confirm:"))
async def user_delete_confirm_callback(callback: CallbackQuery):
    nick = callback.data.split(":")[3]
    text = f"⚠️ Вы уверены, что хотите полностью удалить пользователя <code>{nick}</code> и все его протоколы?"
    await callback.message.edit_text(text, reply_markup=user_delete_confirm_keyboard(nick), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("user:delete:run:"))
async def user_delete_run_callback(callback: CallbackQuery):
    nick = callback.data.split(":")[3]
    await callback.message.edit_text(f"⏳ Удаление пользователя <code>{nick}</code>...", parse_mode="HTML")
    
    delete_user(nick)
    render_configs()
    success, msg = validate_and_restart()
    
    if success:
        await callback.answer(f"Пользователь {nick} удален.", show_alert=True)
    else:
        await callback.answer(f"Ошибка перезапуска служб: {msg}", show_alert=True)
        
    # Возвращаемся к списку пользователей
    users = load_users()
    text = "👥 <b>Список пользователей:</b>\nВыберите пользователя для управления или добавьте нового."
    await callback.message.edit_text(text, reply_markup=users_list_keyboard(users), parse_mode="HTML")

# ─── ССЫЛКИ И QR-КОДЫ ────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("user:links:") | F.data.startswith("user:qr:"))
async def user_send_links_callback(callback: CallbackQuery):
    nick = callback.data.split(":")[2]
    await callback.answer("⏳ Отправка ссылок и QR-кодов в чат...", show_alert=False)
    send_user_links(callback.from_user.id, nick)

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
    
    # Клавиатура выбора протокола
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
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="WebSocket (ws)", callback_data="user:new:type:ws")],
            [InlineKeyboardButton(text="gRPC", callback_data="user:new:type:grpc")],
            [InlineKeyboardButton(text="HTTPUpgrade (xhttp)", callback_data="user:new:type:xhttp")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="user:list")]
        ])
        await callback.message.edit_text(f"Никнейм: <code>{nick}</code>\nПротокол: <code>VLESS</code>\n\nВыберите тип транспорта:", reply_markup=kb, parse_mode="HTML")
    else:
        # Для Naive/Mieru транспорт не нужен, переходим к подтверждению
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
        "⚙️ <b>Подтверждение создания пользователя:</b>\n\n"
        f"Никнейм: <code>{nick}</code>\n"
        f"Протокол: <code>{proto_lbl}</code>\n\n"
        "Создать пользователя?"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Создать", callback_data="user:new:confirm:yes"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="user:list")
        ]
    ])
    await message.edit_text(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "user:new:confirm:yes")
async def add_user_confirm_yes(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    
    nick = data["nickname"]
    proto = data["protocol"]
    utype = data.get("type", "")
    
    await callback.message.edit_text(f"⏳ Создание пользователя <code>{nick}</code>...", parse_mode="HTML")
    
    # Добавляем пользователя
    add_user(nick, proto, utype if utype else "ws")
    render_configs()
    success, msg = validate_and_restart()
    
    if success:
        text = f"🎉 Пользователь <code>{nick}</code> успешно создан!\nСлужбы перезапущены."
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔑 Получить ссылки в чат", callback_data=f"user:links:{nick}")],
            [InlineKeyboardButton(text="« К списку пользователей", callback_data="user:list")]
        ])
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        text = f"❌ Пользователь создан, но произошла ошибка при перезапуске служб:\n<code>{msg}</code>"
        await callback.message.edit_text(text, reply_markup=back_to_main_keyboard(), parse_mode="HTML")
        
    await callback.answer()
