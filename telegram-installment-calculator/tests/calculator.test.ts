import { describe, expect, it } from 'vitest';
import {
  calculateAllPlans,
  calculateAllPlansFromInstallmentCapacity,
  calculateFromInstallmentCapacity,
  calculateInstallment,
  isLoanEligible,
  roundToNearestThousand,
} from '../src/calculator/installment-calculator.js';
import type { PlanTerms } from '../src/types/calculator.js';

const sixMonthPlan: PlanTerms = {
  id: 1,
  months: 6,
  creditPercent: '92',
  servicePercent: '8',
  monthlyInstallmentFactor: '0.17802',
  minimumLoan: 0n,
  maximumLoan: null,
  isActive: true,
};

const twelveMonthPlan: PlanTerms = {
  id: 2,
  months: 12,
  creditPercent: '87',
  servicePercent: '13',
  monthlyInstallmentFactor: '0.094076',
  minimumLoan: 500_000_000n,
  maximumLoan: null,
  isActive: true,
};

const eighteenMonthPlan: PlanTerms = {
  id: 3,
  months: 18,
  creditPercent: '83',
  servicePercent: '17',
  monthlyInstallmentFactor: '0.066214',
  minimumLoan: 1_000_000_000n,
  maximumLoan: 3_000_000_000n,
  isActive: true,
};

describe('roundToNearestThousand', () => {
  it('rounds half up to the nearest 1000 rial', () => {
    expect(roundToNearestThousand('972826086.956')).toBe(972_826_000n);
    expect(roundToNearestThousand('972826500')).toBe(972_827_000n);
    expect(roundToNearestThousand('972826499')).toBe(972_826_000n);
  });
});

describe('calculateInstallment', () => {
  it('calculates the 6-month plan for 89,500,000 toman', () => {
    const result = calculateInstallment(89_500_000n, sixMonthPlan);

    expect(result.cashPriceToman).toBe(89_500_000n);
    expect(result.cashPriceRial).toBe(895_000_000n);
    expect(result.requiredLoan).toBe(972_826_000n);
    expect(result.credit).toBe(895_000_000n);
    expect(result.digitalService).toBe(77_826_000n);
    expect(result.monthlyInstallment).toBe(173_183_000n);
    expect(result.totalRepayment).toBe(1_039_098_000n);
    expect(result.eligible).toBe(true);
  });

  it('marks longer plans ineligible when the required loan is below the minimum', () => {
    const result = calculateInstallment(40_000_000n, eighteenMonthPlan);

    expect(result.requiredLoan).toBeLessThan(1_000_000_000n);
    expect(result.eligible).toBe(false);
  });

  it('marks plans ineligible when the required loan exceeds the maximum', () => {
    const result = calculateInstallment(300_000_000n, {
      ...eighteenMonthPlan,
      maximumLoan: 3_000_000_000n,
    });

    expect(result.requiredLoan).toBeGreaterThan(3_000_000_000n);
    expect(result.eligible).toBe(false);
  });
});

describe('isLoanEligible', () => {
  it('accepts loans within configured bounds', () => {
    expect(isLoanEligible(600_000_000n, twelveMonthPlan)).toBe(true);
    expect(isLoanEligible(400_000_000n, twelveMonthPlan)).toBe(false);
  });
});

describe('calculateFromInstallmentCapacity', () => {
  it('derives the max cash price from a 6-month installment capacity', () => {
    const result = calculateFromInstallmentCapacity(173_183_000n, sixMonthPlan);

    expect(result.cashPriceToman).toBe(89_500_300n);
    expect(result.monthlyInstallment).toBe(173_183_000n);
    expect(result.requiredLoan).toBe(972_829_000n);
    expect(result.eligible).toBe(true);
  });

  it('round-trips forward monthly installments to at least the original cash price', () => {
    const forward = calculateInstallment(89_500_000n, sixMonthPlan);
    const reverse = calculateFromInstallmentCapacity(forward.monthlyInstallment, sixMonthPlan);

    expect(reverse.cashPriceToman).toBeGreaterThanOrEqual(89_500_000n);
    expect(reverse.monthlyInstallment).toBe(forward.monthlyInstallment);
  });

  it('marks plans ineligible when derived loan is below the minimum', () => {
    const result = calculateFromInstallmentCapacity(50_000_000n, eighteenMonthPlan);

    expect(result.eligible).toBe(false);
  });
});

describe('calculateAllPlansFromInstallmentCapacity', () => {
  it('returns one result per configured plan', () => {
    const results = calculateAllPlansFromInstallmentCapacity(173_183_000n, [
      sixMonthPlan,
      twelveMonthPlan,
      eighteenMonthPlan,
    ]);

    expect(results).toHaveLength(3);
    expect(results[0]?.cashPriceToman).toBe(89_500_300n);
  });
});

describe('calculateAllPlans', () => {
  it('returns one result per configured plan', () => {
    const results = calculateAllPlans(89_500_000n, [sixMonthPlan, twelveMonthPlan, eighteenMonthPlan]);

    expect(results).toHaveLength(3);
    expect(results.map((plan) => plan.months)).toEqual([6, 12, 18]);
  });
});
