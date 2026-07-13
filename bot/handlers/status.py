import time
import os
import psutil
import subprocess
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from core.config_manager import render_configs, validate_and_restart
from bot.keyboards import diagnostics_menu_keyboard, diagnostics_back_keyboard

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
    
    # Формируем отчет с красивым выравниванием
    text = "📈 <b>Мониторинг ресурсов и служб</b>\n\n"
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

# ─── ДИАГНОСТИКА: МЕНЮ ────────────────────────────────────────────────────────

@router.message(Command("diag"))
@router.callback_query(F.data == "diag:menu")
async def diagnostics_menu_callback(event):
    text = "📊 <b>Диагностика системы</b>\n\nВыберите нужный инструмент диагностики:"
    if isinstance(event, CallbackQuery):
        try:
            await event.message.edit_text(text, reply_markup=diagnostics_menu_keyboard(), parse_mode="HTML")
        except Exception:
            await event.message.answer(text, reply_markup=diagnostics_menu_keyboard(), parse_mode="HTML")
            await event.message.delete()
        await event.answer()
    else:
        await event.answer(text, reply_markup=diagnostics_menu_keyboard(), parse_mode="HTML")

# ─── ДИАГНОСТИКА: МОНИТОРИНГ РЕСУРСОВ ─────────────────────────────────────────

@router.message(Command("status"))
@router.callback_query(F.data == "diag:resources")
async def diagnostics_resources_callback(event):
    text = get_status_text()
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=diagnostics_back_keyboard(), parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=diagnostics_back_keyboard(), parse_mode="HTML")

# ─── ДИАГНОСТИКА: ТЕСТ СКОРОСТИ ────────────────────────────────────────────────

@router.callback_query(F.data == "diag:speedtest")
async def diagnostics_speedtest_callback(callback: CallbackQuery):
    await callback.message.edit_text("⏳ <b>Запуск теста скорости на VPS...</b>\nЭто может занять до 30 секунд. Пожалуйста, подождите.", parse_mode="HTML")
    await callback.answer()
    
    # 1. Проверяем установку Ookla speedtest
    res_installed = subprocess.run(["which", "speedtest"], capture_output=True)
    if res_installed.returncode != 0:
        # Устанавливаем официальный speedtest
        subprocess.run("curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | bash", shell=True, capture_output=True)
        subprocess.run(["apt-get", "install", "-y", "speedtest"], capture_output=True)
        
    # 2. Выполняем тест
    res = subprocess.run(["speedtest", "--accept-license", "--accept-gdpr"], capture_output=True, text=True)
    
    if res.returncode == 0:
        output_lines = []
        for line in res.stdout.split("\n"):
            # Пропускаем пустые и рекламные строки Ookla
            if not line.strip() or "Speedtest by Ookla" in line or "https://" in line:
                continue
            output_lines.append(line.strip())
        output_txt = "\n".join(output_lines)
        text = f"🚀 <b>Результаты теста скорости на VPS:</b>\n\n<code>{output_txt}</code>"
    else:
        text = f"❌ <b>Ошибка запуска Speedtest:</b>\n\n<code>{res.stderr or res.stdout}</code>"
        
    await callback.message.edit_text(text, reply_markup=diagnostics_back_keyboard(), parse_mode="HTML")

# ─── ДИАГНОСТИКА: ПЕРЕСОЗДАТЬ КОНФИГИ ─────────────────────────────────────────

@router.callback_query(F.data == "diag:recreate")
async def diagnostics_recreate_callback(callback: CallbackQuery):
    await callback.message.edit_text("⏳ <b>Перегенерация конфигурационных файлов...</b>", parse_mode="HTML")
    await callback.answer()
    
    try:
        render_configs()
        success, msg = validate_and_restart()
        if success:
            text = "✅ <b>Успешно!</b>\nВсе конфигурационные файлы пересозданы, службы успешно перезапущены."
        else:
            text = f"❌ <b>Конфиги пересозданы, но служба не запустилась:</b>\n\n<code>{msg}</code>"
    except Exception as e:
        text = f"❌ <b>Критическая ошибка перегенерации конфигов:</b>\n\n<code>{e}</code>"
        
    await callback.message.edit_text(text, reply_markup=diagnostics_back_keyboard(), parse_mode="HTML")
