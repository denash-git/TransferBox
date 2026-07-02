import uuid
import secrets
import subprocess
from core.config_manager import load_users, save_users, load_env

def generate_uuid():
    return str(uuid.uuid4())

def generate_password():
    return secrets.token_hex(12)

def generate_username():
    return "user_" + secrets.token_hex(4)

def add_user(nickname, protocol, user_type="ws"):
    users = load_users()
    
    # Check if nickname already exists
    for u in users:
        if u.get("nickname") == nickname:
            return False, "User with this nickname already exists."
            
    if protocol == "naive":
        username = generate_username()
        # Ensure unique username
        while any(u.get("credentials", {}).get("username") == username for u in users):
            username = generate_username()
            
        new_user = {
            "nickname": nickname,
            "protocol": "naive",
            "credentials": {
                "username": username,
                "password": generate_password()
            },
            "enabled": True
        }
    elif protocol == "vless":
        new_user = {
            "nickname": nickname,
            "protocol": "vless",
            "credentials": {
                "uuid": generate_uuid(),
                "type": user_type # ws or grpc
            },
            "enabled": True
        }
    else:
        return False, "Unsupported protocol."
        
    users.append(new_user)
    save_users(users)
    return True, new_user

def delete_user(nickname):
    users = load_users()
    initial_len = len(users)
    users = [u for u in users if u.get("nickname") != nickname]
    if len(users) == initial_len:
        return False, "User not found."
    save_users(users)
    return True, "User deleted successfully."

def toggle_user(nickname, enabled):
    users = load_users()
    for u in users:
        if u.get("nickname") == nickname:
            u["enabled"] = enabled
            save_users(users)
            return True, f"User status updated to {'enabled' if enabled else 'disabled'}."
    return False, "User not found."

def build_client_link(user_obj):
    env = load_env()
    domain = env.get("DOMAIN", "yourdomain.com")
    
    protocol = user_obj.get("protocol")
    nickname = user_obj.get("nickname")
    creds = user_obj.get("credentials", {})
    
    if protocol == "naive":
        username = creds.get("username")
        password = creds.get("password")
        return f"naive+https://{username}:{password}@{domain}:443#{nickname}"
        
    elif protocol == "vless":
        user_uuid = creds.get("uuid")
        user_type = creds.get("type", "ws")
        
        if user_type == "ws":
            path = env.get("VLESS_WS_PATH", "/vless-ws")
            return f"vless://{user_uuid}@{domain}:443?encryption=none&security=tls&type=ws&path={path}#{nickname}"
        else:
            service = env.get("VLESS_GRPC_SERVICE", "vless-grpc")
            return f"vless://{user_uuid}@{domain}:443?encryption=none&security=tls&type=grpc&serviceName={service}#{nickname}"
            
    return ""

def print_qr_code(link):
    # Try using system qrencode if available
    try:
        subprocess.run(["qrencode", "-t", "ANSIUTF8", link])
    except Exception:
        print("  [Предупреждение] Пакет qrencode не установлен на сервере.")
        print("  Вы можете установить его через: apt install qrencode")
