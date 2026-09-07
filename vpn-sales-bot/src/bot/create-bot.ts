import { Telegraf } from 'telegraf';
import { message } from 'telegraf/filters';

import type { Environment } from '../config/env.js';
import { isAdmin } from '../config/env.js';
import type { Logger } from '../config/logger.js';
import type { SalesService } from '../services/sales-service.js';
import { parseCallback } from '../utils/callback.js';
import {
  adminReviewKeyboard,
  mainMenu,
  orderKeyboard,
  plansKeyboard,
  renewalPlansKeyboard,
  servicesKeyboard,
} from './keyboards.js';
import {
  BLOCKED,
  CANCELLED,
  NO_PLANS,
  NO_SERVICES,
  NOT_ADMIN,
  RECEIPT_SAVED,
  REJECTED_CUSTOMER,
  START_TEXT,
  supportText,
  UNKNOWN_CALLBACK,
} from './messages.js';
import { createTelegramAgent } from './telegram-agent.js';

export interface BotDependencies {
  env: Environment;
  logger: Logger;
  sales: SalesService;
}

export function createBot(deps: BotDependencies): Telegraf {
  const agent = createTelegramAgent(deps.env.TELEGRAM_PROXY);
  const bot = new Telegraf(deps.env.BOT_TOKEN, agent === undefined ? {} : { telegram: { agent } });

  bot.start(async (ctx) => {
    const from = ctx.from;
    if (from === undefined) {
      return;
    }
    const user = await deps.sales.ensureUser(from);
    if (user.blocked) {
      await ctx.reply(BLOCKED);
      return;
    }
    await ctx.reply(START_TEXT, mainMenu());
  });

  bot.action(/.*/, async (ctx) => {
    const data = 'data' in ctx.callbackQuery ? ctx.callbackQuery.data : undefined;
    const from = ctx.from;
    if (data === undefined || from === undefined) {
      await ctx.answerCbQuery();
      return;
    }

    const action = parseCallback(data);
    if (action === null) {
      deps.logger.warn('callback.invalid', { data, telegramId: from.id });
      await ctx.answerCbQuery(UNKNOWN_CALLBACK, { show_alert: true });
      return;
    }

    const user = await deps.sales.ensureUser(from);
    if (user.blocked && action.type !== 'approve' && action.type !== 'reject') {
      await ctx.answerCbQuery(BLOCKED, { show_alert: true });
      return;
    }

    try {
      switch (action.type) {
        case 'menu':
          await ctx.answerCbQuery();
          await handleMenu(ctx, action.page, deps, user.id);
          return;
        case 'plan': {
          const created = await deps.sales.createPurchase(user.id, action.planId);
          await ctx.answerCbQuery('سفارش ساخته شد');
          await ctx.reply(deps.sales.paymentInstructions(created.plan, created.orderId), {
            parse_mode: 'HTML',
            ...orderKeyboard(created.orderId),
          });
          return;
        }
        case 'renew': {
          const plans = await deps.sales.activePlans();
          await ctx.answerCbQuery();
          if (plans.length === 0) {
            await ctx.reply(NO_PLANS);
            return;
          }
          await ctx.reply('پلن تمدید را انتخاب کنید:', renewalPlansKeyboard(action.subscriptionId, plans));
          return;
        }
        case 'renewPlan': {
          const created = await deps.sales.createRenewal(user.id, action.subscriptionId, action.planId);
          await ctx.answerCbQuery('سفارش تمدید ساخته شد');
          await ctx.reply(deps.sales.paymentInstructions(created.plan, created.orderId), {
            parse_mode: 'HTML',
            ...orderKeyboard(created.orderId),
          });
          return;
        }
        case 'cancel': {
          const cancelled = await deps.sales.cancelOrder(user.id, action.orderId);
          await ctx.answerCbQuery(cancelled ? CANCELLED : 'این سفارش قابل لغو نیست.');
          if (cancelled) {
            await ctx.reply(CANCELLED, mainMenu());
          }
          return;
        }
        case 'approve': {
          if (!isAdmin(deps.env, from.id)) {
            await ctx.answerCbQuery(NOT_ADMIN, { show_alert: true });
            return;
          }
          const result = await deps.sales.approve(action.paymentId, from.id);
          await ctx.answerCbQuery(result.message, { show_alert: true });
          return;
        }
        case 'reject': {
          if (!isAdmin(deps.env, from.id)) {
            await ctx.answerCbQuery(NOT_ADMIN, { show_alert: true });
            return;
          }
          const result = await deps.sales.reject(action.paymentId, from.id);
          await ctx.answerCbQuery(result.message, { show_alert: true });
          if (result.customerTelegramId !== undefined && !result.duplicate) {
            await bot.telegram.sendMessage(result.customerTelegramId, REJECTED_CUSTOMER).catch((error: unknown) => {
              deps.logger.error('customer.reject.notify.failed', {
                error: error instanceof Error ? error.message : String(error),
              });
            });
          }
          return;
        }
      }
    } catch (error) {
      const messageText = error instanceof Error ? error.message : String(error);
      deps.logger.error('callback.failed', { data, messageText });
      if (messageText === 'PLAN_NOT_FOUND' || messageText === 'SUBSCRIPTION_NOT_FOUND') {
        await ctx.answerCbQuery('این مورد در دسترس نیست.', { show_alert: true });
        return;
      }
      await ctx.answerCbQuery('خطا رخ داد. دوباره تلاش کنید.', { show_alert: true });
    }
  });

  bot.on(message('photo'), async (ctx) => {
    const photo = ctx.message.photo.at(-1);
    if (photo === undefined) {
      return;
    }
    await handleReceipt(ctx, deps, ctx.from.id, photo.file_id, 'photo', bot);
  });

  bot.on(message('document'), async (ctx) => {
    const mime = ctx.message.document.mime_type ?? '';
    if (!mime.startsWith('image/')) {
      await ctx.reply('لطفاً تصویر رسید را به‌صورت عکس یا فایل تصویر بفرستید.');
      return;
    }
    await handleReceipt(ctx, deps, ctx.from.id, ctx.message.document.file_id, 'document', bot);
  });

  bot.catch(async (error, ctx) => {
    deps.logger.error('telegram.update.failed', {
      error: error instanceof Error ? error.message : String(error),
      updateId: ctx.update.update_id,
    });
    await ctx.reply('خطایی رخ داد. /start را بزنید.').catch(() => undefined);
  });

  return bot;
}

async function handleMenu(
  ctx: { reply: (text: string, extra?: object) => Promise<unknown> },
  page: 'home' | 'buy' | 'services' | 'renew' | 'support',
  deps: BotDependencies,
  userId: number,
): Promise<void> {
  if (page === 'home') {
    await ctx.reply(START_TEXT, mainMenu());
    return;
  }
  if (page === 'buy') {
    const plans = await deps.sales.activePlans();
    if (plans.length === 0) {
      await ctx.reply(NO_PLANS, mainMenu());
      return;
    }
    await ctx.reply('یک پلن انتخاب کنید. قیمت‌ها از دیتابیس خوانده می‌شوند:', plansKeyboard(plans));
    return;
  }
  if (page === 'services' || page === 'renew') {
    const items = await deps.sales.myServices(userId);
    if (items.length === 0) {
      await ctx.reply(NO_SERVICES, mainMenu());
      return;
    }
    for (const item of items) {
      await ctx.reply(deps.sales.serviceText(item), {
        parse_mode: 'HTML',
        ...servicesKeyboard([item]),
      });
    }
    return;
  }
  await ctx.reply(supportText(deps.env.SUPPORT_USERNAME, deps.env.SUPPORT_MESSAGE), mainMenu());
}

async function handleReceipt(
  ctx: { reply: (text: string) => Promise<unknown> },
  deps: BotDependencies,
  telegramId: number,
  fileId: string,
  kind: 'photo' | 'document',
  bot: Telegraf,
): Promise<void> {
  const result = await deps.sales.saveReceipt({ telegramId, fileId, kind });
  if ('error' in result) {
    await ctx.reply(result.error);
    return;
  }

  await ctx.reply(RECEIPT_SAVED);

  const caption = deps.sales.adminReceiptCaption(result);
  const extra = { caption, parse_mode: 'HTML' as const, ...adminReviewKeyboard(result.paymentId) };

  for (const adminId of deps.env.ADMIN_TELEGRAM_IDS) {
    try {
      if (kind === 'photo') {
        await bot.telegram.sendPhoto(adminId, fileId, extra);
      } else {
        await bot.telegram.sendDocument(adminId, fileId, extra);
      }
    } catch (error) {
      deps.logger.error('admin.receipt.notify.failed', {
        adminId,
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }
}
