import pytest
import os
import json
import base64
from core.models.config import AppConfig
from core.models.user import User, ProtocolType
from core.services.config_render_service import ConfigRenderService


def test_config_render_service(tmp_path):
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    fakesite_dir = templates_dir / "fakesite" / "aether"
    fakesite_dir.mkdir(parents=True)

    # Caddy template
    caddy_tmpl = templates_dir / "Caddyfile.template"
    caddy_tmpl.write_text("{{DOMAIN}} {\n  {{FORWARD_PROXY_BLOCK}}\n}\n", encoding="utf-8")

    # Singbox template
    sb_tmpl = templates_dir / "sing-box-base.json.template"
    sb_tmpl.write_text('{\n  "inbounds": [\n    // {{VLESS_WS_USERS}}\n  ]\n}', encoding="utf-8")

    caddy_dest = str(tmp_path / "Caddyfile")
    sb_dest = str(tmp_path / "sing-box.json")
    mieru_dest = str(tmp_path / "mieru.json")

    service = ConfigRenderService(
        project_root=str(tmp_path),
        templates_dir=str(templates_dir),
        caddy_dest=caddy_dest,
        singbox_dest=sb_dest,
        mieru_dest=mieru_dest,
    )

    config = AppConfig(domain="vpn.mytest.org")
    users = [
        User(nickname="alice", protocol=ProtocolType.VLESS, credentials={"uuid": "uuid-111", "type": "ws"}, sub_token="tok123"),
        User(nickname="bob", protocol=ProtocolType.NAIVE, credentials={"username": "bob_user", "password": "bob_pwd"}),
    ]

    ok, msg = service.render_all(config, users)
    assert ok is True

    # 1. Caddyfile verification
    with open(caddy_dest, "r", encoding="utf-8") as f:
        caddy_content = f.read()
    assert "vpn.mytest.org" in caddy_content
    assert "basic_auth bob_user bob_pwd" in caddy_content

    # 2. Sing-box verification
    with open(sb_dest, "r", encoding="utf-8") as f:
        sb_content = f.read()
    assert "uuid-111" in sb_content

    # 3. Subscription verification
    sub_file = tmp_path / "sub" / "tok123"
    assert sub_file.exists()
    decoded = base64.b64decode(sub_file.read_text(encoding="utf-8")).decode("utf-8")
    assert "vless://uuid-111@vpn.mytest.org" in decoded
