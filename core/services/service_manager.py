from __future__ import annotations
import logging
from typing import Dict, List, Optional
from core.models.service import ServiceInfo, ServiceStatus
from core.system.executor import SystemExecutor

logger = logging.getLogger("transferbox.services")

CORE_SERVICES = [
    ("caddy", "Caddy (HTTPS/Reverse Proxy)", "/etc/caddy/Caddyfile"),
    ("sing-box", "Sing-Box Core", "/etc/sing-box/config.json"),
    ("mita", "Mieru (mita)", "/etc/mieru/config.json"),
    ("transferbox-bot", "Telegram Bot", None),
]


class ServiceManager:
    """
    Manages background services (Caddy, sing-box, Mieru, Telegram Bot)
    with strict safety checks required by GEMINI.md.
    """

    def __init__(self, executor: SystemExecutor, caddy_config_path: str = "/etc/caddy/Caddyfile"):
        self.executor = executor
        self.caddy_config_path = caddy_config_path

    def get_service_status(self, service_name: str) -> ServiceStatus:
        if self.executor.is_service_active(service_name):
            return ServiceStatus.ACTIVE
        res = self.executor.run(["systemctl", "is-failed", "--quiet", service_name])
        if res.success:
            return ServiceStatus.FAILED
        return ServiceStatus.INACTIVE

    def get_all_services(self) -> List[ServiceInfo]:
        services = []
        for name, display_name, _ in CORE_SERVICES:
            status = self.get_service_status(name)
            services.append(ServiceInfo(
                name=name,
                display_name=display_name,
                status=status,
                is_enabled=True,
            ))
        return services

    def validate_caddy(self) -> bool:
        """Validates Caddyfile before applying any reload."""
        res = self.executor.run(["caddy", "validate", "--config", self.caddy_config_path])
        if not res.success:
            logger.error(f"Caddy validation failed: {res.stderr}")
            return False
        return True

    def reload_caddy(self) -> bool:
        """
        Gracefully reloads Caddy with syntax validation and reset-failed handling
        as strictly defined in GEMINI.md.
        """
        if not self.validate_caddy():
            return False

        if self.executor.is_service_active("caddy"):
            res = self.executor.systemctl("reload", "caddy")
            return res.success

        # If Caddy was stopped or in failed state (e.g. start-limit-hit)
        self.executor.systemctl("reset-failed", "caddy")
        res = self.executor.systemctl("start", "caddy")
        return res.success

    def restart_singbox(self) -> bool:
        """Restarts sing-box service."""
        self.executor.systemctl("reset-failed", "sing-box")
        res = self.executor.systemctl("restart", "sing-box")
        return res.success

    def restart_mieru(self) -> bool:
        """Restarts Mieru (mita) service."""
        self.executor.systemctl("reset-failed", "mita")
        res = self.executor.systemctl("restart", "mita")
        return res.success

    def control_bot(self, action: str) -> bool:
        """Controls Telegram bot daemon (start, stop, restart)."""
        if action in ("start", "restart"):
            self.executor.systemctl("reset-failed", "transferbox-bot")
        res = self.executor.systemctl(action, "transferbox-bot")
        return res.success
