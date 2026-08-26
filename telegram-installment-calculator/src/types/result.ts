import type { InstallmentResult } from './calculator.js';

export type FundingSource = 'bank-melli' | 'bank-saman' | 'blubank';

export type CalculationMode = 'cash-price' | 'installment-capacity';

export interface CalculationResult {
  mode: CalculationMode;
  cashPriceToman?: bigint;
  storeDepositToman?: bigint;
  installmentCapacityRial?: bigint;
  fundingSource: FundingSource;
  createdAt: Date;
  plans: InstallmentResult[];
}

export const FUNDING_SOURCE_LABELS: Record<FundingSource, string> = {
  'bank-melli': 'بانک ملی',
  'bank-saman': 'بانک سامان',
  blubank: 'بلوبانک',
};
