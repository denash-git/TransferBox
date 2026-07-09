import os
import sys
import json
import subprocess
import re
import secrets
import urllib.parse
import shutil
import base64

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
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    mode = 0o600
    try:
        fd = os.open(INSTANCE_ENV, flags, mode)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("# TransferBox Instance Config\n")
            for k, v in env.items():
                f.write(f"{k}={v}\n")
        os.chmod(INSTANCE_ENV, 0o600)
    except Exception:
        with open(INSTANCE_ENV, "w", encoding="utf-8") as f:
            f.write("# TransferBox Instance Config\n")
            for k, v in env.items():
                f.write(f"{k}={v}\n")
        try:
            os.chmod(INSTANCE_ENV, 0o600)
        except Exception:
            pass


def load_users():
    if os.path.exists(USERS_DB):
        try:
            with open(USERS_DB, "r", encoding="utf-8") as f:
                users = json.load(f)
            changed = False
            for u in users:
                if "sub_token" not in u:
                    u["sub_token"] = secrets.token_hex(8)
                    changed = True
            if changed:
                save_users(users)
            return users
        except Exception as e:
            print(f"[WARNING] Не удалось загрузить users.json: {e}", file=sys.stderr)
            return []
    return []


def save_users(users):
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    mode = 0o600
    try:
        fd = os.open(USERS_DB, flags, mode)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        os.chmod(USERS_DB, 0o600)
    except Exception:
        with open(USERS_DB, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        try:
            os.chmod(USERS_DB, 0o600)
        except Exception:
            pass


def build_client_link(user_obj, env=None):
    if env is None:
        env = load_env()
    domain = env.get("DOMAIN", "yourdomain.com")
    
    protocol = user_obj.get("protocol")
    nickname = user_obj.get("nickname")
    creds = user_obj.get("credentials", {})
    
    if protocol == "naive":
        username = creds.get("username")
        password = creds.get("password")
        return f"naive://{username}:{password}@{domain}:443#{nickname}"
        
    elif protocol == "vless":
        user_uuid = creds.get("uuid")
        user_type = creds.get("type", "ws")
        
        if user_type == "ws":
            path = env.get("VLESS_WS_PATH", "/")
            return f"vless://{user_uuid}@{domain}:443?encryption=none&security=tls&sni={domain}&type=ws&path={path}#{nickname}"
        elif user_type == "grpc":
            service = env.get("VLESS_GRPC_SERVICE", "")
            return f"vless://{user_uuid}@{domain}:443?encryption=none&security=tls&sni={domain}&type=grpc&serviceName={service}#{nickname}"
        elif user_type == "xhttp":
            path = env.get("VLESS_XHTTP_PATH", "/xhttp")
            return f"vless://{user_uuid}@{domain}:443?encryption=none&security=tls&sni={domain}&type=httpupgrade&path={path}#{nickname}"
            
    elif protocol == "mieru":
        username = creds.get("username")
        password = creds.get("password")
        port = int(env.get("MIERU_PORT", 21000))
        safe_user = urllib.parse.quote(username)
        safe_pass = urllib.parse.quote(password)
        safe_profile = urllib.parse.quote(f"Mieru-{nickname}")
        return f"mierus://{safe_user}:{safe_pass}@{domain}?profile={safe_profile}&port={port}&protocol=TCP&multiplexing=MULTIPLEXING_HIGH"
            
    return ""


def build_mieru_json_config(user_obj):
    env = load_env()
    domain = env.get("DOMAIN", "yourdomain.com")
    creds = user_obj.get("credentials", {})
    username = creds.get("username")
    password = creds.get("password")
    port = int(env.get("MIERU_PORT", 21000))
    config = {
        "profileName": f"Mieru-{user_obj['nickname']}",
        "user": {
            "name": username,
            "password": password
        },
        "servers": [
            {
                "ipAddress": domain,
                "portBindings": [
                    {
                        "port": port,
                        "protocol": "TCP"
                    }
                ]
            }
        ],
        "mtu": 1400,
        "multiplexing": {
            "level": "MULTIPLEXING_HIGH"
        }
    }
    return json.dumps(config, indent=2)


def build_mieru_clash_yaml(user_obj):
    env = load_env()
    domain = env.get("DOMAIN", "yourdomain.com")
    creds = user_obj.get("credentials", {})
    username = creds.get("username")
    password = creds.get("password")
    port = int(env.get("MIERU_PORT", 21000))
    yaml_str = f"""proxies:
  - name: "Mieru-{user_obj['nickname']}"
    type: mieru
    server: {domain}
    port: {port}
    username: {username}
    password: {password}
    transport: tcp"""
    return yaml_str


def build_mieru_singbox_json(user_obj):
    env = load_env()
    domain = env.get("DOMAIN", "yourdomain.com")
    creds = user_obj.get("credentials", {})
    username = creds.get("username")
    password = creds.get("password")
    port = int(env.get("MIERU_PORT", 21000))
    config = {
        "outbounds": [
            {
                "type": "mieru",
                "tag": f"Mieru-{user_obj['nickname']}",
                "server": domain,
                "server_port": port,
                "transport": "TCP",
                "username": username,
                "password": password
            }
        ]
    }
    return json.dumps(config, indent=2)


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
    caddy_content = caddy_content.replace("{{FORWARD_PROXY_BLOCK}}", forward_proxy_block)
    caddy_content = caddy_content.replace("{{VLESS_WS_PATH}}", vless_ws_path)
    caddy_content = caddy_content.replace("{{VLESS_GRPC_PATH}}", f"/{vless_grpc_service}")
    caddy_content = caddy_content.replace("{{VLESS_XHTTP_PATH}}", vless_xhttp_path)
    caddy_content = caddy_content.replace("{{PROJECT_ROOT}}", PROJECT_ROOT)

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
    try:
        os.chmod(CADDY_CONFIG, 0o600)
    except Exception:
        pass

    os.makedirs(os.path.dirname(SINGBOX_CONFIG), exist_ok=True)
    with open(SINGBOX_CONFIG, "w", encoding="utf-8") as f:
        f.write(sb_content)
    try:
        import pwd
        import grp
        uid = pwd.getpwnam("root").pw_uid
        gid = grp.getgrnam("sing-box").gr_gid
        os.chown(SINGBOX_CONFIG, uid, gid)
        os.chmod(SINGBOX_CONFIG, 0o640)
    except Exception:
        try:
            os.chmod(SINGBOX_CONFIG, 0o600)
        except Exception:
            pass

    # 3. Generate subscription files in PROJECT_ROOT/sub/
    sub_dir = os.path.join(PROJECT_ROOT, "sub")
    if os.path.exists(sub_dir):
        shutil.rmtree(sub_dir)
    os.makedirs(sub_dir, exist_ok=True)
    try:
        os.chmod(sub_dir, 0o700)
    except Exception:
        pass

    for u in users:
        if not u.get("enabled", True):
            continue
        token = u.get("sub_token")
        if not token:
            continue

        # Find all active protocols for this nickname
        nick = u.get("nickname")
        nick_links = []
        for other in users:
            if other.get("nickname") == nick and other.get("enabled", True):
                link = build_client_link(other, env=env)
                if link:
                    nick_links.append(link)

        if nick_links:
            sub_content = "\n".join(nick_links)
            encoded = base64.b64encode(sub_content.encode("utf-8")).decode("utf-8")

            sub_file = os.path.join(sub_dir, token)
            with open(sub_file, "w", encoding="utf-8") as sf:
                sf.write(encoded)
            try:
                os.chmod(sub_file, 0o600)
            except Exception:
                pass

    # 4. Generate Mieru server configuration
    mieru_enabled = env.get("MIERU_ENABLED", "false").lower() == "true"
    if mieru_enabled:
        mieru_port = env.get("MIERU_PORT", "21000")
        mieru_users = []
        for u in users:
            if u.get("protocol") == "mieru" and u.get("enabled", True):
                creds = u.get("credentials", {})
                mieru_users.append({
                    "name": creds.get("username"),
                    "password": creds.get("password")
                })
        
        mita_config = {
            "portBindings": [
                {
                    "portRange": f"{mieru_port}-{mieru_port}",
                    "protocol": "TCP"
                },
                {
                    "portRange": f"{mieru_port}-{mieru_port}",
                    "protocol": "UDP"
                }
            ],
            "users": mieru_users,
            "loggingLevel": "INFO",
            "mtu": 1400
        }
        
        if os.path.exists("/usr/bin/mita"):
            override_dir = "/etc/systemd/system/mita.service.d"
            os.makedirs(override_dir, exist_ok=True)
            override_file = os.path.join(override_dir, "override.conf")
            with open(override_file, "w", encoding="utf-8") as f:
                f.write("[Service]\nEnvironment=\"MITA_CONFIG_JSON_FILE=/etc/mita/server.conf.json\"\n")
            try:
                os.chmod(override_file, 0o600)
            except Exception:
                pass
            
            mita_json_path = "/etc/mita/server.conf.json"
            os.makedirs(os.path.dirname(mita_json_path), exist_ok=True)
            with open(mita_json_path, "w", encoding="utf-8") as f:
                json.dump(mita_config, f, indent=2)
            try:
                os.chmod(mita_json_path, 0o600)
            except Exception:
                pass
                
            subprocess.run(["rm", "-f", "/etc/mita/server.conf.pb"])
            subprocess.run(["chown", "-R", "mita:mita", "/etc/mita"])
            subprocess.run(["systemctl", "daemon-reload"])


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
    res = subprocess.run(["systemctl", "restart", "caddy"], capture_output=True, text=True)
    if res.returncode != 0:
        return False, f"Не удалось перезапустить caddy:\n{res.stderr}"

    res = subprocess.run(["systemctl", "restart", "sing-box"], capture_output=True, text=True)
    if res.returncode != 0:
        return False, f"Не удалось перезапустить sing-box:\n{res.stderr}"

    # Manage mita service and UFW firewall rules
    env = load_env()
    mieru_enabled = env.get("MIERU_ENABLED", "false").lower() == "true"
    mieru_port = env.get("MIERU_PORT", "21000")
    mita_installed = os.path.exists("/usr/bin/mita")

    if mita_installed:
        # Dynamically clean up old UFW rules with Mieru comment
        status_res = subprocess.run(["ufw", "status", "numbered"], capture_output=True, text=True)
        if status_res.returncode == 0:
            rule_nums = []
            for line in status_res.stdout.splitlines():
                if "Mieru TCP" in line or "Mieru UDP" in line:
                    m = re.search(r'\[\s*(\d+)\]', line)
                    if m:
                        rule_nums.append(int(m.group(1)))
            for num in sorted(rule_nums, reverse=True):
                subprocess.run(["ufw", "delete", str(num)], input="y\n", text=True, capture_output=True)

        if mieru_enabled:
            subprocess.run(["systemctl", "enable", "mita"], capture_output=True)
            subprocess.run(["systemctl", "restart", "mita"], capture_output=True)
            # Allow port range in UFW
            subprocess.run(["ufw", "allow", f"{mieru_port}/tcp", "comment", "Mieru TCP"], capture_output=True)
            subprocess.run(["ufw", "allow", f"{mieru_port}/udp", "comment", "Mieru UDP"], capture_output=True)
        else:
            subprocess.run(["systemctl", "stop", "mita"], capture_output=True)
            subprocess.run(["systemctl", "disable", "mita"], capture_output=True)

    return True, "Services successfully reloaded and validated!"


def get_current_ssh_port():
    port = 22
    config_path = "/etc/ssh/sshd_config"
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.lower().startswith("port ") or line.lower().startswith("port\t"):
                    parts = line.split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        port = int(parts[1])
                        break
    return port


def change_ssh_port(new_port):
    if not (1 <= new_port <= 65535):
        return False, "Неверный порт. Диапазон: 1-65535."
        
    old_port = get_current_ssh_port()
    if old_port == new_port:
        return True, f"SSH уже настроен на порт {new_port}."
        
    config_path = "/etc/ssh/sshd_config"
    if not os.path.exists(config_path):
        return False, f"Конфигурационный файл {config_path} не найден."
        
    # 1. Открываем новый порт в UFW до изменения, чтобы не заблокировать пользователя
    subprocess.run(["ufw", "allow", f"{new_port}/tcp", "comment", "SSH Port"], capture_output=True)
    
    # 2. Читаем и обновляем sshd_config
    with open(config_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    port_replaced = False
    for i, line in enumerate(lines):
        clean_line = line.strip()
        if clean_line.lower().startswith("port ") or clean_line.lower().startswith("port\t"):
            lines[i] = f"Port {new_port}\n"
            port_replaced = True
            break
            
    if not port_replaced:
        for i, line in enumerate(lines):
            clean_line = line.strip()
            if clean_line.startswith("#") and ("port " in clean_line.lower() or "port\t" in clean_line.lower()):
                lines[i] = f"Port {new_port}\n"
                port_replaced = True
                break
                
    if not port_replaced:
        lines.append(f"\nPort {new_port}\n")
        
    with open(config_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
        
    # 3. Перезапускаем SSH сервис
    res = subprocess.run(["systemctl", "restart", "ssh"], capture_output=True)
    if res.returncode != 0:
        res = subprocess.run(["systemctl", "restart", "sshd"], capture_output=True)
        
    # 4. Проверяем, слушает ли SSH новый порт
    check = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True)
    port_active = bool(re.search(rf":{new_port}\s", check.stdout)) if check.returncode == 0 else False
    if not port_active:
        # Revert change
        for i, line in enumerate(lines):
            if line.strip() == f"Port {new_port}":
                lines[i] = f"Port {old_port}\n"
                break
        with open(config_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        subprocess.run(["systemctl", "restart", "ssh"], capture_output=True)
        subprocess.run(["systemctl", "restart", "sshd"], capture_output=True)
        return False, f"Ошибка: SSH-сервер не запустился на порту {new_port}. Изменения отменены."
        
    return True, f"Успешно! SSH переведен на порт {new_port}."


def remove_old_ssh_port_ufw(old_port):
    if old_port and old_port != 22:
        subprocess.run(["ufw", "delete", "allow", f"{old_port}/tcp"], capture_output=True)
