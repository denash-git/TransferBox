from __future__ import annotations
import os
import json
import base64
import shutil
import logging
from typing import List, Tuple, Optional

from core.models.config import AppConfig
from core.models.user import User, ProtocolType
from core.services.user_service import UserService
from core.system.executor import SystemExecutor

logger = logging.getLogger("transferbox.render")

CADDY_CONFIG = "/etc/caddy/Caddyfile"
SINGBOX_CONFIG = "/etc/sing-box/config.json"
MIERU_CONFIG = "/etc/mieru/config.json"


class ConfigRenderService:
    """
    Renders Caddyfile, sing-box JSON, Mieru JSON, and subscription endpoints
    based on AppConfig and User list.
    """

    def __init__(
        self,
        project_root: str = "/opt/transferbox",
        templates_dir: Optional[str] = None,
        caddy_dest: str = CADDY_CONFIG,
        singbox_dest: str = SINGBOX_CONFIG,
        mieru_dest: str = MIERU_CONFIG,
    ):
        self.project_root = project_root
        self.templates_dir = templates_dir or os.path.join(project_root, "templates")
        self.caddy_dest = caddy_dest
        self.singbox_dest = singbox_dest
        self.mieru_dest = mieru_dest

    def render_all(self, config: AppConfig, users: List[User]) -> Tuple[bool, str]:
        try:
            # 1. Render Caddyfile
            self._render_caddyfile(config, users)

            # 2. Render sing-box
            self._render_singbox(config, users)

            # 3. Render Mieru
            self._render_mieru(config, users)

            # 4. Render Subscriptions
            self._render_subscriptions(config, users)

            return True, "Все конфигурации успешно сформированы."
        except Exception as e:
            logger.error(f"Error rendering configs: {e}")
            return False, f"Ошибка рендеринга конфигураций: {e}"

    def _render_caddyfile(self, config: AppConfig, users: List[User]):
        caddy_tmpl_path = os.path.join(self.templates_dir, "Caddyfile.template")
        if not os.path.exists(caddy_tmpl_path):
            return

        with open(caddy_tmpl_path, "r", encoding="utf-8") as f:
            tmpl = f.read()

        # Naive basic_auth
        basic_auth_rules = []
        for u in users:
            if u.protocol == ProtocolType.NAIVE and u.enabled:
                creds = u.credentials
                user = creds.get("username", u.nickname)
                password = creds.get("password")
                if user and password:
                    basic_auth_rules.append(f"basic_auth {user} {password}")

        if basic_auth_rules:
            basic_auth_str = "\n        ".join(basic_auth_rules)
            forward_proxy_block = f"""forward_proxy {{
        {basic_auth_str}
        hide_ip
        hide_via
        probe_resistance
        upstream socks5://127.0.0.1:10001
    }}"""
        else:
            forward_proxy_block = "# No NaiveProxy users configured"

        fakesite_dir = os.path.join(self.templates_dir, "fakesite", "aether")

        content = tmpl.replace("{{DOMAIN}}", config.domain)
        content = content.replace("{{ADMIN_EMAIL}}", "")
        content = content.replace("{{CADDY_TLS_EMAIL}}", "# anonymous ACME")
        content = content.replace("{{FAKESITE_DIR}}", fakesite_dir)
        content = content.replace("{{FORWARD_PROXY_BLOCK}}", forward_proxy_block)
        content = content.replace("{{VLESS_WS_PATH}}", config.vless_ws_path)
        content = content.replace("{{VLESS_GRPC_PATH}}", f"/{config.vless_grpc_service.lstrip('/')}")
        content = content.replace("{{VLESS_XHTTP_PATH}}", config.vless_xhttp_path)
        content = content.replace("{{PROJECT_ROOT}}", self.project_root)

        os.makedirs(os.path.dirname(self.caddy_dest), exist_ok=True)
        with open(self.caddy_dest, "w", encoding="utf-8") as f:
            f.write(content)
        try:
            os.chmod(self.caddy_dest, 0o600)
        except Exception:
            pass

    def _render_singbox(self, config: AppConfig, users: List[User]):
        sb_tmpl_path = os.path.join(self.templates_dir, "sing-box-base.json.template")
        if not os.path.exists(sb_tmpl_path):
            return

        with open(sb_tmpl_path, "r", encoding="utf-8") as f:
            tmpl = f.read()

        ws_users = []
        grpc_users = []
        xhttp_users = []

        for u in users:
            if u.protocol == ProtocolType.VLESS and u.enabled:
                creds = u.credentials
                uuid = creds.get("uuid")
                u_type = creds.get("type", "ws")
                item = {"uuid": uuid, "name": f"{u.nickname}@vless"}
                if u_type == "ws":
                    ws_users.append(item)
                elif u_type == "grpc":
                    grpc_users.append(item)
                elif u_type == "xhttp":
                    xhttp_users.append(item)

        content = tmpl.replace("{{VLESS_WS_PATH}}", config.vless_ws_path)
        content = content.replace("{{VLESS_GRPC_SERVICE}}", config.vless_grpc_service)
        content = content.replace("{{VLESS_XHTTP_PATH}}", config.vless_xhttp_path)
        content = content.replace("{{DOMAIN}}", config.domain)

        ws_users_str = json.dumps(ws_users, indent=8)
        grpc_users_str = json.dumps(grpc_users, indent=8)
        xhttp_users_str = json.dumps(xhttp_users, indent=8)

        content = content.replace("// {{VLESS_WS_USERS}}", ws_users_str.strip("[]").strip())
        content = content.replace("// {{VLESS_GRPC_USERS}}", grpc_users_str.strip("[]").strip())
        content = content.replace("// {{VLESS_XHTTP_USERS}}", xhttp_users_str.strip("[]").strip())

        os.makedirs(os.path.dirname(self.singbox_dest), exist_ok=True)
        with open(self.singbox_dest, "w", encoding="utf-8") as f:
            f.write(content)
        try:
            os.chmod(self.singbox_dest, 0o600)
        except Exception:
            pass

    def _render_mieru(self, config: AppConfig, users: List[User]):
        mieru_users = []
        for u in users:
            if u.protocol == ProtocolType.MIERU and u.enabled:
                creds = u.credentials
                username = creds.get("username", u.nickname)
                password = creds.get("password", "")
                mieru_users.append({"name": username, "password": password})

        mieru_cfg = {
            "portBindings": [
                {
                    "port": config.mieru_port,
                    "protocol": "TCP"
                }
            ],
            "users": mieru_users,
            "logging": {
                "level": "INFO"
            }
        }

        os.makedirs(os.path.dirname(self.mieru_dest), exist_ok=True)
        with open(self.mieru_dest, "w", encoding="utf-8") as f:
            json.dump(mieru_cfg, f, indent=2, ensure_ascii=False)
        try:
            os.chmod(self.mieru_dest, 0o600)
        except Exception:
            pass

    def _render_subscriptions(self, config: AppConfig, users: List[User]):
        sub_dir = os.path.join(self.project_root, "sub")
        os.makedirs(sub_dir, exist_ok=True)

        for u in users:
            if not u.enabled or not u.sub_token:
                continue

            links = []
            link = UserService.build_client_link(u, config)
            if link:
                links.append(link)

            b64_content = base64.b64encode("\n".join(links).encode("utf-8")).decode("utf-8")
            target_file = os.path.join(sub_dir, u.sub_token)
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(b64_content)
