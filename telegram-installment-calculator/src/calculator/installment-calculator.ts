import { Decimal } from 'decimal.js';
import type { InstallmentResult, PlanTerms } from '../types/calculator.js';
import type { FundingSource } from '../types/result.js';
import { MAX_SIGNED_64 } from '../utils/input-validation.js';
import { applyBankMelliEligibility } from './bank-melli-eligibility.js';

Decimal.set({ precision: 50, rounding: Decimal.ROUND_HALF_UP });

const RIAL_ROUNDING_UNIT = new Decimal(1_000);
const PERCENT = new Decimal(100);
const RIALS_PER_TOMAN = new Decimal(10);

export class RialStorageError extends RangeError {
  constructor(field: string) {
    super(`${field} exceeds signed 64-bit rial storage`);
    this.name = 'RialStorageError';
  }
}

function decimal(value: string | number | bigint | Decimal, field: string): Decimal {
  if (typeof value === 'string' && value.length > 128) {
    throw new RangeError(`${field} is too long`);
  }

  const result = new Decimal(value);
  if (!result.isFinite()) {
    throw new RangeError(`${field} must be finite`);
  }

  return result;
}

function positive(value: string | number | bigint, field: string): Decimal {
  const result = decimal(value, field);
  if (result.lessThanOrEqualTo(0)) {
    throw new RangeError(`${field} must be greater than zero`);
  }

  return result;
}

function validatePlan(plan: PlanTerms): void {
  if (!Number.isSafeInteger(plan.months) || plan.months <= 0) {
    throw new RangeError('plan.months must be a positive safe integer');
  }

  const creditPercent = decimal(plan.creditPercent, 'creditPercent');
  const servicePercent = decimal(plan.servicePercent, 'servicePercent');

  if (!creditPercent.isPositive() || creditPercent.greaterThan(PERCENT)) {
    throw new RangeError('creditPercent must be greater than 0 and at most 100');
  }

  if (servicePercent.isNegative() || !creditPercent.plus(servicePercent).equals(PERCENT)) {
    throw new RangeError('creditPercent and servicePercent must total 100');
  }

  if (!decimal(plan.monthlyInstallmentFactor, 'monthlyInstallmentFactor').isPositive()) {
    throw new RangeError('monthlyInstallmentFactor must be greater than zero');
  }

  const minimumLoan = decimal(plan.minimumLoan, 'minimumLoan');
  const maximumLoan =
    plan.maximumLoan === null ? null : decimal(plan.maximumLoan, 'maximumLoan');

  if (
    minimumLoan.isNegative() ||
    !minimumLoan.isInteger() ||
    minimumLoan.greaterThan(MAX_SIGNED_64)
  ) {
    throw new RangeError('minimumLoan must be a signed 64-bit non-negative integer');
  }

  if (
    maximumLoan !== null &&
    (!maximumLoan.isInteger() ||
      maximumLoan.greaterThan(MAX_SIGNED_64) ||
      maximumLoan.lessThan(minimumLoan))
  ) {
    throw new RangeError('maximumLoan cannot be less than minimumLoan');
  }
}

export function roundToNearestThousand(value: string | number | bigint | Decimal): bigint {
  const amount = decimal(value, 'value');
  return BigInt(
    amount
      .dividedBy(RIAL_ROUNDING_UNIT)
      .toDecimalPlaces(0, Decimal.ROUND_HALF_UP)
      .times(RIAL_ROUNDING_UNIT)
      .toFixed(0),
  );
}

export function isLoanEligible(calculatedLoan: bigint, plan: PlanTerms): boolean {
  validatePlan(plan);
  const loan = decimal(calculatedLoan, 'calculatedLoan');
  const meetsMinimum = loan.greaterThanOrEqualTo(plan.minimumLoan);
  const meetsMaximum =
    plan.maximumLoan === null ||
    loan.lessThanOrEqualTo(decimal(plan.maximumLoan, 'maximumLoan'));

  return meetsMinimum && meetsMaximum;
}

function assertStorableRial(value: bigint, field: string): bigint {
  if (value < 0n || value > MAX_SIGNED_64) {
    throw new RialStorageError(field);
  }

  return value;
}

function buildInstallmentResult(
  loan: Decimal,
  plan: PlanTerms,
  cashPriceToman: bigint,
): InstallmentResult {
  const creditRate = decimal(plan.creditPercent, 'creditPercent').dividedBy(PERCENT);
  const serviceRate = decimal(plan.servicePercent, 'servicePercent').dividedBy(PERCENT);
  const requiredLoan = roundToNearestThousand(loan);
  const monthlyInstallment = roundToNearestThousand(
    loan.times(decimal(plan.monthlyInstallmentFactor, 'monthlyInstallmentFactor')),
  );
  const totalRepayment = assertStorableRial(
    monthlyInstallment * BigInt(plan.months),
    'totalRepayment',
  );
  const roundedCashPriceRial = assertStorableRial(
    roundToNearestThousand(decimal(cashPriceToman, 'cashPriceToman').times(RIALS_PER_TOMAN)),
    'cashPriceRial',
  );
  const storableRequiredLoan = assertStorableRial(requiredLoan, 'requiredLoan');
  const credit = assertStorableRial(roundToNearestThousand(loan.times(creditRate)), 'credit');
  const digitalService = assertStorableRial(
    roundToNearestThousand(loan.times(serviceRate)),
    'digitalService',
  );

  assertStorableRial(monthlyInstallment, 'monthlyInstallment');

  return {
    planId: plan.id,
    months: plan.months,
    cashPriceToman,
    cashPriceRial: roundedCashPriceRial,
    requiredLoan: storableRequiredLoan,
    credit,
    digitalService,
    monthlyInstallment,
    totalRepayment,
    minimumLoan: BigInt(decimal(plan.minimumLoan, 'minimumLoan').toFixed(0)),
    maximumLoan:
      plan.maximumLoan === null
        ? null
        : BigInt(decimal(plan.maximumLoan, 'maximumLoan').toFixed(0)),
    eligible: isLoanEligible(requiredLoan, plan),
  };
}

export function calculateInstallment(
  cashPriceTomanInput: string | number | bigint,
  plan: PlanTerms,
): InstallmentResult {
  validatePlan(plan);

  const cashPriceToman = positive(cashPriceTomanInput, 'cashPriceToman');
  if (!cashPriceToman.isInteger()) {
    throw new RangeError('cashPriceToman must be an integer');
  }

  const cashPriceTomanValue = BigInt(cashPriceToman.toFixed(0));
  const loan = cashPriceToman.times(RIALS_PER_TOMAN).dividedBy(
    decimal(plan.creditPercent, 'creditPercent').dividedBy(PERCENT),
  );

  return buildInstallmentResult(loan, plan, cashPriceTomanValue);
}

export function calculateFromInstallmentCapacity(
  monthlyInstallmentInput: string | number | bigint,
  plan: PlanTerms,
): InstallmentResult {
  validatePlan(plan);

  const monthlyInstallment = positive(monthlyInstallmentInput, 'monthlyInstallment');
  if (!monthlyInstallment.isInteger()) {
    throw new RangeError('monthlyInstallment must be an integer');
  }

  const loan = monthlyInstallment.dividedBy(
    decimal(plan.monthlyInstallmentFactor, 'monthlyInstallmentFactor'),
  );
  const requiredLoan = roundToNearestThousand(loan);
  const creditRate = decimal(plan.creditPercent, 'creditPercent').dividedBy(PERCENT);
  const credit = roundToNearestThousand(decimal(requiredLoan, 'requiredLoan').times(creditRate));
  const cashPriceToman = credit / 10n;

  if (cashPriceToman <= 0n) {
    throw new RangeError('installment capacity is too low for this plan');
  }

  return buildInstallmentResult(loan, plan, cashPriceToman);
}

export function calculateAllPlansFromInstallmentCapacity(
  monthlyInstallment: string | number | bigint,
  plans: PlanTerms[],
  fundingSource?: FundingSource,
): InstallmentResult[] {
  const results = plans.map((plan) => calculateFromInstallmentCapacity(monthlyInstallment, plan));

  return fundingSource === 'bank-melli' ? applyBankMelliEligibility(results) : results;
}

export function calculateAllPlans(
  cashPriceToman: string | number | bigint,
  plans: PlanTerms[],
  fundingSource?: FundingSource,
): InstallmentResult[] {
  const results = plans.map((plan) => calculateInstallment(cashPriceToman, plan));

  return fundingSource === 'bank-melli' ? applyBankMelliEligibility(results) : results;
}
