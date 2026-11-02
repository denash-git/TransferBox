from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class AppConfig:
    domain: str = "yourdomain.com"
    server_ip: str = "127.0.0.1"
    ssh_port: int = 22
    bbr_enabled: bool = False
    
    # Telegram Bot
    tg_bot_token: Optional[str] = None
    tg_chat_id: Optional[str] = None
    
    # Protocols
    vless_ws_path: str = "/"
    vless_grpc_service: str = ""
    vless_xhttp_path: str = "/xhttp"
    mieru_port: int = 21000
    
    # Backups
    backup_enabled: bool = False
    backup_hour: int = 12
    backup_minute: int = 0
    backup_password: str = ""
    
    # Schema version
    schema_version: int = 4
    
    # Raw env dict for unknown or extra vars
    extra: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_env_dict(cls, env: Dict[str, str]) -> AppConfig:
        def parse_bool(v: str) -> bool:
            return str(v).strip().lower() in ("true", "1", "yes", "on")

        def parse_int(v: Any, default: int) -> int:
            try:
                return int(v)
            except (ValueError, TypeError):
                return default

        return cls(
            domain=env.get("DOMAIN", "yourdomain.com"),
            server_ip=env.get("SERVER_IP", "127.0.0.1"),
            ssh_port=parse_int(env.get("SSH_PORT"), 22),
            bbr_enabled=parse_bool(env.get("BBR_ENABLED", "false")),
            tg_bot_token=env.get("TG_BOT_TOKEN") or None,
            tg_chat_id=env.get("TG_CHAT_ID") or None,
            vless_ws_path=env.get("VLESS_WS_PATH", "/"),
            vless_grpc_service=env.get("VLESS_GRPC_SERVICE", ""),
            vless_xhttp_path=env.get("VLESS_XHTTP_PATH", "/xhttp"),
            mieru_port=parse_int(env.get("MIERU_PORT"), 21000),
            backup_enabled=parse_bool(env.get("BACKUP_ENABLED", "false")),
            backup_hour=parse_int(env.get("BACKUP_HOUR"), 12),
            backup_minute=parse_int(env.get("BACKUP_MINUTE"), 0),
            backup_password=env.get("BACKUP_PASSWORD", ""),
            schema_version=parse_int(env.get("SCHEMA_VERSION"), 4),
            extra={k: v for k, v in env.items() if k not in {
                "DOMAIN", "SERVER_IP", "SSH_PORT", "BBR_ENABLED", "TG_BOT_TOKEN",
                "TG_CHAT_ID", "VLESS_WS_PATH", "VLESS_GRPC_SERVICE", "VLESS_XHTTP_PATH",
                "MIERU_PORT", "BACKUP_ENABLED", "BACKUP_HOUR", "BACKUP_MINUTE",
                "BACKUP_PASSWORD", "SCHEMA_VERSION"
            }},
        )

    def to_env_dict(self) -> Dict[str, str]:
        res = {
            "DOMAIN": self.domain,
            "SERVER_IP": self.server_ip,
            "SSH_PORT": str(self.ssh_port),
            "BBR_ENABLED": "true" if self.bbr_enabled else "false",
            "VLESS_WS_PATH": self.vless_ws_path,
            "VLESS_GRPC_SERVICE": self.vless_grpc_service,
            "VLESS_XHTTP_PATH": self.vless_xhttp_path,
            "MIERU_PORT": str(self.mieru_port),
            "BACKUP_ENABLED": "true" if self.backup_enabled else "false",
            "BACKUP_HOUR": str(self.backup_hour),
            "BACKUP_MINUTE": str(self.backup_minute),
            "BACKUP_PASSWORD": self.backup_password,
            "SCHEMA_VERSION": str(self.schema_version),
        }
        if self.tg_bot_token:
            res["TG_BOT_TOKEN"] = self.tg_bot_token
        if self.tg_chat_id:
            res["TG_CHAT_ID"] = self.tg_chat_id
        res.update(self.extra)
        return res
