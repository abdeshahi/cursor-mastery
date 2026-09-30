export interface PlanTerms {
  id: number;
  months: number;
  creditPercent: string;
  servicePercent: string;
  monthlyInstallmentFactor: string;
  minimumLoan: bigint;
  maximumLoan: bigint | null;
  isActive: boolean;
}

export interface InstallmentResult {
  planId: number;
  months: number;
  cashPriceToman: bigint;
  cashPriceRial: bigint;
  requiredLoan: bigint;
  credit: bigint;
  digitalService: bigint;
  monthlyInstallment: bigint;
  totalRepayment: bigint;
  minimumLoan: bigint;
  maximumLoan: bigint | null;
  eligible: boolean;
}

export interface PlanPatch {
  creditPercent?: string;
  servicePercent?: string;
  monthlyInstallmentFactor?: string;
  minimumLoan?: bigint;
  maximumLoan?: bigint | null;
  isActive?: boolean;
}

export interface CalculationRecord extends InstallmentResult {
  userId?: number;
  fundingSource: string;
}
