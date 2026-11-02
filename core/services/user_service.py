from __future__ import annotations
import json
import os
import secrets
import urllib.parse
from typing import List, Optional, Dict, Any

from core.models.user import User, ProtocolType
from core.models.config import AppConfig


class UserService:
    """Service for managing VPN/proxy users, configurations and subscription links."""

    def __init__(self, db_path: str = "/opt/transferbox/users.json", on_change_callback=None):
        self.db_path = db_path
        self._users_cache: Optional[List[User]] = None
        self.on_change_callback = on_change_callback

    def load_users(self, force_reload: bool = False) -> List[User]:
        if self._users_cache is not None and not force_reload:
            return self._users_cache

        if not os.path.exists(self.db_path):
            self._users_cache = []
            return []

        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                raw_list = json.load(f)
            users = [User.from_dict(item) for item in raw_list]
            self._users_cache = users
            return users
        except Exception:
            self._users_cache = []
            return []

    def save_users(self, users: List[User]) -> bool:
        self._users_cache = users
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
            mode = 0o600
            try:
                fd = os.open(self.db_path, flags, mode)
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump([u.to_dict() for u in users], f, indent=2, ensure_ascii=False)
                os.chmod(self.db_path, 0o600)
            except Exception:
                with open(self.db_path, "w", encoding="utf-8") as f:
                    json.dump([u.to_dict() for u in users], f, indent=2, ensure_ascii=False)
            if self.on_change_callback:
                try:
                    self.on_change_callback(users)
                except Exception:
                    pass
            return True
        except Exception:
            return False

    def get_user_by_name(self, nickname: str) -> Optional[User]:
        for user in self.load_users():
            if user.nickname.lower() == nickname.lower():
                return user
        return None

    def add_user(
        self,
        nickname: str,
        protocol: ProtocolType,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> User:
        users = self.load_users()
        if self.get_user_by_name(nickname):
            raise ValueError(f"Пользователь с именем '{nickname}' уже существует.")

        if credentials is None:
            credentials = {}

        if protocol == ProtocolType.VLESS:
            if "uuid" not in credentials:
                credentials["uuid"] = secrets.token_hex(16)
            if "type" not in credentials:
                credentials["type"] = "ws"
        elif protocol in (ProtocolType.NAIVE, ProtocolType.MIERU):
            if "username" not in credentials:
                credentials["username"] = nickname
            if "password" not in credentials:
                credentials["password"] = secrets.token_urlsafe(12)

        new_user = User(
            nickname=nickname,
            protocol=protocol,
            credentials=credentials,
            enabled=True,
            sub_token=secrets.token_hex(8),
        )
        users.append(new_user)
        self.save_users(users)
        return new_user

    def delete_user(self, nickname: str) -> bool:
        users = self.load_users()
        filtered = [u for u in users if u.nickname.lower() != nickname.lower()]
        if len(filtered) == len(users):
            return False
        return self.save_users(filtered)

    def toggle_user(self, nickname: str) -> bool:
        users = self.load_users()
        for u in users:
            if u.nickname.lower() == nickname.lower():
                u.enabled = not u.enabled
                self.save_users(users)
                return True
        return False

    @staticmethod
    def build_client_link(user: User, config: AppConfig) -> str:
        domain = config.domain
        creds = user.credentials

        if user.protocol == ProtocolType.NAIVE:
            username = creds.get("username", user.nickname)
            password = creds.get("password", "")
            return f"naive://{username}:{password}@{domain}:443#{user.nickname}-naive"

        elif user.protocol == ProtocolType.VLESS:
            user_uuid = creds.get("uuid", "")
            user_type = creds.get("type", "ws")
            if user_type == "ws":
                path = config.vless_ws_path
                return f"vless://{user_uuid}@{domain}:443?encryption=none&security=tls&sni={domain}&type=ws&path={path}#{user.nickname}-ws"
            elif user_type == "grpc":
                service = config.vless_grpc_service
                return f"vless://{user_uuid}@{domain}:443?encryption=none&security=tls&sni={domain}&type=grpc&serviceName={service}#{user.nickname}-grpc"
            elif user_type == "xhttp":
                path = config.vless_xhttp_path
                return f"vless://{user_uuid}@{domain}:443?encryption=none&security=tls&sni={domain}&type=httpupgrade&path={path}#{user.nickname}-xhttp"

        elif user.protocol == ProtocolType.MIERU:
            username = creds.get("username", user.nickname)
            password = creds.get("password", "")
            port = config.mieru_port
            safe_user = urllib.parse.quote(username)
            safe_pass = urllib.parse.quote(password)
            safe_profile = urllib.parse.quote(f"{user.nickname}-mieru")
            return f"mierus://{safe_user}:{safe_pass}@{domain}?profile={safe_profile}&port={port}&protocol=TCP&multiplexing=MULTIPLEXING_HIGH#{user.nickname}-mieru"

        return ""

    @staticmethod
    def build_mieru_json_config(user: User, config: AppConfig) -> str:
        creds = user.credentials
        cfg = {
            "profileName": f"{user.nickname}-mieru",
            "user": {
                "name": creds.get("username", user.nickname),
                "password": creds.get("password", ""),
            },
            "servers": [
                {
                    "ipAddress": config.domain,
                    "portBindings": [
                        {
                            "port": config.mieru_port,
                            "protocol": "TCP",
                        }
                    ],
                }
            ],
            "mtu": 1400,
            "multiplexing": {
                "level": "MULTIPLEXING_HIGH",
            },
        }
        return json.dumps(cfg, indent=2, ensure_ascii=False)
