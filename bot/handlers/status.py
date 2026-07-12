import time
import os
import psutil
import subprocess
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from bot.keyboards import back_to_main_keyboard

router = Router()

def check_service_active(service_name: str) -> str:
    try:
        res = subprocess.run(["systemctl", "is-active", service_name], capture_output=True, text=True)
        status = res.stdout.strip()
        if status == "active":
            return "🟢 работает"
        elif status == "inactive":
            return "🔴 не запущен"
        else:
            return f"⚪ {status}"
    except Exception:
        return "⚪ неизвестно"

def get_status_text() -> str:
    # 1. Опрос служб
    caddy_status = check_service_active("caddy")
    singbox_status = check_service_active("sing-box")
    
    mita_installed = os.path.exists("/usr/bin/mita")
    mita_status = check_service_active("mita") if mita_installed else "⚪ не установлен"
    
    netbird_installed = subprocess.run(["command", "-v", "netbird"], shell=True, capture_output=True).returncode == 0
    netbird_status = check_service_active("netbird") if netbird_installed else "⚪ не установлен"
    
    # 2. Опрос ресурсов
    cpu_pct = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Uptime
    uptime_secs = int(time.time() - psutil.boot_time())
    days, remainder = divmod(uptime_secs, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    
    uptime_str = ""
    if days > 0:
        uptime_str += f"{days} дн. "
    if hours > 0 or days > 0:
        uptime_str += f"{hours} ч. "
    uptime_str += f"{minutes} мин."
    
    # Формируем отчет
    text = "📊 <b>Статус ресурсов и служб</b>\n\n"
    text += "⚙️ <b>Состояние служб:</b>\n"
    text += f"  • Caddy: {caddy_status}\n"
    text += f"  • sing-box: {singbox_status}\n"
    if mita_installed or mita_status != "⚪ не установлен":
        text += f"  • Mieru (mita): {mita_status}\n"
    if netbird_installed or netbird_status != "⚪ не установлен":
        text += f"  • NetBird: {netbird_status}\n"
        
    text += "\n🖥️ <b>Ресурсы сервера:</b>\n"
    text += f"  • CPU: <code>{cpu_pct}%</code>\n"
    text += f"  • RAM: <code>{ram.percent}%</code> ({ram.used // 1024 // 1024} / {ram.total // 1024 // 1024} MB)\n"
    text += f"  • Диск (/): <code>{disk.percent}%</code> ({disk.used // 1024 // 1024 // 1024} / {disk.total // 1024 // 1024 // 1024} GB)\n"
    text += f"  • Аптайм: <code>{uptime_str}</code>\n"
    return text

@router.message(Command("status"))
async def status_command(message: Message):
    text = get_status_text()
    await message.answer(text, reply_markup=back_to_main_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "status:services")
async def status_services_callback(callback: CallbackQuery):
    text = get_status_text()
    await callback.message.edit_text(text, reply_markup=back_to_main_keyboard(), parse_mode="HTML")
    await callback.answer()
