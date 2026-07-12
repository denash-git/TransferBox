import os
import json
import urllib.request
import urllib.parse
import tempfile
import subprocess
from core.config_manager import load_env, load_users, build_client_link

def send_alert(text: str):
    env = load_env()
    token = env.get("TG_BOT_TOKEN")
    chat_id = env.get("TG_CHAT_ID")
    enabled = env.get("TG_BOT_ENABLED", "false").lower() == "true"
    alerts = env.get("TG_ALERTS_ENABLED", "false").lower() == "true"
    
    if not enabled or not alerts or not token or not chat_id:
        return
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            pass
    except urllib.error.HTTPError as e:
        print(f"[TG BOT] HTTP Error sending alert: {e.code} {e.reason} - {e.read().decode('utf-8', errors='replace')}")
    except Exception as e:
        print(f"[TG BOT] Error sending alert: {e}")

def send_photo(token: str, chat_id: int, photo_path: str, caption: str = ""):
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    
    with open(photo_path, "rb") as f:
        file_content = f.read()
        
    filename = os.path.basename(photo_path)
    
    parts = []
    parts.append(f"--{boundary}".encode("utf-8"))
    parts.append(b'Content-Disposition: form-data; name="chat_id"')
    parts.append(b"")
    parts.append(str(chat_id).encode("utf-8"))
    
    if caption:
        parts.append(f"--{boundary}".encode("utf-8"))
        parts.append(b'Content-Disposition: form-data; name="caption"')
        parts.append(b"")
        parts.append(caption.encode("utf-8"))
        
    parts.append(f"--{boundary}".encode("utf-8"))
    parts.append(f'Content-Disposition: form-data; name="photo"; filename="{filename}"'.encode("utf-8"))
    parts.append(b"Content-Type: image/png")
    parts.append(b"")
    parts.append(file_content)
    parts.append(f"--{boundary}--".encode("utf-8"))
    parts.append(b"")
    
    body = b"\r\n".join(parts)
    
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body))
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            pass
    except urllib.error.HTTPError as e:
        print(f"[TG BOT] HTTP Error sending photo: {e.code} {e.reason} - {e.read().decode('utf-8', errors='replace')}")
    except Exception as e:
        print(f"[TG BOT] Error sending photo: {e}")

def send_user_links(chat_id: int, user_nickname: str):
    env = load_env()
    token = env.get("TG_BOT_TOKEN")
    if not token:
        return
        
    users = load_users()
    user_protocols = [u for u in users if u.get("nickname") == user_nickname]
    if not user_protocols:
        return
        
    domain = env.get("DOMAIN", "yourdomain.com")
    sub_link = f"https://{domain}/sub/{user_nickname}"
    
    msg_parts = [f"🔑 <b>Ссылки для {user_nickname}:</b>\n"]
    msg_parts.append("🌀 <b>Ссылка подписки:</b>")
    msg_parts.append(f"<code>{sub_link}</code>\n")
    
    for u in user_protocols:
        proto = u.get("protocol")
        ptype = u.get("credentials", {}).get("type", "")
        proto_lbl = f"{proto.upper()} {ptype.upper()}".strip()
        link = build_client_link(u, env=env)
        if link:
            msg_parts.append(f"🌐 <b>{proto_lbl}:</b>")
            msg_parts.append(f"<code>{link}</code>\n")
            
    # Отправляем текстовое сообщение
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "\n".join(msg_parts),
        "parse_mode": "HTML"
    }
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            pass
    except urllib.error.HTTPError as e:
        print(f"[TG BOT] HTTP Error sending text links: {e.code} {e.reason} - {e.read().decode('utf-8', errors='replace')}")
    except Exception as e:
        print(f"[TG BOT] Error sending text links: {e}")
        
    # Генерируем и отправляем QR-коды
    for u in user_protocols:
        proto = u.get("protocol")
        ptype = u.get("credentials", {}).get("type", "")
        proto_lbl = f"{proto.upper()} {ptype.upper()}".strip()
        link = build_client_link(u, env=env)
        if link:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = tmp.name
            try:
                subprocess.run(["qrencode", "-o", tmp_path, link], check=True)
                send_photo(token, chat_id, tmp_path, caption=f"QR-код для {user_nickname} ({proto_lbl})")
            except Exception as e:
                print(f"[TG BOT] Error generating/sending QR code: {e}")
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
    # QR-код подписки
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        subprocess.run(["qrencode", "-o", tmp_path, sub_link], check=True)
        send_photo(token, chat_id, tmp_path, caption=f"QR-код подписки для {user_nickname}")
    except Exception as e:
        print(f"[TG BOT] Error generating/sending subscription QR: {e}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
