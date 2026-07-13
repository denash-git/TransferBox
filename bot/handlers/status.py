import time
import os
import psutil
import subprocess
import asyncio
import shutil
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from core.config_manager import render_configs, validate_and_restart
from bot.keyboards import diagnostics_menu_keyboard, diagnostics_back_keyboard

router = Router()

def check_service_active(service_name: str) -> str:
    if service_name == "netbird":
        import shutil
        if shutil.which("netbird") is None:
            return "⚪"
        
        res_active = subprocess.run(["systemctl", "is-active", "netbird"], capture_output=True, text=True)
        if res_active.stdout.strip() != "active":
            return "🔴"
            
        res_status = subprocess.run(["netbird", "status"], capture_output=True, text=True)
        status_out = res_status.stdout + "\n" + res_status.stderr
        if "NeedsLogin" in status_out:
            return "🟡 требует регистрации"
        elif "Connected" in status_out and "Management: Disconnected" not in status_out:
            return "🟢"
        else:
            return "🔴"
    else:
        try:
            res = subprocess.run(["systemctl", "is-active", service_name], capture_output=True, text=True)
            status = res.stdout.strip()
            if status == "active":
                return "🟢"
            else:
                return "🔴"
        except Exception:
            return "⚪"

def get_status_text() -> str:
    # 1. Опрос служб
    caddy_status = check_service_active("caddy")
    singbox_status = check_service_active("sing-box")
    
    mita_installed = os.path.exists("/usr/bin/mita")
    mita_status = check_service_active("mita") if mita_installed else "⚪"
    
    import shutil
    netbird_installed = shutil.which("netbird") is not None
    netbird_status = check_service_active("netbird") if netbird_installed else "⚪"
    
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
    
    # Формируем отчет в виде псевдографического дерева
    text = "📈 <b>Мониторинг ресурсов</b>\n\n"
    text += "⚙️ <b>Состояние служб:</b>\n"
    text += f"├─ Caddy: {caddy_status}\n"
    text += f"├─ sing-box: {singbox_status}\n"
    
    # Добавляем дополнительные службы динамически
    services_lines = []
    if mita_installed or mita_status != "⚪":
        services_lines.append(("Mieru (mita)", mita_status))
    if netbird_installed or netbird_status != "⚪":
        services_lines.append(("NetBird", netbird_status))
        
    if not services_lines:
        text = text.replace("├─ sing-box:", "└─ sing-box:")
    else:
        for idx, (name, val) in enumerate(services_lines):
            prefix = "└─" if idx == len(services_lines) - 1 else "├─"
            text += f"{prefix} {name}: {val}\n"
            
    text += "\n🖥️ <b>Ресурсы сервера:</b>\n"
    text += f"├─ CPU: <code>{cpu_pct}%</code>\n"
    text += f"├─ RAM: <code>{ram.percent}%</code> ({ram.used // 1024 // 1024} / {ram.total // 1024 // 1024} MB)\n"
    text += f"├─ Диск (/): <code>{disk.percent}%</code> ({disk.used // 1024 // 1024 // 1024} / {disk.total // 1024 // 1024 // 1024} GB)\n"
    text += f"└─ Аптайм: <code>{uptime_str}</code>\n"
    return text

# ─── ДИАГНОСТИКА: МЕНЮ ────────────────────────────────────────────────────────

@router.message(Command("diag"))
@router.callback_query(F.data == "diag:menu")
async def diagnostics_menu_callback(event):
    text = "📊 <b>Диагностика</b>"
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
    
    def run_speedtest():
        if not shutil.which("speedtest"):
            import urllib.request
            try:
                url = "https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh"
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req) as response:
                    script_content = response.read()
                subprocess.run(
                    ["bash"],
                    input=script_content,
                    capture_output=True
                )
            except Exception:
                pass
            subprocess.run(["apt-get", "install", "-y", "speedtest"], capture_output=True)
            
        return subprocess.run(["speedtest", "--accept-license", "--accept-gdpr"], capture_output=True, text=True)
        
    res = await asyncio.to_thread(run_speedtest)
    
    if res.returncode == 0:
        output_lines = []
        for line in res.stdout.split("\n"):
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
