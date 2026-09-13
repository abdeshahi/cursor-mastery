import { rialToToman } from '../utils/persian.js';
import type { InstallmentResult } from '../types/calculator.js';

const TEN_MILLION_TOMAN = 10_000_000n;
const FIFTY_MILLION_TOMAN = 50_000_000n;
const ONE_HUNDRED_MILLION_TOMAN = 100_000_000n;
const TWO_HUNDRED_MILLION_TOMAN = 200_000_000n;

const BANK_MELLI_ALLOWED_MONTHS: ReadonlyArray<readonly [bigint, readonly number[]]> = [
  [TWO_HUNDRED_MILLION_TOMAN, [18, 24, 36]],
  [ONE_HUNDRED_MILLION_TOMAN, [12, 18, 24]],
  [FIFTY_MILLION_TOMAN, [6, 12]],
  [TEN_MILLION_TOMAN, [6]],
] as const;

export function allowedBankMelliMonths(requiredLoanToman: bigint): readonly number[] {
  for (const [minimumLoanToman, months] of BANK_MELLI_ALLOWED_MONTHS) {
    if (requiredLoanToman >= minimumLoanToman) {
      return months;
    }
  }

  return [];
}

export function isBankMelliMonthAllowed(requiredLoanRial: bigint, months: number): boolean {
  const requiredLoanToman = rialToToman(requiredLoanRial);
  return allowedBankMelliMonths(requiredLoanToman).includes(months);
}

export function applyBankMelliEligibility(results: InstallmentResult[]): InstallmentResult[] {
  const referenceLoan =
    results.find((plan) => plan.months === 6)?.requiredLoan ??
    results.reduce(
      (minimum, plan) => (plan.requiredLoan < minimum ? plan.requiredLoan : minimum),
      results[0]?.requiredLoan ?? 0n,
    );

  const allowedMonths = allowedBankMelliMonths(rialToToman(referenceLoan));

  return results.map((plan) => ({
    ...plan,
    eligible: allowedMonths.includes(plan.months),
  }));
}

function isWithinLoanBounds(requiredLoan: bigint, plan: InstallmentResult): boolean {
  const meetsMinimum = requiredLoan >= plan.minimumLoan;
  const meetsMaximum = plan.maximumLoan === null || requiredLoan <= plan.maximumLoan;
  return meetsMinimum && meetsMaximum;
}

/** Uses each plan's own required loan for month-tier eligibility (installment-capacity mode). */
export function applyBankMelliPerPlanEligibility(results: InstallmentResult[]): InstallmentResult[] {
  return results.map((plan) => ({
    ...plan,
    eligible:
      isBankMelliMonthAllowed(plan.requiredLoan, plan.months) &&
      isWithinLoanBounds(plan.requiredLoan, plan),
  }));
}
