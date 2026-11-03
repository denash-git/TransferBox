import pytest
from core.models.config import AppConfig
from core.system.executor import MockSystemExecutor
from core.services.user_service import UserService
from core.services.service_manager import ServiceManager
from core.services.network_service import NetworkService
from core.services.backup_service import BackupService
from core.services.diagnostics_service import DiagnosticsService
from core.services.config_render_service import ConfigRenderService
from tui.screens.main_screen import MainScreen


def test_main_screen_initialization(tmp_path):
    mock_exec = MockSystemExecutor()
    config = AppConfig(domain="test.example.com", server_ip="1.2.3.4")
    user_service = UserService(db_path=str(tmp_path / "users.json"))
    service_mgr = ServiceManager(mock_exec)
    network_service = NetworkService(mock_exec)
    backup_service = BackupService(mock_exec, backup_dir=str(tmp_path / "backups"))
    diagnostics_service = DiagnosticsService(mock_exec)
    render_service = ConfigRenderService(project_root=str(tmp_path))

    main_screen = MainScreen(
        config=config,
        user_service=user_service,
        service_mgr=service_mgr,
        network_service=network_service,
        backup_service=backup_service,
        diagnostics_service=diagnostics_service,
        render_service=render_service,
    )

    st = main_screen._get_status_dict()
    assert st["domain"] == "test.example.com"
    assert "caddy" in st
    assert "singbox" in st
    assert "bbr" in st
