import os
import sys
import re
import socket
import subprocess
from core.config_manager import load_env, save_env, get_current_ssh_port

PROJECT_ROOT = "/opt/transferbox"
SSHD_CONFIG_DIR = "/etc/ssh/sshd_config.d"
TRANSFERBOX_SSH_AUTH_CONF = "/etc/ssh/sshd_config.d/00-transferbox-auth.conf"
AUTHORIZED_KEYS_PATH = "/root/.ssh/authorized_keys"
ROOT_SSH_DIR = "/root/.ssh"


def ensure_sshd_includes_dropin():
    """Ensure sshd_config includes sshd_config.d/*.conf for drop-in modularity."""
    config_path = "/etc/ssh/sshd_config"
    if not os.path.exists(config_path):
        return
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
        if "Include /etc/ssh/sshd_config.d/*.conf" not in content and "include /etc/ssh/sshd_config.d/*.conf" not in content:
            with open(config_path, "w", encoding="utf-8") as f:
                f.write("Include /etc/ssh/sshd_config.d/*.conf\n" + content)
    except Exception:
        pass


def get_ssh_auth_mode() -> str:
    """
    Returns current active authentication mode: 'password' or 'key'.
    'password' = PasswordAuthentication yes
    'key' = PasswordAuthentication no (key-only)
    """
    if os.path.exists(TRANSFERBOX_SSH_AUTH_CONF):
        try:
            with open(TRANSFERBOX_SSH_AUTH_CONF, "r", encoding="utf-8") as f:
                content = f.read()
            if re.search(r"^\s*PasswordAuthentication\s+no\b", content, re.M | re.I):
                return "key"
            elif re.search(r"^\s*PasswordAuthentication\s+yes\b", content, re.M | re.I):
                return "password"
        except Exception:
            pass

    try:
        res = subprocess.run(["sshd", "-T"], capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                if line.lower().startswith("passwordauthentication "):
                    val = line.split()[1].strip().lower()
                    return "password" if val == "yes" else "key"
    except Exception:
        pass

    return "password"


def get_authorized_keys() -> list[dict]:
    """
    Reads /root/.ssh/authorized_keys and returns list of parsed public keys.
    """
    keys = []
    if not os.path.exists(AUTHORIZED_KEYS_PATH):
        return keys

    try:
        with open(AUTHORIZED_KEYS_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for idx, line in enumerate(lines, start=1):
            raw = line.strip()
            if not raw or raw.startswith("#"):
                continue

            parts = raw.split()
            if len(parts) >= 2:
                key_type = parts[0]
                key_data = parts[1]
                comment = " ".join(parts[2:]) if len(parts) > 2 else "без комментария"

                fingerprint = ""
                try:
                    fp_proc = subprocess.run(
                        ["ssh-keygen", "-lf", "-"],
                        input=raw + "\n",
                        capture_output=True,
                        text=True,
                        timeout=3
                    )
                    if fp_proc.returncode == 0:
                        fp_parts = fp_proc.stdout.strip().split()
                        if len(fp_parts) >= 2:
                            fingerprint = fp_parts[1]
                except Exception:
                    pass

                if not fingerprint:
                    fingerprint = key_data[:12] + "..." + key_data[-8:]

                keys.append({
                    "index": len(keys) + 1,
                    "line_num": idx,
                    "type": key_type,
                    "fingerprint": fingerprint,
                    "comment": comment,
                    "raw": raw
                })
    except Exception as e:
        print(f"[WARN] Ошибка чтения authorized_keys: {e}", file=sys.stderr)

    return keys


def generate_ssh_key() -> tuple[bool, str, dict]:
    """
    Generates a new Ed25519 keypair on the server.
    File name: /root/ssh_key_transferbox_<hostname>_<N>
    Appends public key to /root/.ssh/authorized_keys.
    Leaves private key in /root/ for user to download.
    Does NOT automatically change auth mode.
    """
    try:
        try:
            hostname = socket.gethostname().split(".")[0]
        except Exception:
            hostname = "vps"
        if not hostname or hostname in ("localhost", ""):
            hostname = "server"

        # Find next available index N (1, 2, 3...)
        n = 1
        while True:
            candidate = f"/root/ssh_key_transferbox_{hostname}_{n}"
            candidate_pub = f"{candidate}.pub"
            if not os.path.exists(candidate) and not os.path.exists(candidate_pub):
                break
            n += 1

        private_key_path = f"/root/ssh_key_transferbox_{hostname}_{n}"
        public_key_path = f"{private_key_path}.pub"
        comment = f"transferbox_{hostname}_{n}"

        # Generate Ed25519 key without passphrase
        res = subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-N", "", "-C", comment, "-f", private_key_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        if res.returncode != 0:
            return False, f"Ошибка ssh-keygen: {res.stderr.strip()}", {}

        os.chmod(private_key_path, 0o600)

        # Read generated public key
        with open(public_key_path, "r", encoding="utf-8") as f:
            pub_content = f.read().strip()

        # Ensure /root/.ssh directory exists with proper permissions
        os.makedirs(ROOT_SSH_DIR, exist_ok=True)
        os.chmod(ROOT_SSH_DIR, 0o700)

        # Append public key to authorized_keys
        with open(AUTHORIZED_KEYS_PATH, "a", encoding="utf-8") as f:
            f.write(f"\n{pub_content}\n")
        os.chmod(AUTHORIZED_KEYS_PATH, 0o600)

        # Remove public key file as it is already in authorized_keys
        if os.path.exists(public_key_path):
            os.remove(public_key_path)

        return True, "Ключ успешно сгенерирован", {
            "private_key_path": private_key_path,
            "filename": os.path.basename(private_key_path),
            "comment": comment,
            "index": n
        }
    except Exception as e:
        return False, f"Ошибка при генерации ключа: {e}", {}


def delete_authorized_key(target_index: int) -> tuple[bool, str]:
    """Deletes public key by 1-based index from authorized_keys."""
    keys = get_authorized_keys()
    if not (1 <= target_index <= len(keys)):
        return False, f"Неверный номер ключа: {target_index}."

    target_key = keys[target_index - 1]
    raw_to_remove = target_key["raw"]

    try:
        with open(AUTHORIZED_KEYS_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = []
        removed = False
        for line in lines:
            if line.strip() == raw_to_remove and not removed:
                removed = True
                continue
            new_lines.append(line)

        with open(AUTHORIZED_KEYS_PATH, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        os.chmod(AUTHORIZED_KEYS_PATH, 0o600)

        # Safety: If mode is currently 'key' and no keys remain, revert to 'password' mode
        remaining = get_authorized_keys()
        if len(remaining) == 0 and get_ssh_auth_mode() == "key":
            set_ssh_auth_mode("password")
            return True, f"Ключ #{target_index} удален. Ключей больше нет — вход по паролю автоматически включен."

        return True, f"Ключ #{target_index} ({target_key['comment']}) успешно удален."
    except Exception as e:
        return False, f"Ошибка при удалении ключа: {e}"


def set_ssh_auth_mode(target_mode: str) -> tuple[bool, str]:
    """
    Switches SSH authentication mode between 'password' and 'key'.
    Validates sshd config with sshd -t before restarting ssh.
    """
    if target_mode in ("key", "disable_password", "key_only"):
        normalized_mode = "key"
    elif target_mode in ("password", "enable_password"):
        normalized_mode = "password"
    else:
        return False, f"Неверный режим: {target_mode}."

    current_mode = get_ssh_auth_mode()
    if normalized_mode == current_mode:
        if normalized_mode == "key":
            return True, "Вход по паролю уже отключен."
        else:
            return True, "Вход по паролю уже включен."

    if normalized_mode == "key":
        keys = get_authorized_keys()
        if len(keys) == 0:
            return False, "Нельзя отключить вход по паролю: в системе нет ни одного открытого ключа! Сначала сгенерируйте ключ."

    ensure_sshd_includes_dropin()
    os.makedirs(SSHD_CONFIG_DIR, exist_ok=True)

    backup_content = None
    if os.path.exists(TRANSFERBOX_SSH_AUTH_CONF):
        try:
            with open(TRANSFERBOX_SSH_AUTH_CONF, "r", encoding="utf-8") as f:
                backup_content = f.read()
        except Exception:
            pass

    # Clean up legacy 99-transferbox-auth.conf if present
    legacy_conf = "/etc/ssh/sshd_config.d/99-transferbox-auth.conf"
    if os.path.exists(legacy_conf):
        try:
            os.remove(legacy_conf)
        except Exception:
            pass

    try:
        if normalized_mode == "key":
            content = """# TransferBox SSH Authentication
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
"""
        else:
            content = """# TransferBox SSH Authentication
PasswordAuthentication yes
KbdInteractiveAuthentication yes
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
"""

        with open(TRANSFERBOX_SSH_AUTH_CONF, "w", encoding="utf-8") as f:
            f.write(content)
        os.chmod(TRANSFERBOX_SSH_AUTH_CONF, 0o644)

        # Validate with sshd -t
        check = subprocess.run(["sshd", "-t"], capture_output=True, text=True)
        if check.returncode != 0:
            if backup_content is not None:
                with open(TRANSFERBOX_SSH_AUTH_CONF, "w", encoding="utf-8") as f:
                    f.write(backup_content)
            else:
                if os.path.exists(TRANSFERBOX_SSH_AUTH_CONF):
                    os.remove(TRANSFERBOX_SSH_AUTH_CONF)
            return False, f"Ошибка проверки sshd -t: {check.stderr.strip()}. Изменения отменены."

        # Restart SSH service
        res = subprocess.run(["systemctl", "restart", "ssh"], capture_output=True, text=True)
        if res.returncode != 0:
            res = subprocess.run(["systemctl", "restart", "sshd"], capture_output=True, text=True)
            if res.returncode != 0:
                if backup_content is not None:
                    with open(TRANSFERBOX_SSH_AUTH_CONF, "w", encoding="utf-8") as f:
                        f.write(backup_content)
                else:
                    if os.path.exists(TRANSFERBOX_SSH_AUTH_CONF):
                        os.remove(TRANSFERBOX_SSH_AUTH_CONF)
                subprocess.run(["systemctl", "restart", "ssh"], capture_output=True)
                subprocess.run(["systemctl", "restart", "sshd"], capture_output=True)
                return False, f"Не удалось перезапустить службу SSH: {res.stderr.strip()}"

        env = load_env()
        env["SSH_AUTH_MODE"] = normalized_mode
        save_env(env)

        if normalized_mode == "key":
            return True, "Вход по паролю успешно отключен."
        else:
            return True, "Вход по паролю успешно включен."
    except Exception as e:
        return False, f"Ошибка при смене режима: {e}"


def get_ssh_auth_status() -> dict:
    """Returns combined status dict for UI (Telegram and TUI)."""
    mode = get_ssh_auth_mode()
    keys = get_authorized_keys()
    ssh_port = get_current_ssh_port()
    password_allowed = (mode == "password")
    return {
        "mode": mode,
        "password_auth": password_allowed,
        "password_status_label": "🟢 Включен" if password_allowed else "🔴 Отключен",
        "key_status_label": "🟢 Включен",
        "mode_label": "Вход по паролю: 🟢 Включен" if password_allowed else "Вход по паролю: 🔴 Отключен",
        "keys": keys,
        "keys_count": len(keys),
        "ssh_port": ssh_port
    }
