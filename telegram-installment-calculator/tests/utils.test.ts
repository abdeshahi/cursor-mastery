import { describe, expect, it } from 'vitest';
import { formatThousands, formatRialAsToman, parsePersianInteger, toEnglishDigits, toPersianDigits } from '../src/utils/persian.js';
import { rtl, stripDirectionalIsolates } from '../src/utils/rtl.js';
import { UserInputError, parseBoundedUnsignedInteger } from '../src/utils/input-validation.js';
import {
  customerResultMessageChunks,
  storeResultMessageChunks,
} from '../src/utils/result-formatter.js';
import type { CalculationResult } from '../src/types/result.js';

describe('persian utilities', () => {
  it('converts digits both ways', () => {
    expect(toPersianDigits('89500000')).toBe('۸۹۵۰۰۰۰۰');
    expect(toEnglishDigits('۸۹۵۰۰۰۰۰')).toBe('89500000');
  });

  it('formats thousands with Persian separators', () => {
    expect(formatThousands('89500000')).toBe('۸۹٬۵۰۰٬۰۰۰');
  });

  it('formats rial amounts as toman', () => {
    expect(formatRialAsToman(895_000_000n)).toBe('۸۹٬۵۰۰٬۰۰۰ تومان');
  });

  it('parses Persian integers', () => {
    expect(parsePersianInteger('۱۲۳۴')).toBe(1234n);
  });
});

describe('rtl utilities', () => {
  it('wraps and strips directional isolates', () => {
    const wrapped = rtl('متن');
    expect(wrapped).toContain('متن');
    expect(stripDirectionalIsolates(wrapped)).toBe('متن');
  });
});

describe('input validation', () => {
  it('parses bounded unsigned integers', () => {
    expect(parseBoundedUnsignedInteger('89,500,000', 1_000_000_000n, { allowZero: false, label: 'قیمت' })).toBe(
      89_500_000n,
    );
  });

  it('rejects zero when not allowed', () => {
    expect(() =>
      parseBoundedUnsignedInteger('0', 1_000_000_000n, { allowZero: false, label: 'قیمت' }),
    ).toThrow(UserInputError);
  });
});

describe('result formatter', () => {
  it('chunks store and customer results for Telegram', () => {
    const result: CalculationResult = {
      mode: 'cash-price',
      storeDepositToman: 80_550_000n,
      cashPriceToman: 89_500_000n,
      fundingSource: 'bank-melli',
      createdAt: new Date('2026-08-06T00:00:00.000Z'),
      plans: [
        {
          planId: 1,
          months: 6,
          cashPriceToman: 89_500_000n,
          cashPriceRial: 895_000_000n,
          requiredLoan: 972_826_000n,
          credit: 895_000_000n,
          digitalService: 77_826_000n,
          monthlyInstallment: 173_184_000n,
          totalRepayment: 1_039_104_000n,
          minimumLoan: 0n,
          maximumLoan: null,
          eligible: true,
        },
      ],
    };

    const storeChunks = storeResultMessageChunks(result);
    const customerChunks = customerResultMessageChunks(result);

    expect(storeChunks.length).toBeGreaterThan(0);
    expect(customerChunks.length).toBeGreaterThan(0);
    expect(storeChunks[0]).toContain('نسخه فروشگاه');
    expect(customerChunks[0]).toContain('نسخه مشتری');
    expect(storeChunks[0]).toContain('<b>');
    expect(customerChunks[0]).toContain('قیمت نقدی کالا');
  });
});
