import os
import json
import subprocess

PROJECT_ROOT = "/opt/transferbox"
INSTANCE_ENV = os.path.join(PROJECT_ROOT, "instance.env")
USERS_DB = os.path.join(PROJECT_ROOT, "users.json")

CADDY_CONFIG = "/etc/caddy/Caddyfile"
SINGBOX_CONFIG = "/etc/sing-box/config.json"

TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "templates")
CADDY_TEMPLATE = os.path.join(TEMPLATES_DIR, "Caddyfile.template")
SINGBOX_TEMPLATE = os.path.join(TEMPLATES_DIR, "sing-box-base.json.template")

def load_env():
    env = {}
    if os.path.exists(INSTANCE_ENV):
        with open(INSTANCE_ENV, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    env[key.strip()] = val.strip()
    return env

def save_env(env):
    with open(INSTANCE_ENV, "w", encoding="utf-8") as f:
        f.write("# TransferBox Instance Config\n")
        for k, v in env.items():
            f.write(f"{k}={v}\n")

def load_users():
    if os.path.exists(USERS_DB):
        try:
            with open(USERS_DB, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_users(users):
    with open(USERS_DB, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def render_configs():
    env = load_env()
    users = load_users()

    domain = env.get("DOMAIN", "example.com")
    email = env.get("ADMIN_EMAIL", "")
    fakesite_template = env.get("FAKE_SITE_TEMPLATE", "aether")
    
    # Path settings
    vless_ws_path = env.get("VLESS_WS_PATH", "/")
    vless_grpc_service = env.get("VLESS_GRPC_SERVICE", "")
    vless_xhttp_path = env.get("VLESS_XHTTP_PATH", "/xhttp")

    fakesite_dir = os.path.join(PROJECT_ROOT, "templates", "fakesite", fakesite_template)
    if not os.path.exists(fakesite_dir):
        fakesite_dir = os.path.join(PROJECT_ROOT, "templates", "fakesite", "aether")

    # 1. Render Caddyfile
    basic_auth_rules = []
    for u in users:
        if u.get("protocol") == "naive" and u.get("enabled", True):
            creds = u.get("credentials", {})
            user = creds.get("username")
            password = creds.get("password")
            if user and password:
                basic_auth_rules.append(f"basic_auth {user} {password}")

    basic_auth_str = "\n        ".join(basic_auth_rules) if basic_auth_rules else "# No users configured"

    if not os.path.exists(CADDY_TEMPLATE):
        raise FileNotFoundError(f"Caddyfile template not found: {CADDY_TEMPLATE}")

    with open(CADDY_TEMPLATE, "r", encoding="utf-8") as f:
        caddy_tmpl = f.read()

    # Direct substitution of domain, email, and fake site directory
    caddy_content = caddy_tmpl.replace("{{DOMAIN}}", domain)
    if email:
        caddy_content = caddy_content.replace("{{ADMIN_EMAIL}}", email)
    else:
        caddy_content = caddy_content.replace("tls {{ADMIN_EMAIL}}", "tls")
    caddy_content = caddy_content.replace("{{FAKESITE_DIR}}", fakesite_dir)
    caddy_content = caddy_content.replace("{{BASIC_AUTH_LIST}}", basic_auth_str)
    caddy_content = caddy_content.replace("{{VLESS_WS_PATH}}", vless_ws_path)
    caddy_content = caddy_content.replace("{{VLESS_GRPC_PATH}}", f"/{vless_grpc_service}")
    caddy_content = caddy_content.replace("{{VLESS_XHTTP_PATH}}", vless_xhttp_path)

    # 2. Render sing-box base config
    vless_ws_users = []
    vless_grpc_users = []
    vless_xhttp_users = []

    for u in users:
        if u.get("protocol") == "vless" and u.get("enabled", True):
            creds = u.get("credentials", {})
            uuid = creds.get("uuid")
            email_addr = u.get("nickname") + "@vless"
            user_type = creds.get("type", "ws")
            
            user_obj = {"uuid": uuid, "name": email_addr}
            if user_type == "ws":
                vless_ws_users.append(user_obj)
            elif user_type == "grpc":
                vless_grpc_users.append(user_obj)
            elif user_type == "xhttp":
                vless_xhttp_users.append(user_obj)

    if not os.path.exists(SINGBOX_TEMPLATE):
        raise FileNotFoundError(f"sing-box base template not found: {SINGBOX_TEMPLATE}")

    with open(SINGBOX_TEMPLATE, "r", encoding="utf-8") as f:
        sb_tmpl = f.read()

    # Replaces placeholders (chain: each replace reads from previous result)
    sb_content = sb_tmpl.replace("{{VLESS_WS_PATH}}", vless_ws_path)
    sb_content = sb_content.replace("{{VLESS_GRPC_SERVICE}}", vless_grpc_service)
    sb_content = sb_content.replace("{{VLESS_XHTTP_PATH}}", vless_xhttp_path)
    sb_content = sb_content.replace("{{DOMAIN}}", domain)

    # Inject users into inbounds
    ws_users_str = json.dumps(vless_ws_users, indent=8)
    grpc_users_str = json.dumps(vless_grpc_users, indent=8)
    xhttp_users_str = json.dumps(vless_xhttp_users, indent=8)

    sb_content = sb_content.replace("// {{VLESS_WS_USERS}}", ws_users_str.strip("[]").strip())
    sb_content = sb_content.replace("// {{VLESS_GRPC_USERS}}", grpc_users_str.strip("[]").strip())
    sb_content = sb_content.replace("// {{VLESS_XHTTP_USERS}}", xhttp_users_str.strip("[]").strip())

    # Write to target dirs
    os.makedirs(os.path.dirname(CADDY_CONFIG), exist_ok=True)
    with open(CADDY_CONFIG, "w", encoding="utf-8") as f:
        f.write(caddy_content)

    os.makedirs(os.path.dirname(SINGBOX_CONFIG), exist_ok=True)
    with open(SINGBOX_CONFIG, "w", encoding="utf-8") as f:
        f.write(sb_content)

def validate_and_restart():
    # 1. Validate Caddyfile
    res = subprocess.run(["caddy", "validate", "--config", CADDY_CONFIG], capture_output=True, text=True)
    if res.returncode != 0:
        return False, f"Caddyfile validation failed:\n{res.stderr}"

    # 2. Validate sing-box config
    res = subprocess.run(["sing-box", "check", "-c", SINGBOX_CONFIG], capture_output=True, text=True)
    if res.returncode != 0:
        return False, f"sing-box config validation failed:\n{res.stderr}"

    # Restart services
    subprocess.run(["systemctl", "restart", "caddy"])
    subprocess.run(["systemctl", "restart", "sing-box"])

    return True, "Services successfully reloaded and validated!"
