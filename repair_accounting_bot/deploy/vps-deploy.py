#!/usr/bin/env python3
"""Deploy repair-accounting-bot to VPS via SFTP."""

from __future__ import annotations

import os
import sys

try:
    import paramiko
except ImportError:
    import subprocess

    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'paramiko', '-q'])
    import paramiko

HOST = os.environ.get('VPS_HOST', '185.18.214.66')
USER = os.environ.get('VPS_USER', 'root')
PASSWORD = os.environ.get('VPS_PASSWORD', '')
LOCAL = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
REMOTE = '/opt/repair-accounting-bot'
EXCLUDE = {'.venv', '__pycache__', '.env', '.git', 'data', '.pytest_cache'}


def should_sync(name: str) -> bool:
    return name not in EXCLUDE


def ensure_remote_dir(sftp: paramiko.SFTPClient, remote_dir: str) -> None:
    if remote_dir in ('', '/', '.'):
        return
    parts = [part for part in remote_dir.split('/') if part]
    current = ''
    for part in parts:
        current = f'{current}/{part}' if current else f'/{part}'
        try:
            sftp.stat(current)
        except FileNotFoundError:
            sftp.mkdir(current)


def sync_tree(sftp: paramiko.SFTPClient, local_root: str, remote_root: str) -> int:
    count = 0
    for root, dirs, files in os.walk(local_root):
        dirs[:] = [d for d in dirs if should_sync(d)]
        rel = os.path.relpath(root, local_root)
        remote_dir = remote_root if rel == '.' else f'{remote_root}/{rel}'.replace('\\', '/')
        ensure_remote_dir(sftp, remote_dir)
        for name in files:
            if not should_sync(name):
                continue
            local_path = os.path.join(root, name)
            remote_path = f'{remote_dir}/{name}'
            sftp.put(local_path, remote_path)
            count += 1
    return count


def run_ssh(ssh: paramiko.SSHClient, command: str) -> None:
    print(f'\n>>> {command}')
    _, stdout, stderr = ssh.exec_command(command)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out:
        print(out, end='')
    if err:
        print(err, end='')
    code = stdout.channel.recv_exit_status()
    if code != 0:
        raise SystemExit(f'Command failed ({code}): {command}')


def main() -> None:
    if not PASSWORD:
        raise SystemExit('Set VPS_PASSWORD environment variable')

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)
    sftp = ssh.open_sftp()
    ensure_remote_dir(sftp, REMOTE)
    uploaded = sync_tree(sftp, LOCAL, REMOTE)
    print(f'Uploaded {uploaded} files to {REMOTE}')
    sftp.close()

    run_ssh(
        ssh,
        f'cd {REMOTE} && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && PYTHONPATH={REMOTE} .venv/bin/pytest -q',
    )
    run_ssh(ssh, f'install -m 644 {REMOTE}/deploy/cttelfix-bot.service /etc/systemd/system/cttelfix-bot.service')
    run_ssh(ssh, 'systemctl daemon-reload')
    run_ssh(ssh, 'systemctl enable cttelfix-bot')
    run_ssh(ssh, 'systemctl restart cttelfix-bot')
    _, stdout, _ = ssh.exec_command('systemctl is-active cttelfix-bot')
    print(stdout.read().decode(), end='')
    ssh.close()


if __name__ == '__main__':
    main()
