import { Markup } from 'telegraf';
import { initialSession, type AdminField } from '../bot/context.js';
import type { BotContext } from '../bot/types.js';
import type { Telegraf } from 'telegraf';
import type { PlanTerms } from '../types/calculator.js';
import { adminFieldsKeyboard, adminMainKeyboard } from '../keyboards/keyboards.js';
import { formatRialAsToman, toPersianDigits } from '../utils/persian.js';
import { UserInputError } from '../utils/input-validation.js';
import type { HandlerDependencies } from './helpers.js';
import { isAdmin } from './helpers.js';

const fieldLabels: Record<AdminField, string> = {
  creditPercent: 'درصد اعتبار',
  servicePercent: 'درصد خدمات',
  monthlyInstallmentFactor: 'ضریب قسط ماهانه',
  minimumLoan: 'حداقل وام (تومان)',
  maximumLoan: 'حداکثر وام (تومان یا unlimited)',
};

function isEditableField(value: string): value is AdminField {
  return Object.hasOwn(fieldLabels, value);
}

function parsePlanId(value: string | undefined): number | null {
  if (value === undefined || value.length > 10) {
    return null;
  }

  const id = Number(value);
  return Number.isSafeInteger(id) && id > 0 ? id : null;
}

function formatPlanSummary(plan: PlanTerms): string {
  return [
    `طرح ${toPersianDigits(plan.months)} ماهه`,
    `اعتبار: ${String(plan.creditPercent)}٪`,
    `خدمات: ${String(plan.servicePercent)}٪`,
    `ضریب: ${String(plan.monthlyInstallmentFactor)}`,
    `حداقل: ${formatRialAsToman(plan.minimumLoan)}`,
    `حداکثر: ${plan.maximumLoan === null ? 'نامحدود' : formatRialAsToman(plan.maximumLoan)}`,
    `وضعیت: ${plan.isActive ? 'فعال' : 'غیرفعال'}`,
  ].join('\n');
}

async function replyPlanDetails(ctx: BotContext, plan: PlanTerms): Promise<void> {
  await ctx.reply(formatPlanSummary(plan), adminFieldsKeyboard(plan));
}

async function showAdminPlans(ctx: BotContext, dependencies: HandlerDependencies): Promise<void> {
  const plans = await dependencies.admin.listPlans();
  await ctx.reply('طرح موردنظر برای مدیریت را انتخاب کنید:', adminMainKeyboard(plans));
}

async function showAdminSettings(ctx: BotContext, dependencies: HandlerDependencies): Promise<void> {
  const storeName = await dependencies.admin.getStoreName();
  await ctx.reply(
    ['تنظیمات عمومی ربات:', `نام فروشگاه: ${storeName}`].join('\n'),
    Markup.inlineKeyboard([
      [Markup.button.callback('ویرایش نام فروشگاه', 'admin:setting:store_name')],
      [Markup.button.callback('بازگشت به طرح‌ها', 'admin:list')],
    ]),
  );
}

export function registerAdminFlow(bot: Telegraf<BotContext>, dependencies: HandlerDependencies): void {
  bot.command('admin', async (ctx) => {
    if (!isAdmin(ctx, dependencies.adminId)) {
      await ctx.reply('دسترسی به این بخش مجاز نیست.');
      return;
    }

    ctx.session = { step: 'idle' };
    await showAdminPlans(ctx, dependencies);
  });

  bot.action('admin:list', async (ctx) => {
    await ctx.answerCbQuery();
    if (!isAdmin(ctx, dependencies.adminId)) {
      return;
    }

    ctx.session = { step: 'idle' };
    await showAdminPlans(ctx, dependencies);
  });

  bot.action('admin:settings', async (ctx) => {
    await ctx.answerCbQuery();
    if (!isAdmin(ctx, dependencies.adminId)) {
      return;
    }

    ctx.session = { step: 'idle' };
    await showAdminSettings(ctx, dependencies);
  });

  bot.action('admin:setting:store_name', async (ctx) => {
    await ctx.answerCbQuery();
    if (!isAdmin(ctx, dependencies.adminId)) {
      return;
    }

    ctx.session = { step: 'admin-store-name' };
    await ctx.reply('نام جدید فروشگاه را وارد کنید (در پیام‌ها و خروجی‌ها نمایش داده می‌شود):');
  });

  bot.action(/^admin:plan:(\d+)$/, async (ctx) => {
    await ctx.answerCbQuery();
    if (!isAdmin(ctx, dependencies.adminId)) {
      return;
    }

    const planId = parsePlanId(ctx.match[1]);
    const plan =
      planId === null
        ? undefined
        : await dependencies.admin
            .listPlans()
            .then((plans) => plans.find(({ id }) => id === planId));

    if (plan === undefined) {
      await ctx.reply('طرح پیدا نشد.');
      return;
    }

    ctx.session = { step: 'idle' };
    await replyPlanDetails(ctx, plan);
  });

  bot.action(/^admin:field:(\d+):([A-Za-z]+)$/, async (ctx) => {
    await ctx.answerCbQuery();
    if (!isAdmin(ctx, dependencies.adminId)) {
      return;
    }

    const planId = parsePlanId(ctx.match[1]);
    const field = ctx.match[2];
    if (planId === null || field === undefined || !isEditableField(field)) {
      await ctx.reply('درخواست مدیریت نامعتبر است.');
      return;
    }

    ctx.session = { step: 'admin-value', adminPlanId: planId, adminField: field };
    await ctx.reply(`مقدار جدید «${fieldLabels[field]}» را وارد کنید:`);
  });

  bot.action(/^admin:toggle:(\d+)$/, async (ctx) => {
    await ctx.answerCbQuery();
    if (!isAdmin(ctx, dependencies.adminId)) {
      return;
    }

    const planId = parsePlanId(ctx.match[1]);
    if (planId === null) {
      await ctx.reply('شناسه طرح نامعتبر است.');
      return;
    }

    const updated = await dependencies.admin.toggleActive(String(ctx.from.id), planId);
    ctx.session = { step: 'idle' };
    await ctx.reply(`وضعیت طرح ${toPersianDigits(updated.months)} ماهه به «${updated.isActive ? 'فعال' : 'غیرفعال'}» تغییر کرد.`);
    await replyPlanDetails(ctx, updated);
  });
}

export async function handleAdminText(
  ctx: BotContext,
  text: string,
  dependencies: HandlerDependencies,
): Promise<boolean> {
  if (ctx.session.step === 'admin-store-name') {
    if (!isAdmin(ctx, dependencies.adminId)) {
      ctx.session = initialSession();
      return true;
    }

    try {
      const storeName = await dependencies.admin.setStoreName(String(ctx.from?.id), text);
      ctx.session = { step: 'idle' };
      await ctx.reply(`نام فروشگاه به «${storeName}» به‌روزرسانی شد.`);
      await showAdminSettings(ctx, dependencies);
    } catch (error) {
      if (!(error instanceof UserInputError)) {
        throw error;
      }

      await ctx.reply(`${error.message}\nلطفاً نام معتبر وارد کنید.`);
    }

    return true;
  }

  if (ctx.session.step !== 'admin-value') {
    return false;
  }

  if (
    !isAdmin(ctx, dependencies.adminId) ||
    ctx.session.adminPlanId === undefined ||
    ctx.session.adminField === undefined
  ) {
    ctx.session = initialSession();
    return true;
  }

  try {
    const updated = await dependencies.admin.updateField(
      String(ctx.from?.id),
      ctx.session.adminPlanId,
      ctx.session.adminField,
      text,
    );
    ctx.session = { step: 'idle' };
    await ctx.reply(`طرح ${toPersianDigits(updated.months)} ماهه با موفقیت به‌روزرسانی شد.`);
    await replyPlanDetails(ctx, updated);
  } catch (error) {
    if (!(error instanceof UserInputError)) {
      throw error;
    }

    await ctx.reply(`${error.message}\nلطفاً مقدار صحیح را دوباره وارد کنید.`);
  }

  return true;
}
