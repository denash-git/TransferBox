from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from bot.keyboards import main_menu_keyboard
from core.config_manager import get_app_version

router = Router()

def get_start_text() -> str:
    version = get_app_version()
    return f"📦 <b>TransferBox v. {version}</b>\n<b>Панель Управления</b>"

@router.message(Command("start"))
async def start_cmd(message: Message):
    text = get_start_text()
    await message.answer(text, reply_markup=main_menu_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "menu:main")
async def main_menu_callback(callback: CallbackQuery):
    text = get_start_text()
    try:
        await callback.message.edit_text(text, reply_markup=main_menu_keyboard(), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=main_menu_keyboard(), parse_mode="HTML")
        await callback.message.delete()
    await callback.answer()
