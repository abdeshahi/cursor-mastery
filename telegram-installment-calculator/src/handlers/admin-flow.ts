import type { Context, Telegraf } from 'telegraf';
import { initialSession, type AdminField } from '../bot/context.js';
import { adminFieldsKeyboard, adminPlansKeyboard } from '../keyboards/keyboards.js';
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

async function showAdminPlans(ctx: Context, dependencies: HandlerDependencies): Promise<void> {
  const plans = await dependencies.admin.listPlans();
  await ctx.reply('طرح موردنظر برای مدیریت را انتخاب کنید:', adminPlansKeyboard(plans));
}

export function registerAdminFlow(bot: Telegraf, dependencies: HandlerDependencies): void {
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

    await showAdminPlans(ctx, dependencies);
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

    await ctx.reply(
      [
        `طرح ${toPersianDigits(plan.months)} ماهه`,
        `اعتبار: ${String(plan.creditPercent)}٪`,
        `خدمات: ${String(plan.servicePercent)}٪`,
        `ضریب: ${String(plan.monthlyInstallmentFactor)}`,
        `حداقل: ${formatRialAsToman(plan.minimumLoan)}`,
        `حداکثر: ${plan.maximumLoan === null ? 'نامحدود' : formatRialAsToman(plan.maximumLoan)}`,
        `وضعیت: ${plan.isActive ? 'فعال' : 'غیرفعال'}`,
      ].join('\n'),
      adminFieldsKeyboard(plan),
    );
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
    await ctx.reply(`وضعیت طرح ${toPersianDigits(updated.months)} ماهه تغییر کرد.`);
  });
}

export async function handleAdminText(
  ctx: Context,
  text: string,
  dependencies: HandlerDependencies,
): Promise<boolean> {
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
  } catch (error) {
    if (!(error instanceof UserInputError)) {
      throw error;
    }

    await ctx.reply(`${error.message}\nلطفاً مقدار صحیح را دوباره وارد کنید.`);
  }

  return true;
}
