import type { Telegraf } from 'telegraf';
import {
  exportFilename,
  type ExportAudience,
} from '../services/export-service.js';
import {
  renderCustomerResult,
  renderStoreResult,
} from '../utils/result-formatter.js';
import type { HandlerDependencies } from './helpers.js';
import { askForMode } from './user-flow.js';

function parseExportAudience(value: string | undefined): ExportAudience | null {
  return value === 'store' || value === 'customer' ? value : null;
}

export function registerResultActions(bot: Telegraf, dependencies: HandlerDependencies): void {
  bot.action('result:new', async (ctx) => {
    await ctx.answerCbQuery();
    await askForMode(ctx);
  });

  bot.action('result:copy', async (ctx) => {
    await ctx.answerCbQuery();
    if (ctx.session.lastResult === undefined) {
      await ctx.reply('نتیجه‌ای در نشست فعلی وجود ندارد.');
      return;
    }

    await ctx.reply(renderStoreResult(ctx.session.lastResult, false));
    await ctx.reply(renderCustomerResult(ctx.session.lastResult, false));
  });

  bot.action(/^export:(store|customer):(pdf|png|xlsx)$/, async (ctx) => {
    const audience = parseExportAudience(ctx.match[1]);
    const kind = ctx.match[2];
    if (audience === null || kind === undefined) {
      await ctx.answerCbQuery('درخواست نامعتبر است.');
      return;
    }

    await ctx.answerCbQuery('در حال ساخت فایل…');
    const result = ctx.session.lastResult;
    if (result === undefined) {
      await ctx.reply('نتیجه‌ای در نشست فعلی وجود ندارد.');
      return;
    }

    if (kind === 'png') {
      const source = await dependencies.exports.createPng(result, audience);
      await ctx.replyWithPhoto({ source, filename: exportFilename(audience, 'png') });
      return;
    }

    if (kind === 'pdf') {
      const source = await dependencies.exports.createPdf(result, audience);
      await ctx.replyWithDocument({ source, filename: exportFilename(audience, 'pdf') });
      return;
    }

    const source = await dependencies.exports.createXlsx(result, audience);
    await ctx.replyWithDocument({ source, filename: exportFilename(audience, 'xlsx') });
  });
}
