import os
import re
import subprocess
from core.config_manager import load_env, save_env, get_current_ssh_port

PROJECT_ROOT = "/opt/transferbox"
PORTSCAN_TRAP_FILTER = "/etc/fail2ban/filter.d/portscan-trap.conf"
TRANSFERBOX_JAIL = "/etc/fail2ban/jail.d/transferbox.conf"
UFW_BEFORE_RULES = "/etc/ufw/before.rules"
UFW_BEFORE6_RULES = "/etc/ufw/before6.rules"
TRAP_PORTS = "21,23,25,445,1433,3389,5900,8080"


def is_fail2ban_installed() -> bool:
    """Check if fail2ban-client is available in PATH."""
    return subprocess.run(["which", "fail2ban-client"], capture_output=True).returncode == 0


def is_security_active() -> bool:
    """Check if fail2ban service is active and running."""
    res = subprocess.run(["systemctl", "is-active", "--quiet", "fail2ban"])
    return res.returncode == 0


def is_port80_allowed() -> bool:
    """Check if port 80/tcp is currently allowed in UFW rules."""
    try:
        res = subprocess.run(["ufw", "status"], capture_output=True, text=True)
        for line in res.stdout.splitlines():
            if "80/tcp" in line and "ALLOW" in line:
                return True
        return False
    except Exception:
        return False


def remove_port80_ufw() -> bool:
    """Remove port 80/tcp allow rules from UFW (both IPv4 and IPv6)."""
    try:
        subprocess.run(["ufw", "delete", "allow", "80/tcp"], capture_output=True, text=True)
        res = subprocess.run(["ufw", "status", "numbered"], capture_output=True, text=True)
        lines = res.stdout.splitlines()
        for line in reversed(lines):
            if "80/tcp" in line and "ALLOW" in line:
                m = re.match(r"\[\s*(\d+)\]", line.strip())
                if m:
                    rule_num = m.group(1)
                    subprocess.run(["ufw", "delete", str(rule_num)], input="y\n", capture_output=True, text=True)
        return True
    except Exception:
        return False


def setup_ufw_trap_rules(enable: bool = True) -> tuple[bool, str]:
    """Add or remove Honeypot trap logging rules in /etc/ufw/before.rules and before6.rules."""
    trap_rule_v4 = f"-A ufw-before-input -p tcp -m multiport --dports {TRAP_PORTS} -m tcp --syn -m limit --limit 6/min -j LOG --log-prefix \"[PORTSCAN-TRAP]: \" --log-level 4\n"
    trap_rule_v6 = f"-A ufw6-before-input -p tcp -m multiport --dports {TRAP_PORTS} -m tcp --syn -m limit --limit 6/min -j LOG --log-prefix \"[PORTSCAN-TRAP]: \" --log-level 4\n"

    try:
        for file_path, rule_line in [(UFW_BEFORE_RULES, trap_rule_v4), (UFW_BEFORE6_RULES, trap_rule_v6)]:
            if not os.path.exists(file_path):
                continue

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Clean any existing trap rules
            lines = content.splitlines(True)
            cleaned_lines = [l for l in lines if "[PORTSCAN-TRAP]" not in l]

            if enable:
                # Insert before COMMIT
                new_lines = []
                inserted = False
                for line in cleaned_lines:
                    if line.strip() == "COMMIT" and not inserted:
                        new_lines.append("# Portscan Honeypot Trap\n")
                        new_lines.append(rule_line)
                        inserted = True
                    new_lines.append(line)
                if not inserted:
                    new_lines.append(rule_line)
                final_content = "".join(new_lines)
            else:
                final_content = "".join(cleaned_lines)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(final_content)

        subprocess.run(["ufw", "reload"], capture_output=True, text=True)
        return True, "UFW правила ловушек обновлены"
    except Exception as e:
        return False, f"Ошибка настройки UFW правил: {e}"


def configure_fail2ban(ssh_port: int = 22) -> tuple[bool, str]:
    """Configure fail2ban filter and jail for TransferBox."""
    try:
        os.makedirs(os.path.dirname(PORTSCAN_TRAP_FILTER), exist_ok=True)
        filter_content = """[Definition]
failregex = ^.*\\[PORTSCAN-TRAP\\]: .* SRC=<HOST> .*$
ignoreregex =
"""
        with open(PORTSCAN_TRAP_FILTER, "w", encoding="utf-8") as f:
            f.write(filter_content)

        os.makedirs(os.path.dirname(TRANSFERBOX_JAIL), exist_ok=True)
        jail_content = f"""[DEFAULT]
bantime = 1d
findtime = 10m
maxretry = 5
backend = systemd
banaction = nftables[type=allports, blocktype=drop]
ignoreip = 127.0.0.1/8 ::1

[sshd]
enabled = true
port = {ssh_port}

[portscan-trap]
enabled = true
filter = portscan-trap
backend = systemd
journalmatch = _TRANSPORT=kernel
maxretry = 1
findtime = 1d
bantime = 1d
banaction = nftables[type=allports, blocktype=drop]
"""
        with open(TRANSFERBOX_JAIL, "w", encoding="utf-8") as f:
            f.write(jail_content)

        return True, "Конфигурация Fail2ban успешно создана"
    except Exception as e:
        return False, f"Ошибка создания конфигов Fail2ban: {e}"


def enable_security() -> tuple[bool, str]:
    """Enable full scanner and bot protection (Fail2ban, Trap, Port 80 close)."""
    if not is_fail2ban_installed():
        res = subprocess.run(["DEBIAN_FRONTEND=noninteractive", "apt-get", "install", "-y", "fail2ban", "ipset"],
                             shell=True, capture_output=True, text=True)
        if res.returncode != 0:
            return False, f"Ошибка установки fail2ban: {res.stderr}"

    ssh_port = get_current_ssh_port()
    ok, msg = configure_fail2ban(ssh_port)
    if not ok:
        return False, msg

    setup_ufw_trap_rules(enable=True)
    remove_port80_ufw()

    subprocess.run(["systemctl", "enable", "fail2ban"], capture_output=True)
    res = subprocess.run(["systemctl", "restart", "fail2ban"], capture_output=True, text=True)
    if res.returncode != 0:
        return False, f"Не удалось запустить fail2ban: {res.stderr}"

    env = load_env()
    env["SECURITY_SCANNER_PROTECTION"] = "true"
    save_env(env)

    return True, "Защита от сканеров (Fail2ban + Silent Drop) успешно включена."


def disable_security() -> tuple[bool, str]:
    """Disable scanner protection and stop Fail2ban service."""
    setup_ufw_trap_rules(enable=False)
    subprocess.run(["systemctl", "stop", "fail2ban"], capture_output=True)
    subprocess.run(["systemctl", "disable", "fail2ban"], capture_output=True)

    env = load_env()
    env["SECURITY_SCANNER_PROTECTION"] = "false"
    save_env(env)

    return True, "Защита от сканеров отключена."


def get_security_status() -> dict:
    """Get real-time security statistics and list of banned scanners."""
    active = is_security_active()
    status_data = {
        "active": active,
        "total_banned": 0,
        "jails": {},
        "banned_ips": [],
        "port80_allowed": is_port80_allowed()
    }

    if not active:
        return status_data

    try:
        res = subprocess.run(["fail2ban-client", "status"], capture_output=True, text=True)
        jails = []
        for line in res.stdout.splitlines():
            if "Jail list:" in line:
                parts = line.split("Jail list:", 1)[1].strip()
                jails = [j.strip() for j in parts.split(",") if j.strip()]

        all_banned = set()
        for jail in jails:
            j_res = subprocess.run(["fail2ban-client", "status", jail], capture_output=True, text=True)
            currently_banned = 0
            banned_list = []
            for j_line in j_res.stdout.splitlines():
                if "Currently banned:" in j_line:
                    try:
                        currently_banned = int(j_line.split("Currently banned:", 1)[1].strip())
                    except ValueError:
                        currently_banned = 0
                elif "Banned IP list:" in j_line:
                    ips_str = j_line.split("Banned IP list:", 1)[1].strip()
                    if ips_str:
                        banned_list = ips_str.split()

            status_data["jails"][jail] = {
                "currently_banned": currently_banned,
                "banned_ips": banned_list
            }
            all_banned.update(banned_list)

        status_data["banned_ips"] = sorted(list(all_banned))
        status_data["total_banned"] = len(status_data["banned_ips"])
    except Exception:
        pass

    return status_data


def unban_ip(ip: str) -> tuple[bool, str]:
    """Unban an IP address from all fail2ban jails."""
    if not ip or not ip.strip():
        return False, "IP-адрес не указан"
    ip = ip.strip()

    try:
        res = subprocess.run(["fail2ban-client", "unban", ip], capture_output=True, text=True)
        if res.returncode == 0:
            return True, f"IP {ip} успешно разблокирован."
        else:
            return False, f"Ошибка разблокировки {ip}: {res.stderr or res.stdout}"
    except Exception as e:
        return False, str(e)


def unban_all() -> tuple[bool, str]:
    """Unban all banned IPs from all jails."""
    try:
        res = subprocess.run(["fail2ban-client", "unban", "--all"], capture_output=True, text=True)
        if res.returncode == 0:
            return True, "Все IP-адреса успешно разблокированы."
        else:
            return False, f"Ошибка разблокировки: {res.stderr or res.stdout}"
    except Exception as e:
        return False, str(e)


def unban_client_session(client_ip: str) -> tuple[bool, str]:
    """Emergency unban for current admin connection IP."""
    if not client_ip:
        return False, "Не удалось определить IP текущей сессии"
    return unban_ip(client_ip)
