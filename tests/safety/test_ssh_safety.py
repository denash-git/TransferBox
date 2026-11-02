import pytest
from core.system.executor import MockSystemExecutor
from core.services.network_service import NetworkService


def test_ssh_port_change_success(tmp_path):
    mock_exec = MockSystemExecutor()
    mock_sshd = tmp_path / "sshd_config"
    mock_sshd.write_text("Port 22\nPermitRootLogin yes\n", encoding="utf-8")

    service = NetworkService(mock_exec, ssh_config_path=str(mock_sshd))

    # Configure mock so port 2222 will be reported listening
    mock_exec.listening_ports.add(2222)

    ok, msg = service.change_ssh_port(new_port=2222, current_port=22)
    assert ok is True

    # 1. UFW opened 2222
    assert "ufw allow 2222/tcp" in mock_exec.history
    # 2. ssh restarted
    assert "systemctl restart ssh" in mock_exec.history
    # 3. Old port 22 rule NOT deleted (standard rule for port 22)
    assert "ufw delete allow 22/tcp" not in mock_exec.history
    # 4. Config updated
    assert "Port 2222" in mock_sshd.read_text(encoding="utf-8")


def test_ssh_port_change_fails_and_rolls_back(tmp_path):
    mock_exec = MockSystemExecutor()
    mock_sshd = tmp_path / "sshd_config"
    mock_sshd.write_text("Port 22\nPermitRootLogin yes\n", encoding="utf-8")

    service = NetworkService(mock_exec, ssh_config_path=str(mock_sshd))

    # Port 3333 is NOT in listening_ports (simulating ss -tlnp failure)
    ok, msg = service.change_ssh_port(new_port=3333, current_port=22)
    assert ok is False
    assert "Выполнен откат" in msg

    # Verification of rollback:
    # 1. Config was rolled back to Port 22
    assert "Port 22" in mock_sshd.read_text(encoding="utf-8")
    # 2. Failed port rule was deleted from UFW
    assert "ufw delete allow 3333/tcp" in mock_exec.history
