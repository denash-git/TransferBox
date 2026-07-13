import os
import shutil
import tempfile
import urllib.request
import tarfile
import subprocess
import sys
import time

def main():
    # 1. Получаем последнюю версию из transferbox
    try:
        url = "https://raw.githubusercontent.com/denash-git/TransferBox/main/transferbox"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        latest = None
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8')
            for line in content.split("\n"):
                if line.startswith("VERSION="):
                    latest = line.split('"')[1]
                    break
        if not latest:
            print("Error: latest version not found in raw file")
            sys.exit(1)
    except Exception as e:
        print(f"Error fetching version: {e}")
        sys.exit(1)

    # 2. Скачиваем архив версии
    tar_url = f"https://github.com/denash-git/TransferBox/archive/refs/tags/v{latest}.tar.gz"
    tmp_dir = tempfile.mkdtemp()
    tar_path = os.path.join(tmp_dir, "tb.tar.gz")
    try:
        urllib.request.urlretrieve(tar_url, tar_path)
    except Exception as e:
        print(f"Warning: Tarball for v{latest} download failed ({e}). Trying to fallback to main branch...")
        fallback_url = "https://github.com/denash-git/TransferBox/archive/refs/heads/main.tar.gz"
        try:
            urllib.request.urlretrieve(fallback_url, tar_path)
        except Exception as fe:
            print(f"Error downloading fallback archive: {fe}")
            sys.exit(1)

    # 3. Распаковываем
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            safe = [m for m in tar.getmembers()
                    if not m.name.startswith('/') and '..' not in m.name]
            tar.extractall(path=tmp_dir, members=safe)
        extracted_folder = None
        for name in os.listdir(tmp_dir):
            if (name.startswith("TransferBox-") or name == "TransferBox") and os.path.isdir(os.path.join(tmp_dir, name)):
                extracted_folder = os.path.join(tmp_dir, name)
                break
        if not extracted_folder:
            print("Error: extracted folder not found")
            sys.exit(1)
    except Exception as e:
        print(f"Error extracting: {e}")
        sys.exit(1)

    # 4. Копируем файлы
    project_root = "/opt/transferbox"
    
    # Резервная копия на всякий случай
    shutil.copy(os.path.join(project_root, "users.json"), os.path.join(project_root, "users.json.bak"))
    shutil.copy(os.path.join(project_root, "instance.env"), os.path.join(project_root, "instance.env.bak"))
    shutil.copy(os.path.join(project_root, "transferbox"), os.path.join(project_root, "transferbox.bak"))
    
    # Копируем папки
    for folder in ["core", "templates", "lib", "bot"]:
        src = os.path.join(extracted_folder, folder)
        dst = os.path.join(project_root, folder)
        if os.path.exists(src):
            if os.path.exists(dst):
                # Сохраняем логи/бэкапы если они были внутри папок
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            
    # Копируем скрипт transferbox
    src_tb = os.path.join(extracted_folder, "transferbox")
    dst_tb = os.path.join(project_root, "transferbox")
    shutil.copy(src_tb, dst_tb)
    shutil.copy(src_tb, "/usr/local/bin/menu")
    os.chmod(dst_tb, 0o755)
    os.chmod("/usr/local/bin/menu", 0o755)

    # 5. Запуск миграций и рендер конфигураций
    try:
        subprocess.run([
            sys.executable, "-c",
            "from core.config_manager import run_migrations, render_configs, validate_and_restart; "
            "run_migrations(); render_configs(); validate_and_restart()"
        ], check=True)
    except Exception as e:
        print(f"Migration/Restart failed: {e}")
        # Восстановление
        shutil.copy(os.path.join(project_root, "users.json.bak"), os.path.join(project_root, "users.json"))
        shutil.copy(os.path.join(project_root, "instance.env.bak"), os.path.join(project_root, "instance.env"))
        shutil.copy(os.path.join(project_root, "transferbox.bak"), os.path.join(project_root, "transferbox"))
        shutil.copy(os.path.join(project_root, "transferbox.bak"), "/usr/local/bin/menu")
        sys.exit(1)

    # Чистим резервные копии
    for bak in ["users.json.bak", "instance.env.bak", "transferbox.bak"]:
        path = os.path.join(project_root, bak)
        if os.path.exists(path):
            os.remove(path)
            
    shutil.rmtree(tmp_dir, ignore_errors=True)

    # 6. Перезапускаем бота
    subprocess.run(["systemctl", "restart", "transferbox-bot"])

if __name__ == "__main__":
    time.sleep(2)  # Даем время вызывающему процессу ответить в Telegram
    main()
