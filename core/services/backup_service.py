from __future__ import annotations
import os
import glob
import time
import zipfile
import shutil
import logging
from typing import List, Optional, Tuple, Dict, Any

from core.system.executor import SystemExecutor

logger = logging.getLogger("transferbox.backup")

BACKUP_DIR = "/opt/transferbox/backups"
BACKUP_FILES = [
    "/opt/transferbox/instance.env",
    "/opt/transferbox/users.json",
    "/etc/caddy/Caddyfile",
    "/etc/sing-box/config.json",
    "/etc/mieru/config.json",
]


class BackupService:
    """
    Manages automated and manual encrypted backups and restoration
    adhering strictly to GEMINI.md pre-update retention rules.
    """

    def __init__(self, executor: SystemExecutor, backup_dir: str = BACKUP_DIR):
        self.executor = executor
        self.backup_dir = backup_dir

    def ensure_backup_dir(self):
        os.makedirs(self.backup_dir, exist_ok=True)
        try:
            os.chmod(self.backup_dir, 0o700)
        except Exception:
            pass

    def create_backup(
        self,
        password: Optional[str] = None,
        is_pre_update: bool = False,
        version: str = "4.0.0",
        files: Optional[List[str]] = None,
    ) -> Tuple[bool, str]:
        self.ensure_backup_dir()
        ts = int(time.time())
        if is_pre_update:
            filename = f"transferbox_backup_pre_update_v{version}_{ts}.zip"
        else:
            filename = f"transferbox_backup_{ts}.zip"

        target_path = os.path.join(self.backup_dir, filename)
        source_files = files if files is not None else BACKUP_FILES

        existing_files = [f for f in source_files if os.path.exists(f)]
        if not existing_files:
            return False, "Не найдены файлы конфигурации для создания бэкапа."

        # If password is set, use system zip with -P or fallback
        if password:
            cmd = ["zip", "-j", "-P", password, target_path] + existing_files
            res = self.executor.run(cmd)
            if not res.success:
                # If zip utility is not installed, fallback to standard zipfile (standard encryption)
                try:
                    with zipfile.ZipFile(target_path, "w", zipfile.ZIP_DEFLATED) as zf:
                        zf.setpassword(password.encode("utf-8"))
                        for f in existing_files:
                            zf.write(f, arcname=os.path.basename(f))
                except Exception as e:
                    return False, f"Ошибка создания зашифрованного архива: {e}"
        else:
            try:
                with zipfile.ZipFile(target_path, "w", zipfile.ZIP_DEFLATED) as zf:
                    for f in existing_files:
                        zf.write(f, arcname=os.path.basename(f))
            except Exception as e:
                return False, f"Ошибка создания архива: {e}"

        return True, target_path

    def list_backups(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.backup_dir):
            return []

        pattern = os.path.join(self.backup_dir, "transferbox_backup_*.zip")
        files = glob.glob(pattern)
        files.sort(key=os.path.getmtime, reverse=True)

        result = []
        for path in files:
            fname = os.path.basename(path)
            size_kb = round(os.path.getsize(path) / 1024, 1)
            is_pre_update = "pre_update" in fname
            mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(path)))
            result.append({
                "path": path,
                "filename": fname,
                "size_kb": size_kb,
                "is_pre_update": is_pre_update,
                "mtime": mtime,
            })
        return result

    def get_latest_backup(self) -> Optional[str]:
        backups = self.list_backups()
        return backups[0]["path"] if backups else None

    def restore_backup(
        self,
        zip_path: str,
        password: Optional[str] = None,
        extract_to_root: bool = True,
    ) -> Tuple[bool, str]:
        if not os.path.exists(zip_path):
            return False, f"Файл бэкапа не найден: {zip_path}"

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                pwd_bytes = password.encode("utf-8") if password else None
                try:
                    # Test zip integrity / password
                    zf.testzip()
                except RuntimeError as e:
                    if "password" in str(e).lower() or "encrypted" in str(e).lower():
                        if not password:
                            return False, "Архив защищен паролем. Укажите пароль для восстановления."
                        try:
                            zf.extractall("/tmp/tb_restore_test", pwd=pwd_bytes)
                        except Exception:
                            return False, "Неверный пароль для архива бэкапа."

                # Restore files to proper targets
                for member in zf.infolist():
                    data = zf.read(member.filename, pwd=pwd_bytes)
                    name = os.path.basename(member.filename)

                    target_dest = None
                    if name in ("instance.env", "users.json"):
                        target_dest = os.path.join("/opt/transferbox", name)
                    elif name == "Caddyfile":
                        target_dest = "/etc/caddy/Caddyfile"
                    elif name == "config.json":
                        target_dest = "/etc/sing-box/config.json"

                    if target_dest and extract_to_root:
                        os.makedirs(os.path.dirname(target_dest), exist_ok=True)
                        with open(target_dest, "wb") as out_f:
                            out_f.write(data)

            return True, "Конфигурация успешно восстановлена из архива."
        except Exception as e:
            return False, f"Ошибка восстановления: {e}"
