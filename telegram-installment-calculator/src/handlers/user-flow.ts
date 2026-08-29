import type { Context, Telegraf } from 'telegraf';
import { initialSession } from '../bot/context.js';
import { RialStorageError } from '../calculator/installment-calculator.js';
import { fundingKeyboard, modeKeyboard, resultKeyboard } from '../keyboards/keyboards.js';
import { UserInputError } from '../utils/input-validation.js';
import {
  customerResultMessageChunks,
  storeResultMessageChunks,
} from '../utils/result-formatter.js';
import { TELEGRAM_HTML_PARSE_MODE } from '../utils/telegram-format.js';
import type { HandlerDependencies } from './helpers.js';
import {
  fundingSourceFromCode,
  parseStoreDepositInput,
  parseInstallmentCapacityInput,
} from './helpers.js';

export async function askForMode(ctx: Context): Promise<void> {
  ctx.session = { step: 'mode' };
  await ctx.reply('نوع محاسبه را انتخاب کنید:', modeKeyboard());
}

export async function askForPrice(ctx: Context): Promise<void> {
  ctx.session = { ...ctx.session, step: 'cash-price', calculationMode: 'cash-price' };
  await ctx.reply('مبلغ واریز به حساب فروشگاه را به‌صورت عدد صحیح و به تومان وارد کنید.\nمثال: 80550000');
}

export async function askForInstallmentCapacity(ctx: Context): Promise<void> {
  ctx.session = {
    ...ctx.session,
    step: 'installment-capacity',
    calculationMode: 'installment-capacity',
  };
  await ctx.reply(
    'حداکثر قسط ماهانه‌ای که می‌توانید پرداخت کنید را به‌صورت عدد صحیح و به تومان وارد کنید.\nمثال: 17318300',
  );
}

async function deliverResult(ctx: Context, _dependencies: HandlerDependencies): Promise<void> {
  const result = ctx.session.lastResult!;

  for (const chunk of storeResultMessageChunks(result)) {
    await ctx.reply(chunk, TELEGRAM_HTML_PARSE_MODE);
  }

  const customerChunks = customerResultMessageChunks(result);
  for (const [index, chunk] of customerChunks.entries()) {
    await ctx.reply(
      chunk,
      index === customerChunks.length - 1
        ? { ...TELEGRAM_HTML_PARSE_MODE, ...resultKeyboard(result) }
        : TELEGRAM_HTML_PARSE_MODE,
    );
  }
}

export function registerUserFlow(bot: Telegraf, dependencies: HandlerDependencies): void {
  bot.start(async (ctx) => {
    await ctx.reply('به محاسبه‌گر اقساط CTTEL خوش آمدید.');
    await askForMode(ctx);
  });

  bot.help(async (ctx) => {
    await ctx.reply(
      [
        'راهنما:',
        '۱. نوع محاسبه را انتخاب کنید:',
        '   • مبلغ واریز فروشگاه → محاسبه قسط از روی مبلغ واریزی فروشگاه',
        '   • توان پرداخت قسط → محاسبه حداکثر واریز فروشگاه از روی قسط ماهانه',
        '۲. مبلغ را وارد کنید.',
        '۳. منبع تأمین را انتخاب کنید.',
        '۴. نتیجه همه طرح‌های فعال نمایش داده می‌شود.',
        '',
        '/cancel لغو عملیات',
        '/admin مدیریت طرح‌ها (ویژه مدیر)',
      ].join('\n'),
    );
  });

  bot.command('cancel', async (ctx) => {
    ctx.session = initialSession();
    await ctx.reply('عملیات لغو شد. برای شروع دوباره /start را بزنید.');
  });

  bot.action(/^mode:(cash|installment)$/, async (ctx) => {
    await ctx.answerCbQuery();
    if (ctx.match[1] === 'cash') {
      await askForPrice(ctx);
      return;
    }

    await askForInstallmentCapacity(ctx);
  });

  bot.action(/^fund:(melli|saman|blu)$/, async (ctx) => {
    await ctx.answerCbQuery();

    const source = fundingSourceFromCode(ctx.match[1] ?? '');
    const mode = ctx.session.calculationMode ?? 'cash-price';
    const cashPrice = ctx.session.cashPriceToman;
    const storeDeposit = ctx.session.storeDepositToman;
    const installmentCapacity = ctx.session.installmentCapacityRial;

    if (source === null) {
      await ctx.reply('نشست منقضی شده است؛ لطفاً /start را بزنید.');
      return;
    }

    if (mode === 'cash-price' && (cashPrice === undefined || storeDeposit === undefined)) {
      await ctx.reply('نشست منقضی شده است؛ لطفاً /start را بزنید.');
      return;
    }

    if (mode === 'installment-capacity' && installmentCapacity === undefined) {
      await ctx.reply('نشست منقضی شده است؛ لطفاً /start را بزنید.');
      return;
    }

    const from = ctx.from;
    const user = await dependencies.users.upsert({
      telegramId: BigInt(from.id),
      firstName: from.first_name,
      ...(from.last_name === undefined ? {} : { lastName: from.last_name }),
      ...(from.username === undefined ? {} : { username: from.username }),
    });

    try {
      const result =
        mode === 'installment-capacity'
          ? await dependencies.calculator.calculatePersistAllFromInstallmentCapacity(
              installmentCapacity!,
              source,
              user.id,
            )
          : await dependencies.calculator.calculatePersistAll(
              cashPrice!,
              source,
              user.id,
              storeDeposit!,
            );

      ctx.session = { step: 'idle', lastResult: result };
      await deliverResult(ctx, dependencies);
    } catch (error) {
      if (!(error instanceof RialStorageError)) {
        throw error;
      }

      await ctx.reply(
        'مبلغ واردشده با ضرایب طرح‌ها از محدوده قابل ذخیره بیشتر می‌شود. مبلغ کمتری وارد کنید.',
      );

      if (mode === 'installment-capacity') {
        await askForInstallmentCapacity(ctx);
      } else {
        await askForPrice(ctx);
      }
    }
  });
}

export async function handleUserText(ctx: Context, text: string): Promise<void> {
  if (ctx.session.step === 'cash-price') {
    try {
      const { storeDepositToman, cashPriceToman } = parseStoreDepositInput(text);
      ctx.session = {
        ...ctx.session,
        step: 'funding',
        calculationMode: 'cash-price',
        storeDepositToman,
        cashPriceToman,
      };
      await ctx.reply('منبع تأمین مالی را انتخاب کنید:', fundingKeyboard());
    } catch (error) {
      if (!(error instanceof UserInputError)) {
        throw error;
      }

      await ctx.reply(error.message);
    }

    return;
  }

  if (ctx.session.step === 'installment-capacity') {
    try {
      const installmentCapacity = parseInstallmentCapacityInput(text);
      ctx.session = {
        ...ctx.session,
        step: 'funding',
        calculationMode: 'installment-capacity',
        installmentCapacityRial: installmentCapacity,
      };
      await ctx.reply('منبع تأمین مالی را انتخاب کنید:', fundingKeyboard());
    } catch (error) {
      if (!(error instanceof UserInputError)) {
        throw error;
      }

      await ctx.reply(error.message);
    }

    return;
  }

  await ctx.reply('برای شروع محاسبه /start را بزنید.');
}
