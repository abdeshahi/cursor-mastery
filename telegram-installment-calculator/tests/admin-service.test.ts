import { describe, expect, it } from 'vitest';
import winston from 'winston';
import type { PlanRepository, PrismaSettingRepository } from '../src/database/repositories.js';
import { AdminService, STORE_NAME_SETTING_KEY } from '../src/services/admin-service.js';
import type { PlanPatch, PlanTerms } from '../src/types/calculator.js';

class MemorySettingsRepository implements Pick<PrismaSettingRepository, 'get' | 'set'> {
  private readonly values = new Map<string, string>();

  get(key: string): Promise<string | null> {
    return Promise.resolve(this.values.get(key) ?? null);
  }

  async set(key: string, value: string): Promise<void> {
    this.values.set(key, value);
  }
}

class MemoryPlanRepository implements PlanRepository {
  private readonly plans: PlanTerms[];

  constructor(plans: PlanTerms[]) {
    this.plans = plans.map((plan) => ({ ...plan }));
  }

  findActive(): Promise<PlanTerms[]> {
    return Promise.resolve(this.plans.filter((plan) => plan.isActive));
  }

  findAll(): Promise<PlanTerms[]> {
    return Promise.resolve(this.plans.map((plan) => ({ ...plan })));
  }

  findById(id: number): Promise<PlanTerms | null> {
    const plan = this.plans.find((entry) => entry.id === id);
    return Promise.resolve(plan === undefined ? null : { ...plan });
  }

  async updateValidated(id: number, patch: PlanPatch): Promise<PlanTerms> {
    const index = this.plans.findIndex((entry) => entry.id === id);
    if (index === -1) {
      throw new Error('missing plan');
    }

    const current = this.plans[index]!;
    const updated = { ...current, ...patch };
    this.plans[index] = updated;
    return { ...updated };
  }
}

const logger = winston.createLogger({ silent: true, transports: [new winston.transports.Console()] });

const basePlan: PlanTerms = {
  id: 1,
  months: 6,
  creditPercent: '92',
  servicePercent: '8',
  monthlyInstallmentFactor: '0.17802',
  minimumLoan: 0n,
  maximumLoan: null,
  isActive: true,
};

describe('AdminService settings', () => {
  it('updates store name setting', async () => {
    const settings = new MemorySettingsRepository();
    const admin = new AdminService(new MemoryPlanRepository([basePlan]), settings, logger);

    expect(await admin.getStoreName()).toBe('CTTEL');
    await admin.setStoreName('admin-1', 'CTTEL Shop');
    expect(await admin.getStoreName()).toBe('CTTEL Shop');
    expect(await settings.get(STORE_NAME_SETTING_KEY)).toBe('CTTEL Shop');
  });

  it('accepts Persian unlimited keyword for maximum loan', async () => {
    const plans = new MemoryPlanRepository([
      {
        ...basePlan,
        maximumLoan: 3_000_000_000n,
      },
    ]);
    const admin = new AdminService(plans, new MemorySettingsRepository(), logger);

    const updated = await admin.updateField('admin-1', 1, 'maximumLoan', 'نامحدود');
    expect(updated.maximumLoan).toBeNull();
  });
});
