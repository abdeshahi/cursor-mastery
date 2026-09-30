import { describe, expect, it } from 'vitest';
import { MemoryExportService } from '../src/services/export-service.js';
import type { CalculationResult } from '../src/types/result.js';
import { exportCardLines } from '../src/utils/result-formatter.js';
import { renderExportCardPng, renderExportLetterheadPages } from '../src/utils/export-image.js';

const sampleResult: CalculationResult = {
  mode: 'cash-price',
  storeDepositToman: 80_550_000n,
  cashPriceToman: 89_500_000n,
  fundingSource: 'bank-melli',
  createdAt: new Date('2026-08-24T12:00:00.000Z'),
  plans: [
    {
      planId: 1,
      months: 6,
      cashPriceToman: 89_500_000n,
      cashPriceRial: 895_000_000n,
      requiredLoan: 972_826_000n,
      credit: 895_000_000n,
      digitalService: 77_826_000n,
      monthlyInstallment: 173_200_000n,
      totalRepayment: 1_039_200_000n,
      minimumLoan: 0n,
      maximumLoan: null,
      eligible: true,
    },
  ],
};

describe('export image rendering', () => {
  it('renders Persian PNG output with a valid PNG header on letterhead', async () => {
    const png = await renderExportCardPng({
      lines: ['محاسبه اقساط CTTEL', 'قیمت نقدی: ۸۹,۵۰۰,۰۰۰ تومان'],
      createdAt: sampleResult.createdAt,
    });

    expect(png.subarray(0, 8).equals(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]))).toBe(
      true,
    );
    expect(png.length).toBeGreaterThan(10_000);
  });

  it('builds separate store and customer card lines', () => {
    const storeLines = exportCardLines(sampleResult, 'store');
    const customerLines = exportCardLines(sampleResult, 'customer');

    expect(storeLines.some((line) => line.includes('نسخه فروشگاه'))).toBe(true);
    expect(customerLines.some((line) => line.includes('نسخه مشتری'))).toBe(true);
    expect(storeLines.some((line) => line.includes('اعتبار خرید'))).toBe(true);
    expect(customerLines.some((line) => line.includes('قیمت نقدی کالا'))).toBe(true);
    expect(customerLines.some((line) => line.includes('اعتبار خرید'))).toBe(false);
  });

  it(
    'creates separate PNG and PDF exports for store and customer',
    async () => {
    const exports = new MemoryExportService();

    const storePng = await exports.createPng(sampleResult, 'store');
    const customerPng = await exports.createPng(sampleResult, 'customer');
    const storePdf = await exports.createPdf(sampleResult, 'store');
    const customerPdf = await exports.createPdf(sampleResult, 'customer');
    const storeXlsx = await exports.createXlsx(sampleResult, 'store');
    const customerXlsx = await exports.createXlsx(sampleResult, 'customer');

    for (const png of [storePng, customerPng]) {
      expect(png.subarray(0, 8).equals(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]))).toBe(
        true,
      );
      expect(png.length).toBeGreaterThan(10_000);
    }

    for (const pdf of [storePdf, customerPdf]) {
      expect(pdf.subarray(0, 4).toString()).toBe('%PDF');
      expect(pdf.length).toBeGreaterThan(10_000);
    }

    expect(storeXlsx.length).toBeGreaterThan(1000);
    expect(customerXlsx.length).toBeGreaterThan(1000);
    expect(storeXlsx.equals(customerXlsx)).toBe(false);
    },
    20_000,
  );

  it('can paginate long exports across multiple letterhead pages', async () => {
    const lines = Array.from({ length: 40 }, (_, index) => `خط ${String(index + 1)}`);
    const pages = await renderExportLetterheadPages({ lines, createdAt: sampleResult.createdAt });

    expect(pages.length).toBeGreaterThan(1);
    expect(pages[0]?.length).toBeGreaterThan(10_000);
  });
});
