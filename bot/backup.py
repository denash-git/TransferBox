import os
import random
import datetime
import subprocess
import requests
from core.config_manager import PROJECT_ROOT, load_env

def run_backup() -> tuple[bool, str]:
    env = load_env()
    token = env.get("TG_BOT_TOKEN")
    chat_id = env.get("TG_CHAT_ID")
    backup_password = env.get("BACKUP_PASSWORD", "").strip()
    
    if not token or not chat_id:
        return False, "TG_BOT_TOKEN или TG_CHAT_ID не настроены в instance.env"
        
    if not backup_password:
        return False, "Пароль для бэкапов не задан. Задайте его в настройках."
        
    # Проверяем установлен ли zip
    res_installed = subprocess.run(["which", "zip"], capture_output=True)
    if res_installed.returncode != 0:
        subprocess.run(["apt-get", "update"], capture_output=True)
        subprocess.run(["apt-get", "install", "-y", "zip"], capture_output=True)
        
    # Пути
    users_path = os.path.join(PROJECT_ROOT, "users.json")
    env_path = os.path.join(PROJECT_ROOT, "instance.env")
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    zip_filename = f"transferbox_backup_{timestamp}_pass.zip"
    zip_path = f"/tmp/{zip_filename}"
    
    if os.path.exists(zip_path):
        os.remove(zip_path)
        
    # Создаем зашифрованный ZIP
    cmd = ["zip", "-P", backup_password, "-j", zip_path, users_path, env_path]
    res_zip = subprocess.run(cmd, capture_output=True, text=True)
    
    if res_zip.returncode != 0:
        return False, f"Ошибка создания zip: {res_zip.stderr}"
        
    # Отправляем файл в Telegram
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        with open(zip_path, "rb") as f:
            resp = requests.post(
                url,
                data={
                    "chat_id": chat_id,
                    "caption": f"💾 <b>Зашифрованный бэкап TransferBox</b>\n\n📅 Дата: <code>{date_str}</code>\n🔑 Архив защищен вашим паролем бэкапов.",
                    "parse_mode": "HTML"
                },
                files={"document": (zip_filename, f)},
                timeout=30
            )
            
        if resp.status_code == 200:
            return True, "Резервная копия успешно отправлена."
        else:
            return False, f"Ошибка Telegram API: {resp.text}"
    except Exception as e:
        return False, f"Ошибка отправки: {e}"
    finally:
        if os.path.exists(zip_path):
            os.unlink(zip_path)

if __name__ == "__main__":
    success, msg = run_backup()
    print(f"Success: {success}, Msg: {msg}")

