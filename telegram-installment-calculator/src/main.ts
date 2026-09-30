import { PrismaClient } from '@prisma/client';

import { registerBotCommands } from './bot/commands.js';
import { createBot, createBotDependencies } from './bot/create-bot.js';
import { STORE_NAME_SETTING_KEY } from './services/admin-service.js';
import { loadEnvironment } from './config/env.js';
import { createLogger } from './config/logger.js';

async function ensureDefaultSettings(db: PrismaClient): Promise<void> {
  await db.setting.upsert({
    where: { key: STORE_NAME_SETTING_KEY },
    create: { key: STORE_NAME_SETTING_KEY, value: 'CTTEL' },
    update: {},
  });
}

async function main(): Promise<void> {
  const env = loadEnvironment();
  const logger = createLogger(env);
  const db = new PrismaClient();
  await ensureDefaultSettings(db);
  const dependencies = createBotDependencies(db, env.ADMIN_TELEGRAM_ID, logger);
  const bot = createBot(env, dependencies, logger);

  logger.info('bot.starting');
  await registerBotCommands(bot);
  await bot.launch();

  const shutdown = async (signal: string) => {
    logger.info('bot.stopping', { signal });
    bot.stop(signal);
    await db.$disconnect();
  };

  process.once('SIGINT', () => {
    void shutdown('SIGINT');
  });
  process.once('SIGTERM', () => {
    void shutdown('SIGTERM');
  });
}

main().catch((error: unknown) => {
  console.error(error);
  process.exit(1);
});
