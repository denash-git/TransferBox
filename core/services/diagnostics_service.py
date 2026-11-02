from __future__ import annotations
import json
import time
import shutil
from typing import Dict, Any, Optional, Tuple
from core.system.executor import SystemExecutor


class DiagnosticsService:
    """
    Diagnostics, resource monitoring, Speedtest, ephemeral iperf3 test runner,
    and service journal logs as mandated by GEMINI.md.
    """

    def __init__(self, executor: SystemExecutor):
        self.executor = executor

    def get_system_metrics(self) -> Dict[str, Any]:
        """Collects CPU, RAM, Disk and Uptime metrics."""
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            uptime_sec = time.time() - psutil.boot_time()
        except ImportError:
            cpu = 0.0
            mem = None
            disk = None
            uptime_sec = 0

        uptime_days = int(uptime_sec // 86400)
        uptime_hours = int((uptime_sec % 86400) // 3600)
        uptime_mins = int((uptime_sec % 3600) // 60)
        uptime_str = f"{uptime_days}d {uptime_hours}h {uptime_mins}m"

        return {
            "cpu_percent": cpu,
            "ram_used_mb": round(mem.used / 1024 / 1024) if mem else 0,
            "ram_total_mb": round(mem.total / 1024 / 1024) if mem else 0,
            "ram_percent": mem.percent if mem else 0,
            "disk_used_gb": round(disk.used / 1024 / 1024 / 1024, 1) if disk else 0,
            "disk_total_gb": round(disk.total / 1024 / 1024 / 1024, 1) if disk else 0,
            "disk_percent": disk.percent if disk else 0,
            "uptime_str": uptime_str,
        }

    def run_speedtest(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Executes Ookla Speedtest with clean output formatting
        grouped into sections as required by GEMINI.md.
        """
        res = self.executor.run("speedtest --format=json", timeout=60)
        if not res.success:
            res = self.executor.run("speedtest-cli --json", timeout=60)
            if not res.success:
                return False, {"error": "Утилита Speedtest не установлена или недоступна."}

        try:
            data = json.loads(res.stdout)
            server = data.get("server", {})
            ping = data.get("ping", {})
            download = data.get("download", {})
            upload = data.get("upload", {})

            # Ookla speedtest returns bandwidth in bytes/s, convert to Mbps (* 8 / 1e6)
            down_mbps = round((download.get("bandwidth", 0) * 8) / 1_000_000, 2)
            if down_mbps == 0 and "download" in data:
                # speedtest-cli returns bps directly
                down_mbps = round(data["download"] / 1_000_000, 2)

            up_mbps = round((upload.get("bandwidth", 0) * 8) / 1_000_000, 2)
            if up_mbps == 0 and "upload" in data:
                up_mbps = round(data["upload"] / 1_000_000, 2)

            latency = ping.get("latency", data.get("ping", 0))
            jitter = ping.get("jitter", 0)
            packet_loss = data.get("packetLoss", 0)

            result = {
                "server_name": server.get("name", "Auto"),
                "server_country": server.get("country", ""),
                "provider": data.get("isp", server.get("sponsor", "Unknown")),
                "latency_ms": round(latency, 1),
                "jitter_ms": round(jitter, 1),
                "download_mbps": down_mbps,
                "upload_mbps": up_mbps,
                "packet_loss_percent": round(packet_loss, 1) if packet_loss is not None else 0.0,
            }
            return True, result
        except Exception as e:
            return False, {"error": f"Ошибка парсинга Speedtest: {e}"}

    def run_ephemeral_iperf3(self, timeout_sec: int = 180) -> Tuple[bool, str]:
        """
        Runs one-off ephemeral iperf3 test server strictly adhering to GEMINI.md:
        1. Opens UFW port 5201.
        2. Launches iperf3 -s -1 with auto-kill timeout.
        3. Upon completion, immediately kills process and closes UFW port 5201.
        """
        # Step 1: Open UFW
        self.executor.run(["ufw", "allow", "5201/tcp"])

        # Step 2: Run iperf3 -s -1 in background
        cmd = f"timeout {timeout_sec} iperf3 -s -1 >/tmp/iperf3.log 2>&1; ufw delete allow 5201/tcp"
        res = self.executor.run(cmd, timeout=timeout_sec + 5)

        # Step 3: Always ensure UFW rule is removed
        self.executor.run(["ufw", "delete", "allow", "5201/tcp"])
        return res.success, "Тест iperf3 завершен. Порт 5201 закрыт в UFW."

    def get_service_logs(self, service_name: str, lines_count: int = 40) -> str:
        """Retrieves clean recent journalctl logs for a service."""
        cmd = f"journalctl -u {service_name} -n {lines_count} --no-pager"
        res = self.executor.run(cmd, timeout=10)
        return res.stdout if res.success else f"Не удалось прочитать логи: {res.stderr}"
