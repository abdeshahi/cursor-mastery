import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { MemoryExportService } from '../src/services/export-service.js';
import type { CalculationResult } from '../src/types/result.js';

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

const outputDir = process.argv[2] ?? path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../artifacts');
const exports = new MemoryExportService();

await fs.promises.mkdir(outputDir, { recursive: true });

const storePng = await exports.createPng(sampleResult, 'store');
const customerPng = await exports.createPng(sampleResult, 'customer');
const storePdf = await exports.createPdf(sampleResult, 'store');

await fs.promises.writeFile(path.join(outputDir, 'sample-store-letterhead.png'), storePng);
await fs.promises.writeFile(path.join(outputDir, 'sample-customer-letterhead.png'), customerPng);
await fs.promises.writeFile(path.join(outputDir, 'sample-store-letterhead.pdf'), storePdf);

console.log(`Wrote samples to ${outputDir}`);
