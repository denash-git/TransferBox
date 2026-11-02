import pytest
import os
import json
from core.models.user import ProtocolType
from core.models.config import AppConfig
from core.services.user_service import UserService


def test_user_service_crud(tmp_path):
    db_file = str(tmp_path / "users.json")
    service = UserService(db_path=db_file)

    # 1. Initially empty
    assert len(service.load_users()) == 0

    # 2. Add user
    alice = service.add_user("alice", ProtocolType.VLESS, {"uuid": "1111-2222-3333-4444", "type": "ws"})
    assert alice.nickname == "alice"
    assert alice.protocol == ProtocolType.VLESS
    assert len(service.load_users()) == 1

    # 3. Prevent duplicate
    with pytest.raises(ValueError):
        service.add_user("alice", ProtocolType.NAIVE)

    # 4. Toggle enabled
    service.toggle_user("alice")
    alice_toggled = service.get_user_by_name("alice")
    assert alice_toggled.enabled is False

    # 5. Delete user
    assert service.delete_user("alice") is True
    assert len(service.load_users()) == 0


def test_client_link_generation():
    config = AppConfig(
        domain="vpn.testserver.xyz",
        vless_ws_path="/ws-secret",
        mieru_port=21055,
    )
    service = UserService(db_path="/tmp/dummy.json")

    # VLESS ws link
    vless_user = service.add_user.__wrapped__(service, "bob", ProtocolType.VLESS, {"uuid": "uuid-1234", "type": "ws"}) if hasattr(service.add_user, "__wrapped__") else None
    from core.models.user import User
    vless_user = User("bob", ProtocolType.VLESS, {"uuid": "uuid-1234", "type": "ws"})
    link = service.build_client_link(vless_user, config)
    assert link == "vless://uuid-1234@vpn.testserver.xyz:443?encryption=none&security=tls&sni=vpn.testserver.xyz&type=ws&path=/ws-secret#bob-ws"

    # Naive link
    naive_user = User("carol", ProtocolType.NAIVE, {"username": "carol_u", "password": "carol_pass"})
    link = service.build_client_link(naive_user, config)
    assert link == "naive://carol_u:carol_pass@vpn.testserver.xyz:443#carol-naive"

    # Mieru link
    mieru_user = User("dave", ProtocolType.MIERU, {"username": "dave_u", "password": "dave_pass"})
    link = service.build_client_link(mieru_user, config)
    assert "mierus://dave_u:dave_pass@vpn.testserver.xyz?" in link
    assert "port=21055" in link
