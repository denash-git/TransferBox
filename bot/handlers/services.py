import subprocess
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.filters import Command
from bot.keyboards import (
    services_menu_keyboard, service_confirm_keyboard, back_to_main_keyboard
)

router = Router()

@router.message(Command("services"))
@router.callback_query(F.data == "services:menu")
async def services_menu_callback(event):
    text = "🔄 <b>Управление службами</b>\n\nВыберите службу для перезапуска:"
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=services_menu_keyboard(), parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=services_menu_keyboard(), parse_mode="HTML")

@router.callback_query(F.data.startswith("services:confirm:"))
async def services_confirm_callback(callback: CallbackQuery):
    service = callback.data.split(":")[2]
    service_lbl = "все прокси-службы" if service == "all" else f"службу {service}"
    text = f"❓ Вы действительно хотите перезапустить {service_lbl}?"
    await callback.message.edit_text(text, reply_markup=service_confirm_keyboard(service), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("services:run:"))
async def services_run_callback(callback: CallbackQuery):
    service = callback.data.split(":")[2]
    service_lbl = "Все службы" if service == "all" else service
    
    await callback.message.edit_text(f"⏳ Перезапуск {service_lbl}...", parse_mode="HTML")
    
    services_to_restart = []
    if service == "all":
        services_to_restart = ["caddy", "sing-box"]
        # Добавляем опциональные службы, если они установлены
        import os
        import shutil
        if os.path.exists("/usr/bin/mita"):
            services_to_restart.append("mita")
        if shutil.which("netbird") is not None:
            services_to_restart.append("netbird")
    else:
        services_to_restart = [service]
        
    failed = []
    for s in services_to_restart:
        res = subprocess.run(["systemctl", "restart", s], capture_output=True, text=True)
        if res.returncode != 0:
            failed.append(s)
            
    if not failed:
        text = f"🟢 <b>Успешно!</b>\nПерезапуск {service_lbl} выполнен успешно."
    else:
        text = f"🔴 <b>Ошибка!</b>\nНе удалось перезапустить службы: {', '.join(failed)}."
        
    await callback.message.edit_text(text, reply_markup=back_to_main_keyboard(), parse_mode="HTML")
    await callback.answer()
