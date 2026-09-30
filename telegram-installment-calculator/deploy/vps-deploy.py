#!/usr/bin/env python3
"""Deploy telegram-installment-calculator to VPS via SFTP."""

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
REMOTE = '/opt/cttel-installment-bot'
EXCLUDE = {'node_modules', 'dist', '.env', '.git', 'data', 'coverage'}


def should_sync(root: str, name: str) -> bool:
    rel = os.path.relpath(os.path.join(root, name), LOCAL)
    return rel.split(os.sep)[0] not in EXCLUDE


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
        code = stdout.channel.recv_exit_status()
        if code != 0:
            client.close()
            raise SystemExit(f'Command failed ({code}): {command}')

    client.close()


def main() -> None:
    upload_tree()
    run_remote(
        [
            f'test -f {REMOTE}/.env || (echo "Missing {REMOTE}/.env — create it on the server first" && exit 1)',
            f'cd {REMOTE} && (command -v corepack >/dev/null && corepack enable || true)',
            f'cd {REMOTE} && pnpm install && pnpm exec prisma generate && pnpm build && pnpm test',
            f'cd {REMOTE} && pnpm exec prisma db push',
            f'install -m 644 {REMOTE}/deploy/cttel-installment-bot.service /etc/systemd/system/cttel-installment-bot.service',
            'systemctl daemon-reload',
            'systemctl enable cttel-installment-bot',
            'systemctl restart cttel-installment-bot',
            'systemctl is-active cttel-installment-bot',
        ]
    )


if __name__ == '__main__':
    main()
