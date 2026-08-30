import { z } from 'zod';

const envSchema = z.object({
  BOT_TOKEN: z.string().min(1),
  CHANNEL_ID: z.string().min(1),
  ADMIN_ID: z.coerce.number().int().positive().optional(),
  TELEGRAM_PROXY: z.string().optional(),
  OPENAI_API_KEY: z.string().min(1),
  OPENAI_BASE_URL: z.string().url().default('https://api.openai.com/v1'),
  OPENAI_MODEL: z.string().default('gpt-4o-mini'),
  FEED_URLS: z.string().optional(),
  POLL_CRON: z.string().default('*/30 * * * *'),
  POLL_ON_START: z
    .string()
    .optional()
    .transform((value) => value !== 'false'),
  MAX_POSTS_PER_RUN: z.coerce.number().int().positive().max(20).default(5),
  DATA_DIR: z.string().default('./data'),
  PORT: z.coerce.number().int().positive().default(3002),
  LOG_LEVEL: z.enum(['error', 'warn', 'info', 'debug']).default('info'),
});

export type Env = z.infer<typeof envSchema>;

export function loadEnv(): Env {
  return envSchema.parse(process.env);
}

export function parseFeedUrls(raw: string | undefined): string[] {
  if (raw === undefined || raw.trim() === '') {
    return [];
  }

  return raw
    .split(',')
    .map((url) => url.trim())
    .filter((url) => url.length > 0);
}
