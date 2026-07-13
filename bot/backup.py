import os
import random
import string
import datetime
import subprocess
import requests
from core.config_manager import PROJECT_ROOT, load_env, save_env
from bot.alerts import send_alert

def generate_random_password(length=16) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))

def run_backup() -> tuple[bool, str]:
    env = load_env()
    token = env.get("TG_BOT_TOKEN")
    chat_id = env.get("TG_CHAT_ID")
    
    if not token or not chat_id:
        return False, "TG_BOT_TOKEN или TG_CHAT_ID не настроены в instance.env"
        
    # Проверяем и генерируем пароль шифрования если отсутствует
    password = env.get("BACKUP_PASSWORD")
    if not password:
        password = generate_random_password()
        env["BACKUP_PASSWORD"] = password
        save_env(env)
        # Отправляем сообщение с новым паролем
        send_alert(
            f"🔑 <b>Создан пароль шифрования бэкапов:</b> <code>{password}</code>\n\n"
            "Пожалуйста, запишите и сохраните этот пароль! Все резервные копии, "
            "отправляемые ботом в Telegram, будут зашифрованы им. Без него распаковать бэкап не получится."
        )
        
    # Проверяем установлен ли zip
    res_installed = subprocess.run(["which", "zip"], capture_output=True)
    if res_installed.returncode != 0:
        subprocess.run(["apt-get", "update"], capture_output=True)
        subprocess.run(["apt-get", "install", "-y", "zip"], capture_output=True)
        
    # Пути
    users_path = os.path.join(PROJECT_ROOT, "users.json")
    env_path = os.path.join(PROJECT_ROOT, "instance.env")
    zip_path = "/tmp/transferbox_backup.zip"
    
    if os.path.exists(zip_path):
        os.remove(zip_path)
        
    # Создаем зашифрованный ZIP
    # -j отбрасывает структуру папок (файлы будут лежать в корне zip)
    cmd = ["zip", "-P", password, "-j", zip_path, users_path, env_path]
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
                    "caption": f"💾 <b>Зашифрованный бэкап TransferBox</b>\n\n📅 Дата: <code>{date_str}</code>",
                    "parse_mode": "HTML"
                },
                files={"document": f},
                timeout=30
            )
            
        if resp.status_code == 200:
            return True, "Резервная копия успешно отправлена в Telegram."
        else:
            return False, f"Ошибка Telegram API: {resp.text}"
    except Exception as e:
        return False, f"Ошибка отправки: {e}"
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)

if __name__ == "__main__":
    success, msg = run_backup()
    print(f"Success: {success}, Msg: {msg}")
