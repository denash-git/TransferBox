from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, Any, Optional
import secrets
import time


class ProtocolType(str, Enum):
    VLESS = "vless"
    NAIVE = "naive"
    MIERU = "mieru"


@dataclass
class VlessCredentials:
    uuid: str = field(default_factory=lambda: secrets.token_hex(16))
    type: str = "ws"  # ws, grpc, xhttp
    flow: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> VlessCredentials:
        return cls(
            uuid=data.get("uuid", secrets.token_hex(16)),
            type=data.get("type", "ws"),
            flow=data.get("flow"),
        )


@dataclass
class MieruCredentials:
    username: str = ""
    password: str = ""
    port: int = 21000

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MieruCredentials:
        return cls(
            username=data.get("username", ""),
            password=data.get("password", ""),
            port=int(data.get("port", 21000)),
        )


@dataclass
class NaiveCredentials:
    username: str = ""
    password: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> NaiveCredentials:
        return cls(
            username=data.get("username", ""),
            password=data.get("password", ""),
        )


@dataclass
class User:
    nickname: str
    protocol: ProtocolType
    credentials: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    sub_token: str = field(default_factory=lambda: secrets.token_hex(8))
    created_at: int = field(default_factory=lambda: int(time.time()))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> User:
        raw_proto = data.get("protocol", "vless").lower()
        try:
            proto = ProtocolType(raw_proto)
        except ValueError:
            proto = ProtocolType.VLESS

        return cls(
            nickname=data.get("nickname", "unknown"),
            protocol=proto,
            credentials=data.get("credentials", {}),
            enabled=data.get("enabled", True),
            sub_token=data.get("sub_token") or secrets.token_hex(8),
            created_at=data.get("created_at") or int(time.time()),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nickname": self.nickname,
            "protocol": self.protocol.value,
            "credentials": self.credentials,
            "enabled": self.enabled,
            "sub_token": self.sub_token,
            "created_at": self.created_at,
        }
