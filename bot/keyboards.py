from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="user:list")],
        [InlineKeyboardButton(text="📊 Ресурсы и службы", callback_data="status:services")],
        [InlineKeyboardButton(text="🔄 Перезапуск служб", callback_data="services:menu")]
    ])

def back_to_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Главное меню", callback_data="menu:main")]
    ])

def services_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Caddy", callback_data="services:confirm:caddy"),
            InlineKeyboardButton(text="sing-box", callback_data="services:confirm:sing-box")
        ],
        [
            InlineKeyboardButton(text="Mieru", callback_data="services:confirm:mita"),
            InlineKeyboardButton(text="NetBird", callback_data="services:confirm:netbird")
        ],
        [InlineKeyboardButton(text="🔄 Все службы", callback_data="services:confirm:all")],
        [InlineKeyboardButton(text="« Главное меню", callback_data="menu:main")]
    ])

def service_confirm_keyboard(service: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, перезапустить", callback_data=f"services:run:{service}"),
            InlineKeyboardButton(text="❌ Нет, отмена", callback_data="services:menu")
        ]
    ])

def users_list_keyboard(users: list):
    keyboard = []
    # Сгруппируем пользователей по именам (поскольку один никнейм может иметь несколько протоколов)
    unique_nicks = sorted(list(set(u.get("nickname") for u in users if u.get("nickname"))))
    
    # Добавляем кнопки для каждого пользователя (по 2 в ряд)
    row = []
    for nick in unique_nicks:
        row.append(InlineKeyboardButton(text=f"👤 {nick}", callback_data=f"user:info:{nick}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    keyboard.append([InlineKeyboardButton(text="➕ Добавить пользователя", callback_data="user:new:step1")])
    keyboard.append([InlineKeyboardButton(text="« Главное меню", callback_data="menu:main")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def user_info_keyboard(nick: str, is_enabled: bool):
    toggle_text = "🔴 Выключить" if is_enabled else "🟢 Включить"
    toggle_val = "0" if is_enabled else "1"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔑 Ссылки", callback_data=f"user:links:{nick}"),
            InlineKeyboardButton(text="📡 QR-коды", callback_data=f"user:qr:{nick}")
        ],
        [InlineKeyboardButton(text=toggle_text, callback_data=f"user:toggle:{nick}:{toggle_val}")],
        [InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"user:delete:confirm:{nick}")],
        [InlineKeyboardButton(text="« К списку пользователей", callback_data="user:list")]
    ])

def user_delete_confirm_keyboard(nick: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗑️ Да, удалить", callback_data=f"user:delete:run:{nick}"),
            InlineKeyboardButton(text="❌ Нет, отмена", callback_data=f"user:info:{nick}")
        ]
    ])
