import 'dotenv/config';

import { z } from 'zod';

const envSchema = z.object({
  BOT_TOKEN: z.string().min(1),
  ADMIN_TELEGRAM_ID: z.string().min(1),
  DATABASE_URL: z.string().min(1),
  TELEGRAM_PROXY: z.string().optional(),
  LOG_LEVEL: z.enum(['error', 'warn', 'info', 'debug']).default('info'),
});

export type Environment = z.infer<typeof envSchema>;

export function loadEnvironment(source: NodeJS.ProcessEnv = process.env): Environment {
  return envSchema.parse(source);
}
