import { formatRialAsToman } from './persian.js';
import { boldHtml } from './telegram-format.js';
import { calculateStoreDepositFromCredit } from './store-deposit.js';

export function storeDepositResultLines(creditRial: bigint, html = false): string[] {
  const { deductionRial, depositRial } = calculateStoreDepositFromCredit(creditRial);
  const depositAmount = formatRialAsToman(depositRial);

  return [
    `کسر ۱۰٪ از اعتبار خرید: ${formatRialAsToman(deductionRial)}`,
    html
      ? `واریز به حساب فروشگاه: ${boldHtml(depositAmount)}`
      : `واریز به حساب فروشگاه: ${depositAmount}`,
  ];
}
