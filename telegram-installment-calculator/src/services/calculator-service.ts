import type { CalculationRecord, InstallmentResult } from '../types/calculator.js';
import type { CalculationResult, CalculationMode, FundingSource } from '../types/result.js';
import {
  calculateAllPlans,
  calculateAllPlansFromInstallmentCapacity,
  calculateInstallment,
} from '../calculator/installment-calculator.js';
import type { CalculationRepository, PlanRepository } from '../database/repositories.js';

export class CalculatorService {
  constructor(
    private readonly plans: PlanRepository,
    private readonly calculations: CalculationRepository,
  ) {}

  async calculatePlans(
    cashPriceToman: string | number | bigint,
    fundingSource: FundingSource,
  ): Promise<InstallmentResult[]> {
    const plans = await this.plans.findActive();
    return calculateAllPlans(cashPriceToman, plans, fundingSource);
  }

  async calculatePlansFromInstallmentCapacity(
    monthlyInstallmentRial: string | number | bigint,
    fundingSource: FundingSource,
  ): Promise<InstallmentResult[]> {
    const plans = await this.plans.findActive();
    return calculateAllPlansFromInstallmentCapacity(monthlyInstallmentRial, plans, fundingSource);
  }

  async calculatePersistAll(
    cashPriceToman: string | number | bigint,
    fundingSource: FundingSource,
    userId: number,
    storeDepositToman?: string | number | bigint,
  ): Promise<CalculationResult> {
    const plans = await this.calculatePlans(cashPriceToman, fundingSource);
    return this.persistResult('cash-price', plans, fundingSource, userId, {
      cashPriceToman: BigInt(String(cashPriceToman)),
      ...(storeDepositToman === undefined
        ? {}
        : { storeDepositToman: BigInt(String(storeDepositToman)) }),
    });
  }

  async calculatePersistAllFromInstallmentCapacity(
    monthlyInstallmentRial: string | number | bigint,
    fundingSource: FundingSource,
    userId: number,
  ): Promise<CalculationResult> {
    const plans = await this.calculatePlansFromInstallmentCapacity(
      monthlyInstallmentRial,
      fundingSource,
    );
    return this.persistResult('installment-capacity', plans, fundingSource, userId, {
      installmentCapacityRial: BigInt(String(monthlyInstallmentRial)),
    });
  }

  private async persistResult(
    mode: CalculationMode,
    plans: InstallmentResult[],
    fundingSource: FundingSource,
    userId: number,
    input: Pick<CalculationResult, 'cashPriceToman' | 'storeDepositToman' | 'installmentCapacityRial'>,
  ): Promise<CalculationResult> {
    if (plans.length === 0) {
      throw new Error('No active installment plans are configured');
    }

    await this.calculations.createMany(
      plans.map((plan) => ({ ...plan, userId, fundingSource })),
    );

    return {
      mode,
      ...(input.cashPriceToman === undefined ? {} : { cashPriceToman: input.cashPriceToman }),
      ...(input.storeDepositToman === undefined ? {} : { storeDepositToman: input.storeDepositToman }),
      ...(input.installmentCapacityRial === undefined
        ? {}
        : { installmentCapacityRial: input.installmentCapacityRial }),
      fundingSource,
      createdAt: new Date(),
      plans,
    };
  }

  async calculateAndSave(
    cashPriceToman: string | number | bigint,
    planId: number,
    fundingSource: FundingSource,
    userId?: number,
  ): Promise<InstallmentResult> {
    const plan = await this.plans.findById(planId);
    if (plan === null) {
      throw new Error(`Plan ${String(planId)} was not found`);
    }

    const activePlans = await this.plans.findActive();
    const results =
      fundingSource === 'bank-melli'
        ? calculateAllPlans(cashPriceToman, activePlans, fundingSource)
        : [calculateInstallment(cashPriceToman, plan)];
    const result = results.find((entry) => entry.planId === planId) ?? calculateInstallment(cashPriceToman, plan);
    const record: CalculationRecord = {
      ...result,
      ...(userId === undefined ? {} : { userId }),
      fundingSource,
    };

    await this.calculations.create(record);
    return result;
  }
}
