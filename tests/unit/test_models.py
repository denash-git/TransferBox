import pytest
from core.models.user import User, ProtocolType
from core.models.config import AppConfig
from core.models.service import ServiceStatus


def test_user_creation_and_serialization():
    user = User(
        nickname="test_user",
        protocol=ProtocolType.VLESS,
        credentials={"uuid": "12345678-1234-1234-1234-123456789abc", "type": "ws"},
    )
    assert user.nickname == "test_user"
    assert user.protocol == ProtocolType.VLESS
    assert user.enabled is True
    assert len(user.sub_token) == 16  # token_hex(8) -> 16 chars

    data = user.to_dict()
    assert data["nickname"] == "test_user"
    assert data["protocol"] == "vless"
    assert data["enabled"] is True

    # Deserialize back
    restored = User.from_dict(data)
    assert restored.nickname == user.nickname
    assert restored.protocol == user.protocol
    assert restored.sub_token == user.sub_token


def test_app_config_env_roundtrip():
    env = {
        "DOMAIN": "sub.example.com",
        "SERVER_IP": "1.2.3.4",
        "SSH_PORT": "2222",
        "BBR_ENABLED": "true",
        "BACKUP_ENABLED": "false",
        "CUSTOM_KEY": "custom_val",
    }
    cfg = AppConfig.from_env_dict(env)
    assert cfg.domain == "sub.example.com"
    assert cfg.ssh_port == 2222
    assert cfg.bbr_enabled is True
    assert cfg.backup_enabled is False
    assert cfg.extra["CUSTOM_KEY"] == "custom_val"

    exported = cfg.to_env_dict()
    assert exported["DOMAIN"] == "sub.example.com"
    assert exported["SSH_PORT"] == "2222"
    assert exported["BBR_ENABLED"] == "true"
    assert exported["CUSTOM_KEY"] == "custom_val"


def test_service_status_indicators():
    active = ServiceStatus.ACTIVE
    assert active.is_healthy is True
    assert active.dot_symbol == "●"
    assert active.display_label == "активен"

    failed = ServiceStatus.FAILED
    assert failed.is_healthy is False
    assert failed.display_label == "ошибка"
