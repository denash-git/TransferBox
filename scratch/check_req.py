import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.31.209.61', username='root', password='OK82cn4ZJKIDVICQt8BsAzIDwBVAiaNb')
stdin, stdout, stderr = ssh.exec_command('python3 -c "import requests"')
print('ERR:', stderr.read().decode())
print('OUT:', stdout.read().decode())
ssh.close()
