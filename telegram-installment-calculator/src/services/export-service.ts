import ExcelJS from 'exceljs';
import { PDFDocument } from 'pdf-lib';
import type { CalculationResult } from '../types/result.js';
import { FUNDING_SOURCE_LABELS } from '../types/result.js';
import type { InstallmentResult } from '../types/calculator.js';
import { renderExportCardPng, renderExportLetterheadPages } from '../utils/export-image.js';
import { formatJalali } from '../utils/jalali.js';
import { rialToToman } from '../utils/persian.js';
import {
  exportCardLines,
  type ExportAudience,
} from '../utils/result-formatter.js';
import { calculateStoreDepositFromCredit, storeDepositTomanFromCreditRial } from '../utils/store-deposit.js';

export type { ExportAudience };

function storeDepositForPlan(result: CalculationResult, plan: InstallmentResult): bigint {
  if (result.storeDepositToman !== undefined) {
    return result.storeDepositToman;
  }

  return storeDepositTomanFromCreditRial(plan.credit);
}

function inputSummaryLabel(result: CalculationResult): string {
  if (result.mode === 'installment-capacity') {
    return 'توان پرداخت قسط (تومان)';
  }

  return 'مبلغ واریز به فروشگاه (تومان)';
}

function inputSummaryValue(result: CalculationResult): string {
  if (result.mode === 'installment-capacity') {
    return result.installmentCapacityRial === undefined
      ? ''
      : rialToToman(result.installmentCapacityRial).toString();
  }

  return (result.storeDepositToman ?? result.cashPriceToman)?.toString() ?? '';
}

async function createPdfFromPngPages(pages: Buffer[]): Promise<Buffer> {
  const document = await PDFDocument.create();

  for (const png of pages) {
    const image = await document.embedPng(png);
    const page = document.addPage([595.28, 841.89]);
    const scale = Math.min(535 / image.width, 781 / image.height);

    page.drawImage(image, {
      x: (595.28 - image.width * scale) / 2,
      y: 841.89 - image.height * scale - 30,
      width: image.width * scale,
      height: image.height * scale,
    });
  }

  return Buffer.from(await document.save());
}

function renderCardOptions(result: CalculationResult, audience: ExportAudience) {
  return {
    lines: exportCardLines(result, audience),
    createdAt: result.createdAt,
  };
}

function buildStoreXlsx(result: CalculationResult): ExcelJS.Workbook {
  const workbook = new ExcelJS.Workbook();
  workbook.creator = 'CTTEL Installment Calculator';
  workbook.created = result.createdAt;

  const sheet = workbook.addWorksheet('فروشگاه', {
    views: [{ rightToLeft: true }],
  });

  sheet.columns = [
    { header: 'مدت (ماه)', key: 'months', width: 14 },
    { header: 'وضعیت', key: 'eligible', width: 14 },
    { header: 'وام موردنیاز (تومان)', key: 'loan', width: 24 },
    { header: 'اعتبار خرید (تومان)', key: 'credit', width: 24 },
    { header: 'کسر ۱۰٪ (تومان)', key: 'deduction', width: 24 },
    { header: 'واریز به فروشگاه (تومان)', key: 'deposit', width: 28 },
    { header: 'خدمات دیجیتال (تومان)', key: 'service', width: 24 },
    { header: 'قسط ماهانه (تومان)', key: 'installment', width: 24 },
    { header: 'مجموع بازپرداخت (تومان)', key: 'total', width: 28 },
    { header: 'حداقل وام (تومان)', key: 'minimum', width: 24 },
    { header: 'حداکثر وام (تومان)', key: 'maximum', width: 24 },
  ];

  sheet.addRow([inputSummaryLabel(result), inputSummaryValue(result)]);
  sheet.addRow(['منبع تأمین', FUNDING_SOURCE_LABELS[result.fundingSource]]);
  sheet.addRow(['تاریخ', formatJalali(result.createdAt, false)]);
  sheet.addRow([]);

  for (const plan of result.plans) {
    const storeDeposit = plan.eligible
      ? calculateStoreDepositFromCredit(plan.credit)
      : { deductionRial: 0n, depositRial: 0n };

    sheet.addRow({
      months: plan.months,
      eligible: plan.eligible ? 'مجاز' : 'غیرمجاز',
      loan: rialToToman(plan.requiredLoan).toString(),
      credit: rialToToman(plan.credit).toString(),
      deduction: plan.eligible ? rialToToman(storeDeposit.deductionRial).toString() : '',
      deposit: plan.eligible ? rialToToman(storeDeposit.depositRial).toString() : '',
      service: rialToToman(plan.digitalService).toString(),
      installment: rialToToman(plan.monthlyInstallment).toString(),
      total: rialToToman(plan.totalRepayment).toString(),
      minimum: rialToToman(plan.minimumLoan).toString(),
      maximum: plan.maximumLoan === null ? 'نامحدود' : rialToToman(plan.maximumLoan).toString(),
    });
  }

  sheet.getRow(1).font = { bold: true };
  sheet.eachRow((row) => {
    row.alignment = { horizontal: 'right', vertical: 'middle' };
  });

  return workbook;
}

function buildCustomerXlsx(result: CalculationResult): ExcelJS.Workbook {
  const workbook = new ExcelJS.Workbook();
  workbook.creator = 'CTTEL Installment Calculator';
  workbook.created = result.createdAt;

  const sheet = workbook.addWorksheet('مشتری', {
    views: [{ rightToLeft: true }],
  });

  sheet.columns = [
    { header: 'مدت (ماه)', key: 'months', width: 14 },
    { header: 'قیمت نقدی کالا (تومان)', key: 'price', width: 28 },
    { header: 'قسط ماهانه (تومان)', key: 'installment', width: 24 },
  ];

  sheet.addRow(['منبع تأمین', FUNDING_SOURCE_LABELS[result.fundingSource]]);
  sheet.addRow(['تاریخ', formatJalali(result.createdAt, false)]);
  sheet.addRow([]);

  const eligiblePlans = result.plans.filter((plan) => plan.eligible);
  if (eligiblePlans.length === 0) {
    sheet.addRow(['وضعیت', 'هیچ طرح مجازی برای این مبلغ پیدا نشد.']);
  }

  for (const plan of eligiblePlans) {
    sheet.addRow({
      months: plan.months,
      price: storeDepositForPlan(result, plan).toString(),
      installment: rialToToman(plan.monthlyInstallment).toString(),
    });
  }

  sheet.getRow(1).font = { bold: true };
  sheet.eachRow((row) => {
    row.alignment = { horizontal: 'right', vertical: 'middle' };
  });

  return workbook;
}

export interface ExportService {
  createPng(result: CalculationResult, audience: ExportAudience): Promise<Buffer>;
  createPdf(result: CalculationResult, audience: ExportAudience): Promise<Buffer>;
  createXlsx(result: CalculationResult, audience: ExportAudience): Promise<Buffer>;
}

export class MemoryExportService implements ExportService {
  async createPng(result: CalculationResult, audience: ExportAudience): Promise<Buffer> {
    return renderExportCardPng(renderCardOptions(result, audience));
  }

  async createPdf(result: CalculationResult, audience: ExportAudience): Promise<Buffer> {
    const pages = await renderExportLetterheadPages(renderCardOptions(result, audience));
    return createPdfFromPngPages(pages);
  }

  async createXlsx(result: CalculationResult, audience: ExportAudience): Promise<Buffer> {
    const workbook = audience === 'store' ? buildStoreXlsx(result) : buildCustomerXlsx(result);
    const bytes = await workbook.xlsx.writeBuffer();
    return Buffer.from(bytes);
  }
}

export function exportFilename(audience: ExportAudience, format: 'png' | 'pdf' | 'xlsx'): string {
  const prefix = audience === 'store' ? 'cttel-store' : 'cttel-customer';
  return `${prefix}.${format}`;
}
