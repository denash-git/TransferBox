import time
import os
import re
import json
import psutil
import subprocess
import asyncio
import shutil
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from core.config_manager import render_configs, validate_and_restart
from core.security_manager import is_security_active
from bot.handlers.settings import is_bbr_active
from bot.keyboards import (
    diagnostics_menu_keyboard, diagnostics_back_keyboard,
    speedtest_menu_keyboard, iperf_running_keyboard
)

router = Router()

# Глобальная переменная для фонового процесса iperf3
_active_iperf_proc = None
_iperf_cleanup_task = None


def check_service_active(service_name: str) -> str:
    if service_name == "netbird":
        if shutil.which("netbird") is None:
            return "⚪ не установлен"
        
        res_active = subprocess.run(["systemctl", "is-active", "netbird"], capture_output=True, text=True)
        if res_active.stdout.strip() != "active":
            return "🔴 остановлен"
            
        res_status = subprocess.run(["netbird", "status"], capture_output=True, text=True)
        status_out = res_status.stdout + "\n" + res_status.stderr
        if "NeedsLogin" in status_out:
            return "🟡 требует регистрации"
        elif "Connected" in status_out and "Management: Disconnected" not in status_out:
            return "🟢 подключен"
        else:
            return "🔴 отключен"
    else:
        try:
            res = subprocess.run(["systemctl", "is-active", service_name], capture_output=True, text=True)
            status = res.stdout.strip()
            if status == "active":
                return "🟢 работает"
            else:
                return "🔴 не запущен"
        except Exception:
            return "⚪ не установлен"


def get_status_text() -> str:
    # 1. Опрос всех ключевых служб
    caddy_status = check_service_active("caddy")
    singbox_status = check_service_active("sing-box")
    
    mita_installed = os.path.exists("/usr/bin/mita")
    mita_status = check_service_active("mita") if mita_installed else "⚪ не установлен"
    
    netbird_installed = shutil.which("netbird") is not None
    netbird_status = check_service_active("netbird") if netbird_installed else "⚪ не установлен"
    
    f2b_status = "🟢 активна" if is_security_active() else "🔴 отключена"
    bbr_status = "🟢 активен" if is_bbr_active() else "🔴 отключен"
    
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
    text = "📈 <b>Мониторинг ресурсов и служб</b>\n\n"
    text += "⚙️ <b>Состояние служб:</b>\n"
    text += f"├─ Caddy: {caddy_status}\n"
    text += f"├─ sing-box: {singbox_status}\n"
    text += f"├─ Mieru: {mita_status}\n"
    text += f"├─ NetBird: {netbird_status}\n"
    text += f"├─ Защита (Fail2ban): {f2b_status}\n"
    text += f"└─ TCP BBR: {bbr_status}\n"
            
    text += "\n🖥️ <b>Ресурсы сервера:</b>\n"
    text += f"├─ CPU: <code>{cpu_pct}%</code>\n"
    text += f"├─ RAM: <code>{ram.percent}%</code> ({ram.used // 1024 // 1024} / {ram.total // 1024 // 1024} MB)\n"
    text += f"├─ Диск (/): <code>{disk.percent}%</code> ({disk.used // 1024 // 1024 // 1024} / {disk.total // 1024 // 1024 // 1024} GB)\n"
    text += f"└─ Аптайм: <code>{uptime_str}</code>\n"
    return text


def get_vps_ip() -> str:
    try:
        res = subprocess.run(["curl", "-4", "-s", "--connect-timeout", "3", "https://api.ipify.org"], capture_output=True, text=True)
        ip = res.stdout.strip()
        if ip:
            return ip
    except Exception:
        pass
    try:
        res = subprocess.run(["curl", "-4", "-s", "--connect-timeout", "3", "https://ifconfig.me"], capture_output=True, text=True)
        ip = res.stdout.strip()
        if ip:
            return ip
    except Exception:
        pass
    return "ВАШ_IP_VPS"


def format_speedtest_result(raw_stdout: str) -> str:
    # 1. Попытка распарсить как JSON
    for line in raw_stdout.splitlines():
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                data = json.loads(line)
                srv = data.get("server", {})
                srv_name = srv.get("name", "Неизвестно")
                srv_loc = srv.get("location", "")
                srv_id = srv.get("id", "")
                srv_str = f"{srv_name}"
                if srv_loc:
                    srv_str += f" - {srv_loc}"
                if srv_id:
                    srv_str += f" (id: {srv_id})"

                isp = data.get("isp", "Неизвестно")
                ping = data.get("ping", {})
                latency = ping.get("latency", 0.0)
                jitter = ping.get("jitter", 0.0)

                dl_bandwidth = data.get("download", {}).get("bandwidth", 0)
                dl_mbps = round((dl_bandwidth * 8) / 1_000_000, 2)

                ul_bandwidth = data.get("upload", {}).get("bandwidth", 0)
                ul_mbps = round((ul_bandwidth * 8) / 1_000_000, 2)

                packet_loss = data.get("packetLoss", 0.0)
                loss_str = f"{packet_loss:.1f}%" if packet_loss is not None else "0.0%"

                return (
                    "🚀 <b>Результаты теста скорости VPS → Интернет:</b>\n\n"
                    f"🌐 <b>Сервер:</b> <code>{srv_str}</code>\n"
                    f"🏢 <b>Провайдер:</b> <code>{isp}</code>\n\n"
                    f"⚡ <b>Задержка (Ping):</b> <code>{latency:.2f} ms</code> (jitter: <code>{jitter:.2f} ms</code>)\n"
                    f"📥 <b>Входящая (Download):</b> <code>{dl_mbps} Mbps</code>\n"
                    f"📤 <b>Исходящая (Upload):</b> <code>{ul_mbps} Mbps</code>\n"
                    f"📊 <b>Потери пакетов:</b> <code>{loss_str}</code>"
                )
            except Exception:
                pass

    # 2. Текстовый парсер Ookla Speedtest
    srv_match = re.search(r"Server:\s*(.+)", raw_stdout)
    isp_match = re.search(r"ISP:\s*(.+)", raw_stdout)
    latency_match = re.search(r"(?:Idle Latency|Latency):\s*([\d\.]+)\s*ms\s*(?:\(jitter:\s*([\d\.]+)ms)?", raw_stdout, re.I)
    dl_match = re.search(r"Download:\s*([\d\.]+)\s*Mbps", raw_stdout, re.I)
    ul_match = re.search(r"Upload:\s*([\d\.]+)\s*Mbps", raw_stdout, re.I)
    loss_match = re.search(r"Packet Loss:\s*([\d\.]+)%", raw_stdout, re.I)

    srv = srv_match.group(1).strip() if srv_match else "Неизвестно"
    isp = isp_match.group(1).strip() if isp_match else "Неизвестно"
    lat = latency_match.group(1) if latency_match else "—"
    jit = latency_match.group(2) if (latency_match and latency_match.group(2)) else ""
    dl = dl_match.group(1) if dl_match else "—"
    ul = ul_match.group(1) if ul_match else "—"
    loss = (loss_match.group(1) + "%") if loss_match else "0.0%"

    ping_str = f"<code>{lat} ms</code>"
    if jit:
        ping_str += f" (jitter: <code>{jit} ms</code>)"

    return (
        "🚀 <b>Результаты теста скорости VPS → Интернет:</b>\n\n"
        f"🌐 <b>Сервер:</b> <code>{srv}</code>\n"
        f"🏢 <b>Провайдер:</b> <code>{isp}</code>\n\n"
        f"⚡ <b>Задержка (Ping):</b> {ping_str}\n"
        f"📥 <b>Входящая (Download):</b> <code>{dl} Mbps</code>\n"
        f"📤 <b>Исходящая (Upload):</b> <code>{ul} Mbps</code>\n"
        f"📊 <b>Потери пакетов:</b> <code>{loss}</code>"
    )


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


# ─── ДИАГНОСТИКА: ПОДМЕНЮ ТЕСТОВ СКОРОСТИ ─────────────────────────────────────

@router.callback_query(F.data == "diag:speedtest")
async def diagnostics_speed_menu_callback(callback: CallbackQuery):
    text = (
        "🚀 <b>Тестирование скорости сети</b>\n\n"
        "Выберите тип замера скорости:\n\n"
        "• <b>VPS → Интернет:</b> официальный замер канала сервера до узлов Ookla Speedtest.\n"
        "• <b>Client ↔ VPS (iperf3):</b> замер прямого канала между вашим ПК/смартфоном и сервером."
    )
    await callback.message.edit_text(text, reply_markup=speedtest_menu_keyboard(), parse_mode="HTML")
    await callback.answer()


# ─── ДИАГНОСТИКА: ТЕСТ VPS → ИНТЕРНЕТ (OOKLA) ─────────────────────────────────

@router.callback_query(F.data == "diag:speed_ookla")
async def diagnostics_speed_ookla_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        "⏳ <b>Запуск теста скорости VPS → Интернет...</b>\n"
        "Пожалуйста, подождите 15-30 секунд, идет замер пропускной способности...",
        parse_mode="HTML"
    )
    await callback.answer()

    def run_speedtest():
        if not shutil.which("speedtest"):
            import urllib.request
            try:
                url = "https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh"
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req) as response:
                    script_content = response.read()
                subprocess.run(["bash"], input=script_content, capture_output=True)
            except Exception:
                pass
            subprocess.run(["apt-get", "install", "-y", "speedtest"], capture_output=True)

        # Пробуем запустить с форматом JSON
        proc = subprocess.run(
            ["speedtest", "--accept-license", "--accept-gdpr", "--format=json"],
            capture_output=True,
            text=True
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.returncode, proc.stdout
        # Fallback к обычному текстовому выводу
        proc_text = subprocess.run(
            ["speedtest", "--accept-license", "--accept-gdpr"],
            capture_output=True,
            text=True
        )
        return proc_text.returncode, proc_text.stdout or proc_text.stderr

    code, output = await asyncio.to_thread(run_speedtest)

    if code == 0 and output:
        text = format_speedtest_result(output)
    else:
        text = f"❌ <b>Ошибка запуска Speedtest:</b>\n\n<code>{output}</code>"

    await callback.message.edit_text(text, reply_markup=speedtest_menu_keyboard(), parse_mode="HTML")


# ─── ДИАГНОСТИКА: CLIENT ↔ VPS (IPERF3) ────────────────────────────────────────

def cleanup_iperf():
    global _active_iperf_proc
    if _active_iperf_proc:
        try:
            _active_iperf_proc.terminate()
            _active_iperf_proc.kill()
        except Exception:
            pass
        _active_iperf_proc = None

    subprocess.run(["pkill", "-f", "iperf3 -s"], capture_output=True)
    subprocess.run(["ufw", "delete", "allow", "5201/tcp"], capture_output=True)
    subprocess.run(["ufw", "delete", "allow", "5201/udp"], capture_output=True)


async def iperf_auto_timer(timeout: int = 180):
    await asyncio.sleep(timeout)
    cleanup_iperf()


@router.callback_query(F.data == "diag:speed_iperf")
async def diagnostics_speed_iperf_callback(callback: CallbackQuery):
    global _active_iperf_proc, _iperf_cleanup_task

    await callback.message.edit_text("⏳ <b>Подготовка сервера iperf3...</b>", parse_mode="HTML")
    await callback.answer()

    # 1. Проверяем наличие iperf3
    if not shutil.which("iperf3"):
        await asyncio.to_thread(lambda: subprocess.run(["apt-get", "install", "-y", "-qq", "iperf3"], capture_output=True))

    if not shutil.which("iperf3"):
        await callback.message.edit_text(
            "❌ <b>Не удалось установить iperf3 на сервере.</b>\nУстановите вручную: <code>apt install iperf3</code>",
            reply_markup=speedtest_menu_keyboard(),
            parse_mode="HTML"
        )
        return

    # 2. Очищаем старые сессии и открываем порт в UFW
    cleanup_iperf()
    subprocess.run(["ufw", "allow", "5201/tcp", "comment", "iperf3 TCP"], capture_output=True)
    subprocess.run(["ufw", "allow", "5201/udp", "comment", "iperf3 UDP"], capture_output=True)

    # 3. Запускаем сервер iperf3
    try:
        _active_iperf_proc = subprocess.Popen(["iperf3", "-s"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        cleanup_iperf()
        await callback.message.edit_text(
            f"❌ <b>Ошибка запуска iperf3:</b> {e}",
            reply_markup=speedtest_menu_keyboard(),
            parse_mode="HTML"
        )
        return

    # Запускаем авто-таймаут на 3 минуты для закрытия порта и остановки
    if _iperf_cleanup_task and not _iperf_cleanup_task.done():
        _iperf_cleanup_task.cancel()
    _iperf_cleanup_task = asyncio.create_task(iperf_auto_timer(180))

    vps_ip = await asyncio.to_thread(get_vps_ip)

    text = (
        "📶 <b>Замер скорости: Client ↔ VPS (iperf3)</b>\n\n"
        "🟢 <b>Сервер iperf3 временно запущен на VPS!</b>\n"
        "<i>Служба и порт 5201 в фаерволе автоматически закроются через 3 минуты (или по кнопке «Остановить iperf3»).</i>\n\n"
        "💻 <b>Команды для терминала ПК (Windows / Mac / Linux):</b>\n"
        "• Скачивание (клиент → VPS):\n"
        f"<code>iperf3 -c {vps_ip}</code>\n"
        "• Отдача (VPS → клиент):\n"
        f"<code>iperf3 -c {vps_ip} -R</code>\n\n"
        "📱 <b>Приложения для смартфонов:</b>\n"
        "• Android: <b>Magic iPerf</b>\n"
        "• iOS: <b>HE.NET Network Tools</b>\n"
        f"Адрес сервера: <code>{vps_ip}</code>, порт: <code>5201</code>"
    )

    await callback.message.edit_text(text, reply_markup=iperf_running_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "diag:iperf_stop")
async def diagnostics_iperf_stop_callback(callback: CallbackQuery):
    cleanup_iperf()
    text = (
        "📶 <b>Замер скорости: Client ↔ VPS (iperf3)</b>\n\n"
        "⚪ <b>Сервер iperf3 остановлен.</b>\n"
        "Порт 5201 в фаерволе UFW успешно закрыт."
    )
    await callback.message.edit_text(text, reply_markup=speedtest_menu_keyboard(), parse_mode="HTML")
    await callback.answer("iperf3 остановлен, порт закрыт", show_alert=False)


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
