import type { CalculationMode, CalculationResult } from '../types/result.js';

export type SessionStep =
  | 'idle'
  | 'mode'
  | 'cash-price'
  | 'installment-capacity'
  | 'funding'
  | 'admin-value';

export type AdminField =
  | 'creditPercent'
  | 'servicePercent'
  | 'monthlyInstallmentFactor'
  | 'minimumLoan'
  | 'maximumLoan';

export interface SessionData {
  step: SessionStep;
  calculationMode?: CalculationMode;
  cashPriceToman?: string;
  storeDepositToman?: string;
  installmentCapacityRial?: string;
  adminPlanId?: number;
  adminField?: AdminField;
  lastResult?: CalculationResult;
}

export function initialSession(): SessionData {
  return { step: 'idle' };
}
