import type { Plan, Prisma, PrismaClient, User } from '@prisma/client';
import { calculateInstallment } from '../calculator/installment-calculator.js';
import type {
  CalculationRecord,
  PlanPatch,
  PlanTerms,
} from '../types/calculator.js';

function toPlanTerms(plan: Plan): PlanTerms {
  return {
    id: plan.id,
    months: plan.months,
    creditPercent: plan.creditPercent.toString(),
    servicePercent: plan.servicePercent.toString(),
    monthlyInstallmentFactor: plan.monthlyInstallmentFactor.toString(),
    minimumLoan: plan.minimumLoan,
    maximumLoan: plan.maximumLoan,
    isActive: plan.isActive,
  };
}

export interface PlanRepository {
  findActive(): Promise<PlanTerms[]>;
  findAll(): Promise<PlanTerms[]>;
  findById(id: number): Promise<PlanTerms | null>;
  updateValidated(id: number, patch: PlanPatch): Promise<PlanTerms>;
}

export interface UserUpsertInput {
  telegramId: bigint;
  firstName?: string;
  lastName?: string;
  username?: string;
}

export interface UserRepository {
  findByTelegramId(telegramId: bigint): Promise<User | null>;
  upsert(input: UserUpsertInput): Promise<User>;
}

export interface CalculationRepository {
  create(input: CalculationRecord): Promise<unknown>;
  createMany(inputs: CalculationRecord[]): Promise<number>;
}

export class PrismaPlanRepository implements PlanRepository {
  constructor(private readonly db: PrismaClient) {}

  async findActive(): Promise<PlanTerms[]> {
    const plans = await this.db.plan.findMany({
      where: { isActive: true },
      orderBy: { sortOrder: 'asc' },
    });

    return plans.map(toPlanTerms);
  }

  async findAll(): Promise<PlanTerms[]> {
    return (await this.db.plan.findMany({ orderBy: { sortOrder: 'asc' } })).map(toPlanTerms);
  }

  async findById(id: number): Promise<PlanTerms | null> {
    const plan = await this.db.plan.findUnique({ where: { id } });
    return plan === null ? null : toPlanTerms(plan);
  }

  async updateValidated(id: number, patch: PlanPatch): Promise<PlanTerms> {
    return this.db.$transaction(async (transaction) => {
      const current = await transaction.plan.findUniqueOrThrow({ where: { id } });
      const candidate: PlanTerms = {
        ...toPlanTerms(current),
        ...patch,
      };

      calculateInstallment(1n, candidate);

      const data: Prisma.PlanUpdateInput = {};
      if (patch.creditPercent !== undefined) {
        data.creditPercent = patch.creditPercent;
      }
      if (patch.servicePercent !== undefined) {
        data.servicePercent = patch.servicePercent;
      }
      if (patch.monthlyInstallmentFactor !== undefined) {
        data.monthlyInstallmentFactor = patch.monthlyInstallmentFactor;
      }
      if (patch.minimumLoan !== undefined) {
        data.minimumLoan = patch.minimumLoan;
      }
      if (patch.maximumLoan !== undefined) {
        data.maximumLoan = patch.maximumLoan;
      }
      if (patch.isActive !== undefined) {
        data.isActive = patch.isActive;
      }

      const updated = await transaction.plan.update({ where: { id }, data });
      return toPlanTerms(updated);
    });
  }
}

export class PrismaUserRepository implements UserRepository {
  constructor(private readonly db: PrismaClient) {}

  findByTelegramId(telegramId: bigint): Promise<User | null> {
    return this.db.user.findUnique({ where: { telegramId } });
  }

  upsert(input: UserUpsertInput): Promise<User> {
    const { telegramId } = input;
    const profile = {
      ...(input.firstName === undefined ? {} : { firstName: input.firstName }),
      ...(input.lastName === undefined ? {} : { lastName: input.lastName }),
      ...(input.username === undefined ? {} : { username: input.username }),
    };

    return this.db.user.upsert({
      where: { telegramId },
      create: { telegramId, ...profile },
      update: profile,
    });
  }
}

export class PrismaCalculationRepository implements CalculationRepository {
  constructor(private readonly db: PrismaClient) {}

  create(input: CalculationRecord) {
    return this.db.calculation.create({
      data: {
        ...(input.userId === undefined ? {} : { userId: input.userId }),
        planId: input.planId,
        fundingSource: input.fundingSource,
        cashPriceToman: input.cashPriceToman,
        cashPriceRial: input.cashPriceRial,
        requiredLoan: input.requiredLoan,
        credit: input.credit,
        digitalService: input.digitalService,
        monthlyInstallment: input.monthlyInstallment,
        totalRepayment: input.totalRepayment,
        eligible: input.eligible,
      },
    });
  }

  async createMany(inputs: CalculationRecord[]): Promise<number> {
    const result = await this.db.calculation.createMany({
      data: inputs.map((input) => ({
        userId: input.userId,
        planId: input.planId,
        fundingSource: input.fundingSource,
        cashPriceToman: input.cashPriceToman,
        cashPriceRial: input.cashPriceRial,
        requiredLoan: input.requiredLoan,
        credit: input.credit,
        digitalService: input.digitalService,
        monthlyInstallment: input.monthlyInstallment,
        totalRepayment: input.totalRepayment,
        eligible: input.eligible,
      })),
    });

    return result.count;
  }
}

export class PrismaSettingRepository {
  constructor(private readonly db: PrismaClient) {}

  async get(key: string): Promise<string | null> {
    return (await this.db.setting.findUnique({ where: { key } }))?.value ?? null;
  }

  set(key: string, value: string) {
    return this.db.setting.upsert({
      where: { key },
      create: { key, value },
      update: { value },
    });
  }
}
