import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import type { PrismaClient } from '@prisma/client';
import type winston from 'winston';

import { STORE_NAME_SETTING_KEY } from '../services/admin-service.js';

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');

export function syncDatabaseSchema(logger: winston.Logger): void {
  const result = spawnSync('npx', ['prisma', 'db', 'push', '--skip-generate'], {
    cwd: projectRoot,
    env: process.env,
    encoding: 'utf-8',
  });

  if (result.status !== 0) {
    logger.error('database.push_failed', {
      status: result.status,
      stderr: result.stderr,
      stdout: result.stdout,
    });
    throw new Error('Failed to sync Prisma schema (prisma db push)');
  }
}

export async function ensureDefaultSettings(db: PrismaClient): Promise<void> {
  await db.setting.upsert({
    where: { key: STORE_NAME_SETTING_KEY },
    create: { key: STORE_NAME_SETTING_KEY, value: 'CTTEL' },
    update: {},
  });
}
