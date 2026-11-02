from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union
import subprocess
import logging

logger = logging.getLogger("transferbox.system")


@dataclass
class ExecResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.returncode == 0


class SystemExecutor(ABC):
    """Abstract base class for executing operating system and systemd commands."""

    @abstractmethod
    def run(self, cmd: Union[List[str], str], timeout: int = 30, check: bool = False) -> ExecResult:
        pass

    @abstractmethod
    def is_service_active(self, service_name: str) -> bool:
        pass

    @abstractmethod
    def systemctl(self, action: str, service_name: str) -> ExecResult:
        pass

    @abstractmethod
    def is_port_listening(self, port: int) -> bool:
        pass


class LinuxSystemExecutor(SystemExecutor):
    """Real Linux system executor running actual subprocess commands."""

    def run(self, cmd: Union[List[str], str], timeout: int = 30, check: bool = False) -> ExecResult:
        shell = isinstance(cmd, str)
        try:
            res = subprocess.run(
                cmd,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            result = ExecResult(res.returncode, res.stdout.strip(), res.stderr.strip())
            if check and not result.success:
                logger.error(f"Command failed: {cmd} -> {result.stderr}")
                raise RuntimeError(f"Command failed with code {result.returncode}: {result.stderr}")
            return result
        except subprocess.TimeoutExpired as e:
            logger.error(f"Command timed out after {timeout}s: {cmd}")
            return ExecResult(124, "", f"Timeout after {timeout}s")
        except Exception as e:
            logger.error(f"Execution error on {cmd}: {e}")
            return ExecResult(1, "", str(e))

    def is_service_active(self, service_name: str) -> bool:
        res = self.run(["systemctl", "is-active", "--quiet", service_name])
        return res.success

    def systemctl(self, action: str, service_name: str) -> ExecResult:
        return self.run(["systemctl", action, service_name])

    def is_port_listening(self, port: int) -> bool:
        res = self.run(f"ss -tlnp | grep -E ':{port}\\b'", timeout=5)
        return res.success and len(res.stdout) > 0


class MockSystemExecutor(SystemExecutor):
    """Mock executor for local development on Windows and automated test suites."""

    def __init__(self):
        self.history: List[str] = []
        self.services_state: Dict[str, bool] = {
            "caddy": True,
            "sing-box": True,
            "mita": True,
            "transferbox-bot": True,
            "ssh": True,
            "sshd": True,
        }
        self.listening_ports: set[int] = {22, 80, 443}
        self.mock_caddy_valid: bool = True
        self.mock_command_responses: Dict[str, ExecResult] = {}

    def run(self, cmd: Union[List[str], str], timeout: int = 30, check: bool = False) -> ExecResult:
        cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
        self.history.append(cmd_str)

        # Pre-configured mock responses
        if cmd_str in self.mock_command_responses:
            res = self.mock_command_responses[cmd_str]
            if check and not res.success:
                raise RuntimeError(res.stderr)
            return res

        # Caddy validate mock
        if "caddy validate" in cmd_str:
            if not self.mock_caddy_valid:
                return ExecResult(1, "", "Error: invalid configuration")
            return ExecResult(0, "Valid configuration", "")

        return ExecResult(0, "", "")

    def is_service_active(self, service_name: str) -> bool:
        return self.services_state.get(service_name, False)

    def systemctl(self, action: str, service_name: str) -> ExecResult:
        cmd = f"systemctl {action} {service_name}"
        self.history.append(cmd)
        if action in ("start", "restart", "reload"):
            self.services_state[service_name] = True
        elif action == "stop":
            self.services_state[service_name] = False
        return ExecResult(0, "", "")

    def is_port_listening(self, port: int) -> bool:
        return port in self.listening_ports
