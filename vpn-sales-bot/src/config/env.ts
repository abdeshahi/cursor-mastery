import 'dotenv/config';
import { z } from 'zod';

const jsonObject = z
  .string()
  .default('{}')
  .transform((value, ctx) => {
    try {
      const parsed: unknown = JSON.parse(value);
      if (parsed === null || typeof parsed !== 'object' || Array.isArray(parsed)) {
        ctx.addIssue({ code: 'custom', message: 'must be a JSON object' });
        return z.NEVER;
      }
      return parsed as Record<string, unknown>;
    } catch {
      ctx.addIssue({ code: 'custom', message: 'invalid JSON' });
      return z.NEVER;
    }
  });

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
  LOG_LEVEL: z.enum(['error', 'warn', 'info', 'debug']).default('info'),
  DATABASE_URL: z.string().min(1),
  HEALTH_HOST: z.string().default('127.0.0.1'),
  HEALTH_PORT: z.coerce.number().int().min(1).max(65_535).default(3010),
  BOT_TOKEN: z.string().min(1),
  ADMIN_TELEGRAM_IDS: z
    .string()
    .min(1)
    .transform((value, ctx) => {
      const ids = value
        .split(',')
        .map((part) => part.trim())
        .filter((part) => part.length > 0)
        .map((part) => Number(part));
      if (ids.length === 0 || ids.some((id) => !Number.isSafeInteger(id) || id <= 0)) {
        ctx.addIssue({
          code: 'custom',
          message: 'ADMIN_TELEGRAM_IDS must be comma-separated positive integers',
        });
        return z.NEVER;
      }
      return ids;
    }),
  TELEGRAM_PROXY: z.string().url().optional(),
  PAYMENT_CARD_NUMBER: z.string().min(1),
  PAYMENT_CARD_HOLDER: z.string().min(1),
  PAYMENT_BANK_NAME: z.string().default(''),
  PAYMENT_NOTE: z.string().default('پس از واریز، تصویر رسید را همین‌جا ارسال کنید.'),
  SUPPORT_USERNAME: z.string().default(''),
  SUPPORT_MESSAGE: z.string().default('برای پشتیبانی به ادمین پیام بدهید.'),
  MARZBAN_BASE_URL: z.string().url(),
  MARZBAN_USERNAME: z.string().min(1),
  MARZBAN_PASSWORD: z.string().min(1),
  MARZBAN_TIMEOUT_MS: z.coerce.number().int().positive().default(15_000),
  MARZBAN_INSECURE_TLS: z
    .enum(['true', 'false'])
    .default('false')
    .transform((value) => value === 'true'),
  MARZBAN_PROXIES: jsonObject,
  MARZBAN_INBOUNDS: jsonObject,
  MARZBAN_SUBSCRIPTION_URL_PREFIX: z.string().url().optional(),
  DEFAULT_NODE: z.string().default('node1'),
  NODE_2: z.string().optional(),
  CONNECTION_APPS: z
    .string()
    .default('v2rayNG (اندروید)، Streisand یا V2Box (آیفون)، v2rayN (ویندوز)'),
});

export type Environment = Readonly<z.infer<typeof envSchema>>;

export function loadEnvironment(source: NodeJS.ProcessEnv = process.env): Environment {
  const parsed = envSchema.safeParse(source);
  if (!parsed.success) {
    throw new Error(`Invalid environment configuration: ${z.prettifyError(parsed.error)}`);
  }
  return Object.freeze(parsed.data);
}

export function isAdmin(env: Environment, telegramId: number): boolean {
  return env.ADMIN_TELEGRAM_IDS.includes(telegramId);
}
