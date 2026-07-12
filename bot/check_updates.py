import os
import urllib.request
import re
from core.config_manager import PROJECT_ROOT
from bot.alerts import send_alert

NOTIFIED_FILE = os.path.join(PROJECT_ROOT, ".update_notified")

def get_local_version() -> str:
    tbox_path = os.path.join(PROJECT_ROOT, "transferbox")
    if os.path.exists(tbox_path):
        try:
            with open(tbox_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith('VERSION='):
                        return line.split('=')[1].strip('"\'\r\n ')
        except Exception:
            pass
    return "0.0.0"

def get_github_version() -> str:
    url = "https://raw.githubusercontent.com/denash-git/TransferBox/main/transferbox"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TransferBox-Updater"})
        with urllib.request.urlopen(req, timeout=5) as response:
            content = response.read().decode("utf-8")
            for line in content.splitlines():
                if line.startswith('VERSION='):
                    return line.split('=')[1].strip('"\'\r\n ')
    except Exception as e:
        print(f"[TG BOT] Error fetching GitHub version: {e}")
    return ""

def main():
    local_ver = get_local_version()
    latest_ver = get_github_version()
    
    if not latest_ver or latest_ver == local_ver:
        return
        
    # Проверим, не отправляли ли уже уведомление про эту версию
    notified_ver = ""
    if os.path.exists(NOTIFIED_FILE):
        try:
            with open(NOTIFIED_FILE, "r", encoding="utf-8") as f:
                notified_ver = f.read().strip()
        except Exception:
            pass
            
    if notified_ver == latest_ver:
        return
        
    # Отправляем алерт
    send_alert(f"⬆️ <b>Доступно обновление TransferBox!</b>\n\nТекущая версия: <code>{local_ver}</code>\nСвежая версия: <code>{latest_ver}</code>\n\nВы можете обновиться прямо через TUI-меню настроек панели.")
    
    # Сохраняем версию, о которой сообщили
    try:
        with open(NOTIFIED_FILE, "w", encoding="utf-8") as f:
            f.write(latest_ver)
    except Exception as e:
        print(f"[TG BOT] Error writing update notification state: {e}")

if __name__ == "__main__":
    main()
