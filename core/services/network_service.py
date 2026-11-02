from __future__ import annotations
import re
import os
import logging
from typing import Optional, Tuple
from core.system.executor import SystemExecutor

logger = logging.getLogger("transferbox.network")


class NetworkService:
    """
    Manages firewall (UFW), SSH port switching with strict safety & rollback,
    and BBR TCP congestion control as mandated by GEMINI.md.
    """

    def __init__(self, executor: SystemExecutor, ssh_config_path: str = "/etc/ssh/sshd_config"):
        self.executor = executor
        self.ssh_config_path = ssh_config_path

    # ─── BBR MANAGEMENT ──────────────────────────────────────────────────────

    def is_bbr_enabled(self) -> bool:
        res = self.executor.run("sysctl net.ipv4.tcp_congestion_control", timeout=5)
        return "bbr" in res.stdout.lower()

    def enable_bbr(self) -> bool:
        res1 = self.executor.run("sysctl -w net.core.default_qdisc=fq", timeout=5)
        res2 = self.executor.run("sysctl -w net.ipv4.tcp_congestion_control=bbr", timeout=5)
        return res1.success and res2.success

    # ─── FIREWALL (UFW) ──────────────────────────────────────────────────────

    def ufw_allow_port(self, port: int, proto: str = "tcp") -> bool:
        res = self.executor.run(["ufw", "allow", f"{port}/{proto}"])
        return res.success

    def ufw_delete_port(self, port: int, proto: str = "tcp") -> bool:
        res = self.executor.run(["ufw", "delete", "allow", f"{port}/{proto}"])
        return res.success

    # ─── SSH PORT SWITCHING WITH STRICT SAFETY & ROLLBACK ───────────────────

    def change_ssh_port(self, new_port: int, current_port: int = 22) -> Tuple[bool, str]:
        """
        Switches SSH port with atomic verification and automatic rollback.
        Follows GEMINI.md protocol strictly:
        1. ufw allow <NEW_PORT>/tcp
        2. update sshd_config
        3. restart ssh/sshd
        4. verify listening via ss -tlnp
        5. if failed: rollback to current_port
        6. only remove old ufw rule if current_port != 22
        """
        if new_port == current_port:
            return True, "Порт совпадает с текущим."

        if not (1 <= new_port <= 65535):
            return False, f"Некорректный номер порта: {new_port}"

        # Step 1: Open new port in UFW
        if not self.ufw_allow_port(new_port):
            return False, f"Не удалось открыть порт {new_port} в UFW"

        # Read and backup existing sshd_config
        original_content = None
        if os.path.exists(self.ssh_config_path):
            try:
                with open(self.ssh_config_path, "r", encoding="utf-8") as f:
                    original_content = f.read()
            except Exception as e:
                return False, f"Не удалось прочитать {self.ssh_config_path}: {e}"

        def write_ssh_port(port: int):
            if original_content is None:
                return
            new_text = re.sub(r"^\s*#?\s*Port\s+\d+", f"Port {port}", original_content, flags=re.MULTILINE)
            if f"Port {port}" not in new_text:
                new_text = f"Port {port}\n" + new_text
            with open(self.ssh_config_path, "w", encoding="utf-8") as f:
                f.write(new_text)

        # Step 2: Update config
        try:
            write_ssh_port(new_port)
        except Exception as e:
            return False, f"Ошибка записи {self.ssh_config_path}: {e}"

        # Step 3: Restart SSH
        restart_res = self.executor.systemctl("restart", "ssh")
        if not restart_res.success:
            restart_res = self.executor.systemctl("restart", "sshd")

        # Step 4: Verify SSH is listening on new_port
        is_listening = self.executor.is_port_listening(new_port)

        # Step 5: Rollback if verification failed
        if not is_listening or not restart_res.success:
            logger.error(f"SSH failed to listen on port {new_port}, rolling back to {current_port}")
            try:
                write_ssh_port(current_port)
                self.executor.systemctl("restart", "ssh")
            except Exception:
                pass
            self.ufw_delete_port(new_port)
            return False, f"SSH не начал слушать порт {new_port}. Выполнен откат на порт {current_port}."

        # Step 6: Cleanup old UFW rule only if old port is not 22
        if current_port != 22:
            self.ufw_delete_port(current_port)

        return True, f"SSH порт успешно изменен на {new_port}"
