import { Telegraf, session } from 'telegraf';
import { message } from 'telegraf/filters';
import { HttpsProxyAgent } from 'https-proxy-agent';

import type { Environment } from '../config/env.js';
import type winston from 'winston';
import {
  PrismaCalculationRepository,
  PrismaPlanRepository,
  PrismaSettingRepository,
  PrismaUserRepository,
} from '../database/repositories.js';
import { handleAdminText, registerAdminFlow } from '../handlers/admin-flow.js';
import type { BotDependencies } from '../handlers/dependencies.js';
import { registerResultActions } from '../handlers/result-actions.js';
import { handleLegacyReplyMenuText, handleUserText, registerUserFlow } from '../handlers/user-flow.js';
import { AdminService } from '../services/admin-service.js';
import { CalculatorService } from '../services/calculator-service.js';
import { MemoryExportService } from '../services/export-service.js';
import { initialSession } from './context.js';
import type { BotContext } from './types.js';
import type { PrismaClient } from '@prisma/client';

function createTelegramAgent(proxy: string | undefined) {
  if (proxy === undefined || proxy.length === 0) {
    return undefined;
  }

  return new HttpsProxyAgent(proxy);
}

export function createBotDependencies(
  db: PrismaClient,
  adminId: string,
  logger: winston.Logger,
): BotDependencies {
  const plans = new PrismaPlanRepository(db);
  const settings = new PrismaSettingRepository(db);

  return {
    adminId,
    admin: new AdminService(plans, settings, logger),
    calculator: new CalculatorService(plans, new PrismaCalculationRepository(db)),
    users: new PrismaUserRepository(db),
    exports: new MemoryExportService(),
    settings,
  };
}

export function createBot(env: Environment, dependencies: BotDependencies, logger: winston.Logger): Telegraf<BotContext> {
  const agent = createTelegramAgent(env.TELEGRAM_PROXY);
  const bot = new Telegraf<BotContext>(env.BOT_TOKEN, agent === undefined ? {} : { telegram: { agent } });

  bot.use(session({ defaultSession: (): ReturnType<typeof initialSession> => initialSession() }));

  registerUserFlow(bot, dependencies);
  registerAdminFlow(bot, dependencies);
  registerResultActions(bot, dependencies);

  bot.on(message('text'), async (ctx) => {
    const text = ctx.message.text.trim();
    if (text.startsWith('/')) {
      return;
    }

    if (await handleAdminText(ctx, text, dependencies)) {
      return;
    }

    if (await handleLegacyReplyMenuText(ctx, text, dependencies)) {
      return;
    }

    await handleUserText(ctx, text);
  });

  bot.catch((error) => {
    logger.error('bot.unhandled_error', { error: String(error) });
  });

  return bot;
}
