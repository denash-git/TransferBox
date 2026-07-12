import os
import json
import subprocess
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
    for s in SERVICES:
        state = get_service_state(s)
        # Игнорируем не установленные службы
        if state == "not_installed":
            continue
        new_states[s] = state
        
    # Сравниваем состояния
    for s, state in new_states.items():
        if s in old_states:
            old_state = old_states[s]
            if old_state != state:
                if state == "active":
                    send_alert(f"🟢 <b>Служба {s} восстановлена</b> (статус: active)")
                else:
                    send_alert(f"🔴 <b>Служба {s} остановлена</b> (статус: {state})")
        else:
            # Если служба новая и не активна при первом запуске крона, шлем алерт
            if state != "active":
                send_alert(f"🔴 <b>Служба {s} не запущена</b> (статус: {state})")
                
    # Сохраняем новые состояния
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(new_states, f, indent=2)
    except Exception as e:
        print(f"[TG BOT] Error writing service states: {e}")

if __name__ == "__main__":
    main()
