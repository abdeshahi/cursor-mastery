import { z } from 'zod';

const envSchema = z
  .object({
    BOT_TOKEN: z.string().min(1),
    CHANNEL_ID: z.string().min(1),
    ADMIN_ID: z.coerce.number().int().positive().optional(),
    TELEGRAM_PROXY: z.string().optional(),
    TRANSLATION_PROVIDER: z.enum(['google', 'openai']).default('openai'),
    OPENAI_API_KEY: z.string().optional(),
    OPENAI_BASE_URL: z.string().url().default('https://api.openai.com/v1'),
    OPENAI_MODEL: z.string().default('gpt-4o-mini'),
    FEED_URLS: z.string().optional(),
    POLL_CRON: z.string().default('*/30 * * * *'),
    POLL_ON_START: z
      .string()
      .optional()
      .transform((value) => value !== 'false'),
    MAX_POSTS_PER_RUN: z.coerce.number().int().positive().max(20).default(3),
    DATA_DIR: z.string().default('./data'),
    PORT: z.coerce.number().int().positive().default(3002),
    LOG_LEVEL: z.enum(['error', 'warn', 'info', 'debug']).default('info'),
  })
  .superRefine((value, context) => {
    if (value.TRANSLATION_PROVIDER === 'openai' && (value.OPENAI_API_KEY === undefined || value.OPENAI_API_KEY.trim() === '')) {
      context.addIssue({
        code: 'custom',
        message: 'OPENAI_API_KEY is required when TRANSLATION_PROVIDER=openai',
        path: ['OPENAI_API_KEY'],
      });
    }
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
