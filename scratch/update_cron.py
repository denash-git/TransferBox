import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.31.209.61', username='root', password='OK82cn4ZJKIDVICQt8BsAzIDwBVAiaNb')

cron_content = """*/5 * * * * root PYTHONPATH=/opt/transferbox /usr/bin/python3 /opt/transferbox/bot/check_services.py >/dev/null 2>&1
0 0 * * * root PYTHONPATH=/opt/transferbox /usr/bin/python3 /opt/transferbox/bot/check_updates.py >/dev/null 2>&1
0 1 * * * root PYTHONPATH=/opt/transferbox /usr/bin/python3 /opt/transferbox/bot/backup.py >/dev/null 2>&1
"""

# Base64 encode it to transfer safely without escaping issues
import base64
encoded = base64.b64encode(cron_content.encode()).decode()

cmd = f"echo '{encoded}' | base64 -d > /etc/cron.d/transferbox-bot && chmod 0644 /etc/cron.d/transferbox-bot"
ssh.exec_command(cmd)
print("Cron configuration updated on VPS.")
ssh.close()
