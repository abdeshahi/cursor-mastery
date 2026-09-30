import { describe, expect, it } from 'vitest';
import {
  calculateStoreDepositFromCredit,
  cashPriceTomanFromStoreDepositToman,
} from '../src/utils/store-deposit.js';
import { storeDepositResultLines } from '../src/utils/store-deposit-lines.js';

describe('store deposit breakdown', () => {
  it('deducts 10% from purchase credit and returns the store deposit', () => {
    const creditRial = 895_000_000n;
    const { deductionRial, depositRial } = calculateStoreDepositFromCredit(creditRial);

    expect(deductionRial).toBe(89_500_000n);
    expect(depositRial).toBe(805_500_000n);
    expect(deductionRial + depositRial).toBe(creditRial);
  });

  it('converts store deposit input back to cash price for calculator', () => {
    expect(cashPriceTomanFromStoreDepositToman(80_550_000n)).toBe(89_500_000n);
  });

  it('renders store deposit result lines in toman', () => {
    const lines = storeDepositResultLines(895_000_000n);

    expect(lines).toEqual([
      'کسر ۱۰٪ از اعتبار خرید: ۸٬۹۵۰٬۰۰۰ تومان',
      'واریز به حساب فروشگاه: ۸۰٬۵۵۰٬۰۰۰ تومان',
    ]);
  });

  it('bolds store deposit in html mode', () => {
    const lines = storeDepositResultLines(895_000_000n, true);

    expect(lines[1]).toContain('<b>۸۰٬۵۵۰٬۰۰۰ تومان</b>');
  });
});
