import type { CalculationResult } from '../types/result.js';
import { FUNDING_SOURCE_LABELS } from '../types/result.js';
import type { InstallmentResult } from '../types/calculator.js';
import { formatJalali } from './jalali.js';
import { formatRialAsToman, formatToman, toPersianDigits } from './persian.js';
import { storeDepositResultLines } from './store-deposit-lines.js';
import { storeDepositTomanFromCreditRial } from './store-deposit.js';
import { boldHtml } from './telegram-format.js';
import { rtl } from './rtl.js';

export const TELEGRAM_MESSAGE_LIMIT = 4096;
export const TELEGRAM_SHARE_URL_LIMIT = 2000;

const separator = '────────────────';
const DIRECTIONAL_WRAPPER_LENGTH = 2;

type FormatStyle = 'plain' | 'html';

function money(value: bigint): string {
  return formatRialAsToman(value);
}

function storeDepositAmount(result: CalculationResult, plan?: InstallmentResult): bigint | undefined {
  if (result.storeDepositToman !== undefined) {
    return result.storeDepositToman;
  }

  if (plan !== undefined) {
    return storeDepositTomanFromCreditRial(plan.credit);
  }

  return undefined;
}

function formatStoreDepositLabel(
  amount: bigint,
  style: FormatStyle,
  prefix = 'مبلغ واریز به فروشگاه',
): string {
  const formatted = formatToman(amount);
  return style === 'html'
    ? `${prefix}: ${boldHtml(formatted)}`
    : `${prefix}: ${formatted}`;
}

function storeResultSummary(result: CalculationResult, style: FormatStyle): string {
  if (result.mode === 'installment-capacity' && result.installmentCapacityRial !== undefined) {
    return `توان پرداخت قسط: ${money(result.installmentCapacityRial)}`;
  }

  const storeDeposit = storeDepositAmount(result);
  if (storeDeposit !== undefined) {
    return formatStoreDepositLabel(storeDeposit, style);
  }

  if (result.cashPriceToman !== undefined) {
    return `قیمت نقدی: ${formatToman(result.cashPriceToman)}`;
  }

  return 'محاسبه اقساط CTTEL';
}

function renderStorePlan(
  plan: InstallmentResult,
  mode: CalculationResult['mode'],
  style: FormatStyle,
): string {
  if (!plan.eligible) {
    return [
      `❌ ${toPersianDigits(plan.months)} ماهه`,
      `وام موردنیاز: ${money(plan.requiredLoan)}`,
      `حداقل وام موردنیاز: ${money(plan.minimumLoan)}`,
      ...(plan.maximumLoan === null ? [] : [`حداکثر وام: ${money(plan.maximumLoan)}`]),
      mode === 'installment-capacity'
        ? 'با این توان پرداخت قسط، این طرح در دسترس نیست.'
        : 'این طرح برای مبلغ واردشده در دسترس نیست.',
    ].join('\n');
  }

  const maxStoreDeposit =
    mode === 'installment-capacity'
      ? formatStoreDepositLabel(
          storeDepositTomanFromCreditRial(plan.credit),
          style,
          'حداکثر واریز به فروشگاه',
        )
      : null;

  return [
    `✅ ${toPersianDigits(plan.months)} ماهه`,
    ...(maxStoreDeposit === null ? [] : [maxStoreDeposit]),
    `وام موردنیاز: ${money(plan.requiredLoan)}`,
    `اعتبار خرید: ${money(plan.credit)}`,
    ...storeDepositResultLines(plan.credit, style === 'html'),
    `خدمات دیجیتال: ${money(plan.digitalService)}`,
    `قسط ماهانه: ${money(plan.monthlyInstallment)}`,
    `مجموع بازپرداخت: ${money(plan.totalRepayment)}`,
  ].join('\n');
}

function renderCustomerPlan(plan: InstallmentResult, result: CalculationResult, style: FormatStyle): string | null {
  if (!plan.eligible) {
    return null;
  }

  const storeDeposit = storeDepositAmount(result, plan);
  if (storeDeposit === undefined) {
    return null;
  }

  const priceLine =
    style === 'html'
      ? `قیمت نقدی کالا: ${boldHtml(formatToman(storeDeposit))}`
      : `قیمت نقدی کالا: ${formatToman(storeDeposit)}`;

  return [
    `✅ ${toPersianDigits(plan.months)} ماهه`,
    priceLine,
    `قسط ماهانه: ${money(plan.monthlyInstallment)}`,
  ].join('\n');
}

function storeResultBlocks(result: CalculationResult, style: FormatStyle): string[] {
  return [
    [
      '🏪 نسخه فروشگاه',
      '📱 محاسبه اقساط CTTEL',
      storeResultSummary(result, style),
      `منبع تأمین: ${FUNDING_SOURCE_LABELS[result.fundingSource]}`,
      `تاریخ: ${formatJalali(result.createdAt)}`,
    ].join('\n'),
    ...result.plans.map((plan) => renderStorePlan(plan, result.mode, style)),
  ];
}

function customerResultBlocks(result: CalculationResult, style: FormatStyle): string[] {
  const plans = result.plans
    .map((plan) => renderCustomerPlan(plan, result, style))
    .filter((block): block is string => block !== null);

  if (plans.length === 0) {
    return ['👤 نسخه مشتری', 'هیچ طرح مجازی برای این مبلغ پیدا نشد.'];
  }

  return ['👤 نسخه مشتری', ...plans];
}

function chunkBlocks(blocks: string[], isolated: boolean): string[] {
  const maximumBodyLength = TELEGRAM_MESSAGE_LIMIT - (isolated ? DIRECTIONAL_WRAPPER_LENGTH : 0);
  const chunks: string[] = [];
  let current = '';

  for (const block of blocks) {
    if (block.length > maximumBodyLength) {
      throw new RangeError('A result block exceeds the Telegram message limit');
    }

    const candidate = current === '' ? block : `${current}\n${separator}\n${block}`;
    if (candidate.length > maximumBodyLength) {
      chunks.push(isolated ? rtl(current) : current);
      current = block;
    } else {
      current = candidate;
    }
  }

  if (current !== '') {
    chunks.push(isolated ? rtl(current) : current);
  }

  return chunks;
}

export type ExportAudience = 'store' | 'customer';

export function exportCardLines(result: CalculationResult, audience: ExportAudience): string[] {
  const blocks =
    audience === 'store'
      ? storeResultBlocks(result, 'plain')
      : customerResultBlocks(result, 'plain');

  return blocks.flatMap((block) => block.split('\n'));
}

export function storeResultMessageChunks(result: CalculationResult, isolated = true): string[] {
  return chunkBlocks(storeResultBlocks(result, 'html'), isolated);
}

export function customerResultMessageChunks(result: CalculationResult, isolated = true): string[] {
  return chunkBlocks(customerResultBlocks(result, 'html'), isolated);
}

export function renderStoreResult(result: CalculationResult, isolated = true): string {
  const body = storeResultBlocks(result, 'plain').join(`\n${separator}\n`);
  return isolated ? rtl(body) : body;
}

export function renderCustomerResult(result: CalculationResult, isolated = true): string {
  const body = customerResultBlocks(result, 'plain').join(`\n${separator}\n`);
  return isolated ? rtl(body) : body;
}

export function renderResult(result: CalculationResult, isolated = true): string {
  return renderStoreResult(result, isolated);
}

export function resultMessageChunks(result: CalculationResult, isolated = true): string[] {
  return storeResultMessageChunks(result, isolated);
}

export function createShareUrl(result: CalculationResult): string {
  const fullText = renderStoreResult(result, false);
  const concise =
    result.mode === 'installment-capacity' && result.installmentCapacityRial !== undefined
      ? [
          'محاسبه اقساط CTTEL',
          `توان پرداخت قسط: ${formatRialAsToman(result.installmentCapacityRial)}`,
          ...result.plans
            .filter((plan) => plan.eligible)
            .map(
              (plan) =>
                `${toPersianDigits(plan.months)} ماهه: ${formatToman(storeDepositTomanFromCreditRial(plan.credit))}`,
            ),
        ].join('\n')
      : [
          'محاسبه اقساط CTTEL',
          ...(result.storeDepositToman === undefined
            ? result.cashPriceToman === undefined
              ? []
              : [`مبلغ واریز به فروشگاه: ${formatToman(result.cashPriceToman)}`]
            : [`مبلغ واریز به فروشگاه: ${formatToman(result.storeDepositToman)}`]),
          ...result.plans
            .filter((plan) => plan.eligible)
            .map(
              (plan) =>
                `${toPersianDigits(plan.months)} ماهه: ${formatRialAsToman(plan.monthlyInstallment)}`,
            ),
        ].join('\n');

  const build = (text: string) =>
    `https://t.me/share/url?url=${encodeURIComponent('https://t.me/')}&text=${encodeURIComponent(text)}`;

  const fullUrl = build(fullText);
  if (fullUrl.length <= TELEGRAM_SHARE_URL_LIMIT) {
    return fullUrl;
  }

  const conciseUrl = build(concise);
  if (conciseUrl.length <= TELEGRAM_SHARE_URL_LIMIT) {
    return conciseUrl;
  }

  const fallback =
    result.mode === 'installment-capacity' && result.installmentCapacityRial !== undefined
      ? `محاسبه اقساط CTTEL — ${formatRialAsToman(result.installmentCapacityRial)}`
      : result.storeDepositToman === undefined
        ? result.cashPriceToman === undefined
          ? 'محاسبه اقساط CTTEL'
          : `محاسبه اقساط CTTEL — ${formatToman(result.cashPriceToman)}`
        : `محاسبه اقساط CTTEL — ${formatToman(result.storeDepositToman)}`;

  return build(fallback);
}
