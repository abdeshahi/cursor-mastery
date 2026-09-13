import { Markup } from 'telegraf';
import type { InlineKeyboardMarkup } from 'telegraf/types';
import type { PlanTerms } from '../types/calculator.js';
import type { CalculationResult } from '../types/result.js';
import { toPersianDigits } from '../utils/persian.js';
import { createShareUrl } from '../utils/result-formatter.js';

export function modeKeyboard(): Markup.Markup<InlineKeyboardMarkup> {
  return Markup.inlineKeyboard([
    [Markup.button.callback('💰 بر اساس مبلغ واریز فروشگاه', 'mode:cash')],
    [Markup.button.callback('📊 بر اساس توان پرداخت قسط', 'mode:installment')],
  ]);
}

export function fundingKeyboard(): Markup.Markup<InlineKeyboardMarkup> {
  return Markup.inlineKeyboard([
    [Markup.button.callback('بانک ملی', 'fund:melli')],
    [Markup.button.callback('بانک سامان', 'fund:saman')],
    [Markup.button.callback('بلوبانک', 'fund:blu')],
  ]);
}

export function resultKeyboard(result: CalculationResult): Markup.Markup<InlineKeyboardMarkup> {
  return Markup.inlineKeyboard([
    [
      Markup.button.callback('🔄 محاسبه جدید', 'result:new'),
      Markup.button.callback('📋 کپی نتیجه', 'result:copy'),
    ],
    [Markup.button.url('📤 اشتراک‌گذاری', createShareUrl(result))],
    [
      Markup.button.callback('🏪 PDF', 'export:store:pdf'),
      Markup.button.callback('👤 PDF', 'export:customer:pdf'),
    ],
    [
      Markup.button.callback('🏪 PNG', 'export:store:png'),
      Markup.button.callback('👤 PNG', 'export:customer:png'),
    ],
    [
      Markup.button.callback('🏪 XLSX', 'export:store:xlsx'),
      Markup.button.callback('👤 XLSX', 'export:customer:xlsx'),
    ],
  ]);
}

export function adminPlansKeyboard(plans: PlanTerms[]): Markup.Markup<InlineKeyboardMarkup> {
  return Markup.inlineKeyboard(
    plans.map((plan) => [
      Markup.button.callback(
        `${plan.isActive ? '✅' : '⛔'} طرح ${toPersianDigits(plan.months)} ماهه`,
        `admin:plan:${String(plan.id)}`,
      ),
    ]),
  );
}

export function adminFieldsKeyboard(plan: PlanTerms): Markup.Markup<InlineKeyboardMarkup> {
  return Markup.inlineKeyboard([
    [
      Markup.button.callback('درصد اعتبار', `admin:field:${String(plan.id)}:creditPercent`),
      Markup.button.callback('درصد خدمات', `admin:field:${String(plan.id)}:servicePercent`),
    ],
    [Markup.button.callback('ضریب قسط', `admin:field:${String(plan.id)}:monthlyInstallmentFactor`)],
    [
      Markup.button.callback('حداقل وام', `admin:field:${String(plan.id)}:minimumLoan`),
      Markup.button.callback('حداکثر وام', `admin:field:${String(plan.id)}:maximumLoan`),
    ],
    [
      Markup.button.callback(
        plan.isActive ? 'غیرفعال‌کردن' : 'فعال‌کردن',
        `admin:toggle:${String(plan.id)}`,
      ),
      Markup.button.callback('بازگشت', 'admin:list'),
    ],
  ]);
}
