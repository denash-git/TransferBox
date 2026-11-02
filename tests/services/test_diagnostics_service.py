import pytest
from core.system.executor import MockSystemExecutor, ExecResult
from core.services.diagnostics_service import DiagnosticsService


def test_diagnostics_metrics():
    mock_exec = MockSystemExecutor()
    service = DiagnosticsService(mock_exec)

    metrics = service.get_system_metrics()
    assert "cpu_percent" in metrics
    assert "ram_percent" in metrics
    assert "disk_percent" in metrics
    assert "uptime_str" in metrics


def test_diagnostics_speedtest_parsing():
    mock_exec = MockSystemExecutor()
    service = DiagnosticsService(mock_exec)

    mock_json = """{
        "server": {"name": "Frankfurt Server", "country": "Germany"},
        "isp": "Test ISP",
        "ping": {"latency": 15.4, "jitter": 1.2},
        "download": {"bandwidth": 12500000},
        "upload": {"bandwidth": 6250000},
        "packetLoss": 0.0
    }"""
    mock_exec.mock_command_responses["speedtest --format=json"] = ExecResult(0, mock_json, "")

    ok, res = service.run_speedtest()
    assert ok is True
    assert res["server_name"] == "Frankfurt Server"
    assert res["provider"] == "Test ISP"
    assert res["latency_ms"] == 15.4
    assert res["download_mbps"] == 100.0  # 12.5 MB/s * 8 = 100 Mbps
    assert res["upload_mbps"] == 50.0    # 6.25 MB/s * 8 = 50 Mbps


def test_diagnostics_ephemeral_iperf3():
    mock_exec = MockSystemExecutor()
    service = DiagnosticsService(mock_exec)

    ok, msg = service.run_ephemeral_iperf3(timeout_sec=10)
    assert ok is True
    assert "ufw allow 5201/tcp" in mock_exec.history
    assert "ufw delete allow 5201/tcp" in mock_exec.history
