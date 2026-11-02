#!/usr/bin/env python3
"""
TransferBox v4.0.0 — Modern Modular Python TUI Application.
"""
import os
import sys
import logging

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.models.config import AppConfig
from core.system.executor import LinuxSystemExecutor, MockSystemExecutor
from core.services.user_service import UserService
from core.services.service_manager import ServiceManager
from core.services.network_service import NetworkService
from core.services.backup_service import BackupService
from tui.screens.main_screen import MainScreen

# Setup application logging
log_dir = "/var/log/transferbox"
os.makedirs(log_dir, exist_ok=True) if os.path.exists("/var/log") else None
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main():
    # Detect environment
    is_linux = sys.platform.startswith("linux")
    executor = LinuxSystemExecutor() if is_linux else MockSystemExecutor()

    # Load configuration
    env_file = os.path.join(PROJECT_ROOT, "instance.env")
    env_dict = {}
    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        env_dict[k.strip()] = v.strip()
        except Exception:
            pass

    config = AppConfig.from_env_dict(env_dict)

    # Initialize services
    users_db = os.path.join(PROJECT_ROOT, "users.json")
    user_service = UserService(db_path=users_db)
    service_mgr = ServiceManager(executor=executor)
    network_service = NetworkService(executor=executor)
    backup_service = BackupService(executor=executor, backup_dir=os.path.join(PROJECT_ROOT, "backups"))

    # Launch TUI
    screen = MainScreen(
        config=config,
        user_service=user_service,
        service_mgr=service_mgr,
        network_service=network_service,
        backup_service=backup_service,
    )
    screen.run()


if __name__ == "__main__":
    main()
