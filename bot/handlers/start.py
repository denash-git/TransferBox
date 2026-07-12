from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from bot.keyboards import main_menu_keyboard

router = Router()

@router.message(Command("start"))
async def start_cmd(message: Message):
    text = (
        "📦 <b>TransferBox Панель Управления</b>\n\n"
        "Добро пожаловать в Telegram-бот панели управления TransferBox!\n"
        "Вы можете управлять пользователями, отслеживать статус ресурсов и перезапускать службы."
    )
    await message.answer(text, reply_markup=main_menu_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "menu:main")
async def main_menu_callback(callback: CallbackQuery):
    text = (
        "📦 <b>TransferBox Панель Управления</b>\n\n"
        "Главное меню управления."
    )
    try:
        await callback.message.edit_text(text, reply_markup=main_menu_keyboard(), parse_mode="HTML")
    except Exception:
        # Если сообщение не изменилось, просто отправляем новое
        await callback.message.answer(text, reply_markup=main_menu_keyboard(), parse_mode="HTML")
        await callback.message.delete()
    await callback.answer()
