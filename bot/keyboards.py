from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def align_button_text(text: str, target_width: float = 18.0) -> str:
    # Оценка ширины символов для пропорционального шрифта Telegram
    width = 0.0
    for char in text:
        if char in "🟢🔴":
            width += 1.8
        elif char.isupper():
            width += 1.05
        elif char.islower():
            width += 0.8
        elif char == " ":
            width += 0.35
        else:
            width += 0.7
            
    # Добавляем неразрывные пробелы (\u00A0) для выравнивания по левой стороне кнопки
    spaces_to_add = int((target_width - width) / 0.35)
    if spaces_to_add > 0:
        # \u200b - невидимый символ нулевой ширины, служащий якорем на конце
        # без него сервер Telegram обрезает все пробелы в конце текста кнопок
        return text + ("\u00A0" * spaces_to_add) + "\u200b"
    return text

def main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="user:list")],
        [InlineKeyboardButton(text="📊 Диагностика", callback_data="diag:menu")],
        [InlineKeyboardButton(text="🔄 Перезапуск служб", callback_data="services:menu")]
    ])

def back_to_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Главное меню", callback_data="menu:main")]
    ])

def diagnostics_menu_keyboard():
    # Выравниваем кнопки диагностики по левому краю с целевой шириной 18.0
    btn1 = align_button_text("📈 Мониторинг ресурсов", 18.0)
    btn2 = align_button_text("🚀 Тест скорости", 18.0)
    btn3 = align_button_text("⚙️ Пересоздать конфиги", 18.0)
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn1, callback_data="diag:resources")],
        [InlineKeyboardButton(text=btn2, callback_data="diag:speedtest")],
        [InlineKeyboardButton(text=btn3, callback_data="diag:recreate")],
        [InlineKeyboardButton(text="« Главное меню", callback_data="menu:main")]
    ])

def diagnostics_back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Назад в Диагностику", callback_data="diag:menu")],
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
    unique_nicks = sorted(list(set(u.get("nickname") for u in users if u.get("nickname"))))
    
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

def user_info_keyboard(nick: str, protocols: list):
    keyboard = []
    
    # Кнопки для каждого протокола пользователя (выровненные по левому краю с помощью неразрывных пробелов)
    for u in protocols:
        proto = u.get("protocol")
        utype = u.get("credentials", {}).get("type", "")
        enabled = u.get("enabled", True)
        
        status_lbl = "🟢" if enabled else "🔴"
        proto_lbl = f"{proto.upper()} {utype.upper()}".strip()
        
        # Выравниваем текст кнопки по левому краю с целевой шириной 18.0
        btn_text = align_button_text(f"{status_lbl} {proto_lbl}", target_width=18.0)
        
        # Передаем пустую строку вместо None в callback_data, если тип пустой
        callback_data = f"user:proto:manage:{nick}:{proto}:{utype if utype else 'none'}"
        keyboard.append([InlineKeyboardButton(text=btn_text, callback_data=callback_data)])
        
    # Проверяем, сколько протоколов уже настроено
    configured_tuples = set()
    for u in protocols:
        proto = u.get("protocol")
        utype = u.get("credentials", {}).get("type", "")
        configured_tuples.add((proto, utype if utype else ""))
        
    can_add_proto = len(configured_tuples) < 5
        
    # Функциональные кнопки управления пользователем
    row_buttons = []
    if can_add_proto:
        row_buttons.append(InlineKeyboardButton(text="➕ Протокол", callback_data=f"user:proto:add:{nick}"))
    row_buttons.append(InlineKeyboardButton(text="🌀 Подписка", callback_data=f"user:links:{nick}"))
    keyboard.append(row_buttons)
    
    keyboard.append([InlineKeyboardButton(text="🗑️ Удалить пользователя", callback_data=f"user:delete:confirm:{nick}")])
    keyboard.append([InlineKeyboardButton(text="« К списку пользователей", callback_data="user:list")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def proto_manage_keyboard(nick: str, proto: str, utype: str, is_enabled: bool):
    toggle_text = "🔴 Отключить протокол" if is_enabled else "🟢 Включить протокол"
    toggle_val = "0" if is_enabled else "1"
    
    # Заменяем 'none' на пустоту для корректной передачи в callback_data
    utype_val = utype if utype and utype != "none" else "none"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle_text, callback_data=f"user:proto:toggle:{nick}:{proto}:{utype_val}:{toggle_val}")],
        [InlineKeyboardButton(text="🔑 Получить ссылку & QR", callback_data=f"user:proto:links:{nick}:{proto}:{utype_val}")],
        [InlineKeyboardButton(text="🗑️ Удалить этот протокол", callback_data=f"user:proto:delete:confirm:{nick}:{proto}:{utype_val}")],
        [InlineKeyboardButton(text="« Назад к пользователю", callback_data=f"user:info:{nick}")],
        [InlineKeyboardButton(text="« Главное меню", callback_data="menu:main")]
    ])

def proto_delete_confirm_keyboard(nick: str, proto: str, utype: str):
    utype_val = utype if utype and utype != "none" else "none"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗑️ Да, удалить протокол", callback_data=f"user:proto:delete:run:{nick}:{proto}:{utype_val}"),
            InlineKeyboardButton(text="❌ Нет, отмена", callback_data=f"user:proto:manage:{nick}:{proto}:{utype_val}")
        ],
        [InlineKeyboardButton(text="« Главное меню", callback_data="menu:main")]
    ])

def user_delete_confirm_keyboard(nick: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗑️ Да, удалить пользователя", callback_data=f"user:delete:run:{nick}"),
            InlineKeyboardButton(text="❌ Нет, отмена", callback_data=f"user:info:{nick}")
        ],
        [InlineKeyboardButton(text="« Главное меню", callback_data="menu:main")]
    ])
