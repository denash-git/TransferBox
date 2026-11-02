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
from core.services.diagnostics_service import DiagnosticsService
from core.services.config_render_service import ConfigRenderService
from tui.screens.main_screen import MainScreen

# Setup application logging
log_dir = "/var/log/transferbox"
os.makedirs(log_dir, exist_ok=True) if os.path.exists("/var/log") else None
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def save_env_file(config: AppConfig, env_file_path: str):
    """Saves AppConfig dictionary to instance.env."""
    env_dict = config.to_env_dict()
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        mode = 0o600
        try:
            fd = os.open(env_file_path, flags, mode)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write("# TransferBox Instance Config\n")
                for k, v in env_dict.items():
                    f.write(f"{k}={v}\n")
            os.chmod(env_file_path, 0o600)
        except Exception:
            with open(env_file_path, "w", encoding="utf-8") as f:
                f.write("# TransferBox Instance Config\n")
                for k, v in env_dict.items():
                    f.write(f"{k}={v}\n")
    except Exception as e:
        logging.error(f"Failed to save env file: {e}")


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
    render_service = ConfigRenderService(project_root=PROJECT_ROOT)
    service_mgr = ServiceManager(executor=executor)

    def on_users_changed(updated_users):
        render_service.render_all(config, updated_users)
        if is_linux:
            service_mgr.reload_caddy()
            service_mgr.restart_singbox()

    user_service = UserService(db_path=users_db, on_change_callback=on_users_changed)
    network_service = NetworkService(executor=executor)
    backup_service = BackupService(executor=executor, backup_dir=os.path.join(PROJECT_ROOT, "backups"))
    diagnostics_service = DiagnosticsService(executor=executor)

    # Launch TUI
    screen = MainScreen(
        config=config,
        user_service=user_service,
        service_mgr=service_mgr,
        network_service=network_service,
        backup_service=backup_service,
        diagnostics_service=diagnostics_service,
        env_save_callback=lambda cfg: save_env_file(cfg, env_file),
    )
    screen.run()


if __name__ == "__main__":
    main()
