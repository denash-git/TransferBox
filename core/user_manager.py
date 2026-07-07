import uuid
import secrets
import subprocess
from core.config_manager import load_users, save_users, load_env, build_client_link

def generate_uuid():
    return str(uuid.uuid4())

def generate_password():
    return secrets.token_hex(12)

def generate_username():
    return "user_" + secrets.token_hex(4)

def add_user(nickname, protocol, user_type="ws"):
    users = load_users()
    
    # Find existing sub_token for this nickname
    existing_token = next((u.get("sub_token") for u in users if u.get("nickname") == nickname), None)
    
    # Check if this exact protocol/type already exists for this nickname
    for u in users:
        if u.get("nickname") == nickname:
            u_proto = u.get("protocol")
            u_type = u.get("credentials", {}).get("type", "")
            
            if protocol == "naive" and u_proto == "naive":
                return False, f"User '{nickname}' already has NaiveProxy protocol."
            if protocol == "vless" and u_proto == "vless" and u_type == user_type:
                return False, f"User '{nickname}' already has VLESS over {user_type.upper()} protocol."
            
    if protocol == "naive":
        username = generate_username()
        while any(u.get("credentials", {}).get("username") == username for u in users):
            username = generate_username()
            
        new_user = {
            "nickname": nickname,
            "protocol": "naive",
            "credentials": {
                "username": username,
                "password": generate_password()
            },
            "enabled": True,
            "sub_token": existing_token or secrets.token_hex(8)
        }
    elif protocol == "vless":
        new_user = {
            "nickname": nickname,
            "protocol": "vless",
            "credentials": {
                "uuid": generate_uuid(),
                "type": user_type
            },
            "enabled": True,
            "sub_token": existing_token or secrets.token_hex(8)
        }
    elif protocol == "mieru":
        username = generate_username()
        while any(u.get("credentials", {}).get("username") == username for u in users):
            username = generate_username()
        new_user = {
            "nickname": nickname,
            "protocol": "mieru",
            "credentials": {
                "username": username,
                "password": generate_password()
            },
            "enabled": True,
            "sub_token": existing_token or secrets.token_hex(8)
        }
    else:
        return False, "Unsupported protocol."
        
    users.append(new_user)
    save_users(users)
    return True, new_user

def delete_user(nickname, protocol=None, user_type=None):
    users = load_users()
    initial_len = len(users)
    if protocol:
        users = [u for u in users if not (u.get("nickname") == nickname and u.get("protocol") == protocol and u.get("credentials", {}).get("type", "") == (user_type or ""))]
    else:
        users = [u for u in users if u.get("nickname") != nickname]
    if len(users) == initial_len:
        return False, "User not found."
    save_users(users)
    return True, "User deleted successfully."

def toggle_user(nickname, enabled, protocol=None, user_type=None):
    users = load_users()
    updated = False
    for u in users:
        if u.get("nickname") == nickname:
            if protocol and (u.get("protocol") != protocol or u.get("credentials", {}).get("type", "") != (user_type or "")):
                continue
            u["enabled"] = enabled
            updated = True
    if updated:
        save_users(users)
        return True, f"User status updated to {'enabled' if enabled else 'disabled'}."
    return False, "User not found."

def print_qr_code(link):
    # Try using system qrencode if available
    try:
        subprocess.run(["qrencode", "-t", "ANSIUTF8", link])
    except Exception:
        print("  [Предупреждение] Пакет qrencode не установлен на сервере.")
        print("  Вы можете установить его через: apt install qrencode")
