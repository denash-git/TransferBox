import pytest
from core.system.executor import MockSystemExecutor
from core.services.service_manager import ServiceManager
from core.models.service import ServiceStatus


def test_caddy_reload_requires_validation():
    mock_exec = MockSystemExecutor()
    service_mgr = ServiceManager(mock_exec)

    # When Caddy config is valid and Caddy is active
    mock_exec.mock_caddy_valid = True
    mock_exec.services_state["caddy"] = True

    assert service_mgr.reload_caddy() is True
    # Verify reload was called (not restart!)
    assert "systemctl reload caddy" in mock_exec.history
    assert "systemctl restart caddy" not in mock_exec.history


def test_caddy_reload_aborts_if_config_invalid():
    mock_exec = MockSystemExecutor()
    service_mgr = ServiceManager(mock_exec)

    # When config is invalid
    mock_exec.mock_caddy_valid = False
    mock_exec.services_state["caddy"] = True

    assert service_mgr.reload_caddy() is False
    # Must NOT call reload or restart if invalid
    assert "systemctl reload caddy" not in mock_exec.history
    assert "systemctl restart caddy" not in mock_exec.history


def test_caddy_clears_failed_before_start():
    mock_exec = MockSystemExecutor()
    service_mgr = ServiceManager(mock_exec)

    # When Caddy is inactive/failed
    mock_exec.mock_caddy_valid = True
    mock_exec.services_state["caddy"] = False

    assert service_mgr.reload_caddy() is True
    # Must call reset-failed before start
    assert "systemctl reset-failed caddy" in mock_exec.history
    assert "systemctl start caddy" in mock_exec.history
