import pytest
from core.models.config import AppConfig
from core.system.executor import MockSystemExecutor
from core.services.user_service import UserService
from core.services.service_manager import ServiceManager
from core.services.network_service import NetworkService
from core.services.backup_service import BackupService
from tui.screens.main_screen import MainScreen


def test_main_screen_initialization(tmp_path):
    mock_exec = MockSystemExecutor()
    config = AppConfig(domain="test.example.com", server_ip="1.2.3.4")
    user_service = UserService(db_path=str(tmp_path / "users.json"))
    service_mgr = ServiceManager(mock_exec)
    network_service = NetworkService(mock_exec)
    backup_service = BackupService(mock_exec, backup_dir=str(tmp_path / "backups"))

    main_screen = MainScreen(
        config=config,
        user_service=user_service,
        service_mgr=service_mgr,
        network_service=network_service,
        backup_service=backup_service,
    )

    lines = main_screen._get_status_lines()
    assert len(lines) == 2
    assert "test.example.com" in lines[0]
    assert "1.2.3.4" in lines[0]
    assert "Caddy:" in lines[1]
    assert "Sing-Box:" in lines[1]
