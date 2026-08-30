#!/usr/bin/env python3
"""Deploy cttel-news-bot to VPS via SFTP."""

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
REMOTE = '/opt/cttel-news-bot'
EXCLUDE = {'node_modules', 'dist', '.env', '.git', 'data'}


def should_sync(root: str, name: str) -> bool:
    rel = os.path.relpath(os.path.join(root, name), LOCAL)
    return rel.split(os.sep)[0] not in EXCLUDE


def ensure_remote_dir(sftp: paramiko.SFTPClient, remote_dir: str) -> None:
    parts = remote_dir.split('/')
    current = ''
    for part in parts:
        if not part:
            continue
        current = f'{current}/{part}' if current else part
        try:
            sftp.stat(current)
        except FileNotFoundError:
            sftp.mkdir(current)


def upload_tree() -> None:
    if not PASSWORD:
        raise SystemExit('Set VPS_PASSWORD environment variable')

    transport = paramiko.Transport((HOST, 22))
    transport.connect(username=USER, password=PASSWORD)
    sftp = paramiko.SFTPClient.from_transport(transport)

    uploaded = 0
    for root, dirs, files in os.walk(LOCAL):
        dirs[:] = [entry for entry in dirs if should_sync(root, entry)]
        rel = os.path.relpath(root, LOCAL)
        remote_dir = REMOTE if rel == '.' else f"{REMOTE}/{rel.replace(os.sep, '/')}"
        ensure_remote_dir(sftp, remote_dir)

        for filename in files:
            if not should_sync(root, filename):
                continue
            local_path = os.path.join(root, filename)
            remote_path = f'{remote_dir}/{filename}'
            sftp.put(local_path, remote_path)
            uploaded += 1

    sftp.close()
    transport.close()
    print(f'Uploaded {uploaded} files to {REMOTE}')


def run_remote(commands: list[str]) -> None:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    for command in commands:
        print(f'\n>>> {command}')
        _, stdout, stderr = client.exec_command(command, get_pty=True)
        out = stdout.read().decode()
        err = stderr.read().decode()
        if out:
            print(out)
        if err:
            print(err, file=sys.stderr)

    client.close()


def main() -> None:
    upload_tree()
    run_remote(
        [
            f'cd {REMOTE} && corepack enable && pnpm install && pnpm build && pnpm test',
            'install -m 644 /opt/cttel-news-bot/deploy/cttel-news-bot.service /etc/systemd/system/cttel-news-bot.service',
            'systemctl daemon-reload',
            'systemctl enable cttel-news-bot',
            'systemctl restart cttel-news-bot',
            'systemctl is-active cttel-news-bot',
        ]
    )


if __name__ == '__main__':
    main()
