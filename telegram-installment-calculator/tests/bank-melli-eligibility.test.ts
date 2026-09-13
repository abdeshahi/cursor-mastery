import { describe, expect, it } from 'vitest';
import {
  allowedBankMelliMonths,
  isBankMelliMonthAllowed,
} from '../src/calculator/bank-melli-eligibility.js';
import {
  calculateAllPlans,
  calculateAllPlansFromInstallmentCapacity,
} from '../src/calculator/installment-calculator.js';
import type { PlanTerms } from '../src/types/calculator.js';

const plans: PlanTerms[] = [
  {
    id: 1,
    months: 6,
    creditPercent: '92',
    servicePercent: '8',
    monthlyInstallmentFactor: '0.17802',
    minimumLoan: 0n,
    maximumLoan: null,
    isActive: true,
  },
  {
    id: 2,
    months: 12,
    creditPercent: '87',
    servicePercent: '13',
    monthlyInstallmentFactor: '0.094076',
    minimumLoan: 500_000_000n,
    maximumLoan: null,
    isActive: true,
  },
  {
    id: 3,
    months: 18,
    creditPercent: '83',
    servicePercent: '17',
    monthlyInstallmentFactor: '0.066214',
    minimumLoan: 1_000_000_000n,
    maximumLoan: 3_000_000_000n,
    isActive: true,
  },
  {
    id: 4,
    months: 24,
    creditPercent: '80',
    servicePercent: '20',
    monthlyInstallmentFactor: '0.052373',
    minimumLoan: 1_000_000_000n,
    maximumLoan: 3_000_000_000n,
    isActive: true,
  },
  {
    id: 5,
    months: 36,
    creditPercent: '74',
    servicePercent: '26',
    monthlyInstallmentFactor: '0.0387095',
    minimumLoan: 1_000_000_000n,
    maximumLoan: 3_250_000_000n,
    isActive: true,
  },
];

describe('bank melli month tiers', () => {
  it('maps required loan ranges to allowed months', () => {
    expect(allowedBankMelliMonths(10_000_000n)).toEqual([6]);
    expect(allowedBankMelliMonths(49_999_999n)).toEqual([6]);
    expect(allowedBankMelliMonths(50_000_000n)).toEqual([6, 12]);
    expect(allowedBankMelliMonths(99_999_999n)).toEqual([6, 12]);
    expect(allowedBankMelliMonths(100_000_000n)).toEqual([12, 18, 24]);
    expect(allowedBankMelliMonths(199_999_999n)).toEqual([12, 18, 24]);
    expect(allowedBankMelliMonths(200_000_000n)).toEqual([18, 24, 36]);
    expect(allowedBankMelliMonths(9_999_999n)).toEqual([]);
  });

  it('checks month eligibility from required loan in rial', () => {
    expect(isBankMelliMonthAllowed(600_000_000n, 6)).toBe(true);
    expect(isBankMelliMonthAllowed(600_000_000n, 12)).toBe(true);
    expect(isBankMelliMonthAllowed(600_000_000n, 18)).toBe(false);
    expect(isBankMelliMonthAllowed(2_500_000_000n, 36)).toBe(true);
    expect(isBankMelliMonthAllowed(2_500_000_000n, 12)).toBe(false);
  });

  it('applies bank melli tiers when calculating all plans', () => {
    const results = calculateAllPlans(89_500_000n, plans, 'bank-melli');
    const eligibleMonths = results.filter((plan) => plan.eligible).map((plan) => plan.months);

    expect(eligibleMonths).toEqual([6, 12]);
  });

  it('allows long terms only for large bank melli loans', () => {
    const results = calculateAllPlans(250_000_000n, plans, 'bank-melli');
    const eligibleMonths = results.filter((plan) => plan.eligible).map((plan) => plan.months);

    expect(eligibleMonths).toEqual([18, 24, 36]);
  });

  it('matches Samin installment-capacity results using each plan loan tier', () => {
    const results = calculateAllPlansFromInstallmentCapacity(52_373_000n, plans, 'bank-melli');
    const eligibleMonths = results.filter((plan) => plan.eligible).map((plan) => plan.months);
    const twentyFourMonth = results.find((plan) => plan.months === 24);

    expect(eligibleMonths).toEqual([6, 12, 24]);
    expect(twentyFourMonth?.requiredLoan).toBe(1_000_000_000n);
    expect(twentyFourMonth?.credit).toBe(800_000_000n);
    expect(twentyFourMonth?.monthlyInstallment).toBe(52_373_000n);
    expect(twentyFourMonth?.cashPriceToman).toBe(80_000_000n);
  });
});
