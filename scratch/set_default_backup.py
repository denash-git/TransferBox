import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.31.209.61', username='root', password='OK82cn4ZJKIDVICQt8BsAzIDwBVAiaNb')

cmd = 'PYTHONPATH=/opt/transferbox python3 -c "from core.config_manager import load_env, save_env; env = load_env(); env[\'BACKUP_HOUR\'] = \'12\'; env[\'BACKUP_MINUTE\'] = \'0\'; save_env(env); from bot.handlers.settings import update_cron_schedule; update_cron_schedule(12, 0)"'
stdin, stdout, stderr = ssh.exec_command(cmd)
print('OUT:', stdout.read().decode())
print('ERR:', stderr.read().decode())
ssh.close()
