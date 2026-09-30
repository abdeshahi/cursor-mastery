import 'dotenv/config';

import { z } from 'zod';

function normalizeEnvString(value: string): string {
  const trimmed = value.trim();
  if (
    (trimmed.startsWith('"') && trimmed.endsWith('"')) ||
    (trimmed.startsWith("'") && trimmed.endsWith("'"))
  ) {
    return trimmed.slice(1, -1).trim();
  }

  return trimmed;
}

const envSchema = z
  .object({
    BOT_TOKEN: z.string().optional(),
    TELEGRAM_BOT_TOKEN: z.string().optional(),
    ADMIN_TELEGRAM_ID: z.string().optional(),
    ADMIN_TELEGRAM_IDS: z.string().optional(),
    DATABASE_URL: z.string().min(1),
    TELEGRAM_PROXY: z.string().optional(),
    LOG_LEVEL: z.enum(['error', 'warn', 'info', 'debug']).default('info'),
  })
  .transform((raw) => {
    const botToken = normalizeEnvString(raw.BOT_TOKEN ?? raw.TELEGRAM_BOT_TOKEN ?? '');
    const adminIds = normalizeEnvString(raw.ADMIN_TELEGRAM_IDS ?? raw.ADMIN_TELEGRAM_ID ?? '');

    if (botToken.length === 0) {
      throw new Error('BOT_TOKEN or TELEGRAM_BOT_TOKEN is required');
    }

    if (adminIds.length === 0) {
      throw new Error('ADMIN_TELEGRAM_ID or ADMIN_TELEGRAM_IDS is required');
    }

    return {
      BOT_TOKEN: botToken,
      ADMIN_TELEGRAM_ID: adminIds,
      DATABASE_URL: normalizeEnvString(raw.DATABASE_URL),
      TELEGRAM_PROXY:
        raw.TELEGRAM_PROXY === undefined ? undefined : normalizeEnvString(raw.TELEGRAM_PROXY),
      LOG_LEVEL: raw.LOG_LEVEL,
    };
  });

export type Environment = z.infer<typeof envSchema>;

export function loadEnvironment(source: NodeJS.ProcessEnv = process.env): Environment {
  return envSchema.parse(source);
}
