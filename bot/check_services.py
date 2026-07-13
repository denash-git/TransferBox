import os
import json
import subprocess
import psutil
from core.config_manager import PROJECT_ROOT
from bot.alerts import send_alert

SERVICES = ["caddy", "sing-box", "mita", "netbird"]
STATE_FILE = os.path.join(PROJECT_ROOT, ".service_states")

def get_service_state(name: str) -> str:
    # Проверяем, существует ли юнит
    res_exist = subprocess.run(["systemctl", "list-unit-files", f"{name}.service"], capture_output=True, text=True)
    if f"{name}.service" not in res_exist.stdout:
        return "not_installed"
        
    res_active = subprocess.run(["systemctl", "is-active", name], capture_output=True, text=True)
    return res_active.stdout.strip()

def main():
    # Загружаем предыдущие состояния
    old_states = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                old_states = json.load(f)
        except Exception:
            pass
            
    new_states = {}
    
    # 1. Проверяем службы
    for s in SERVICES:
        state = get_service_state(s)
        if state == "not_installed":
            continue
        new_states[s] = state
        
    # Сравниваем состояния служб
    for s, state in new_states.items():
        if s in old_states:
            old_state = old_states[s]
            if old_state != state:
                if state == "active":
                    send_alert(f"🟢 <b>Служба {s} восстановлена</b>")
                else:
                    send_alert(f"🔴 <b>Служба {s} остановлена</b>")
        else:
            if state != "active":
                send_alert(f"🔴 <b>Служба {s} не запущена</b>")

    # 2. Проверяем ресурсы сервера (CPU, RAM, Диск)
    # Используем интервал 1.0 секунда, чтобы избежать блокировки cron
    cpu_pct = psutil.cpu_percent(interval=1.0)
    ram_pct = psutil.virtual_memory().percent
    disk_pct = psutil.disk_usage('/').percent
    
    # Считываем старые флаги алертов
    cpu_alert_sent = old_states.get("_cpu_alert_sent", False)
    ram_alert_sent = old_states.get("_ram_alert_sent", False)
    disk_alert_sent = old_states.get("_disk_alert_sent", False)
    
    # Проверка CPU (порог 90% для алерта, 80% для сброса)
    if cpu_pct > 90.0:
        if not cpu_alert_sent:
            send_alert(f"⚠️ <b>Критическая нагрузка на CPU: {cpu_pct}%</b>")
            new_states["_cpu_alert_sent"] = True
        else:
            new_states["_cpu_alert_sent"] = True
    else:
        if cpu_pct < 80.0 and cpu_alert_sent:
            send_alert(f"🟢 <b>Нагрузка на CPU нормализована: {cpu_pct}%</b>")
            new_states["_cpu_alert_sent"] = False
        else:
            new_states["_cpu_alert_sent"] = cpu_alert_sent
            
    # Проверка RAM (порог 90% для алерта, 80% для сброса)
    if ram_pct > 90.0:
        if not ram_alert_sent:
            send_alert(f"⚠️ <b>Критическое потребление памяти RAM: {ram_pct}%</b>")
            new_states["_ram_alert_sent"] = True
        else:
            new_states["_ram_alert_sent"] = True
    else:
        if ram_pct < 80.0 and ram_alert_sent:
            send_alert(f"🟢 <b>Потребление памяти RAM нормализовано: {ram_pct}%</b>")
            new_states["_ram_alert_sent"] = False
        else:
            new_states["_ram_alert_sent"] = ram_alert_sent
            
    # Проверка диска (порог 90% для алерта, 85% для сброса)
    if disk_pct > 90.0:
        if not disk_alert_sent:
            send_alert(f"⚠️ <b>Критическое заполнение диска: {disk_pct}%</b>")
            new_states["_disk_alert_sent"] = True
        else:
            new_states["_disk_alert_sent"] = True
    else:
        if disk_pct < 85.0 and disk_alert_sent:
            send_alert(f"🟢 <b>Свободное место на диске восстановлено: {disk_pct}%</b>")
            new_states["_disk_alert_sent"] = False
        else:
            new_states["_disk_alert_sent"] = disk_alert_sent
            
    # Сохраняем новые состояния
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(new_states, f, indent=2)
    except Exception as e:
        print(f"[TG BOT] Error writing states: {e}")

if __name__ == "__main__":
    main()
