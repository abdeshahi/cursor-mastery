import { Decimal } from 'decimal.js';
import type winston from 'winston';
import type { PlanPatch, PlanTerms } from '../types/calculator.js';
import type { PlanRepository } from '../database/repositories.js';
import {
  MAX_CASH_PRICE_TOMAN,
  UserInputError,
  normalizeNumericText,
  parseBoundedUnsignedInteger,
} from '../utils/input-validation.js';
import { tomanToRial } from '../utils/persian.js';

type EditableField = Exclude<keyof PlanPatch, 'isActive'>;

export class AdminService {
  constructor(
    private readonly plans: PlanRepository,
    private readonly logger: winston.Logger,
  ) {}

  listPlans(): Promise<PlanTerms[]> {
    return this.plans.findAll();
  }

  async updateField(
    adminId: string,
    planId: number,
    field: EditableField,
    rawValue: string,
  ): Promise<PlanTerms> {
    const previous = await this.plans.findById(planId);
    if (previous === null) {
      throw new Error('طرح انتخاب‌شده پیدا نشد.');
    }

    const patch = this.parsePatch(field, rawValue);
    this.validateLimits(previous, patch);

    let updated: PlanTerms;
    try {
      updated = await this.plans.updateValidated(planId, patch);
    } catch (error) {
      if (error instanceof RangeError) {
        throw new UserInputError('مقدار با محدودیت‌های طرح سازگار نیست.');
      }

      throw error;
    }

    this.logger.info('admin.plan.updated', {
      adminId,
      planId,
      field,
      before: this.auditValue(previous, field),
      after: this.auditValue(updated, field),
    });

    return updated;
  }

  async toggleActive(adminId: string, planId: number): Promise<PlanTerms> {
    const previous = await this.plans.findById(planId);
    if (previous === null) {
      throw new Error('طرح انتخاب‌شده پیدا نشد.');
    }

    const updated = await this.plans.updateValidated(planId, { isActive: !previous.isActive });

    this.logger.info('admin.plan.status_toggled', {
      adminId,
      planId,
      before: previous.isActive,
      after: updated.isActive,
    });

    return updated;
  }

  private parsePatch(field: EditableField, rawValue: string): PlanPatch {
    if (field === 'minimumLoan' || field === 'maximumLoan') {
      if (field === 'maximumLoan' && rawValue.toLowerCase() === 'unlimited') {
        return { maximumLoan: null };
      }

      const toman = parseBoundedUnsignedInteger(rawValue, MAX_CASH_PRICE_TOMAN, {
        allowZero: true,
        label: 'مبلغ',
      });

      return {
        [field]: tomanToRial(toman),
      };
    }

    const normalized = normalizeNumericText(rawValue);
    if (!/^\d+(?:\.\d+)?$/.test(normalized)) {
      throw new UserInputError('مقدار اعشاری معتبر وارد کنید.');
    }

    let value: Decimal;
    try {
      value = new Decimal(normalized);
    } catch {
      throw new UserInputError('مقدار اعشاری معتبر وارد کنید.');
    }

    if (!value.isFinite() || value.isNegative()) {
      throw new UserInputError('مقدار باید عدد نامنفی باشد.');
    }

    if (field === 'monthlyInstallmentFactor') {
      if (value.isZero()) {
        throw new UserInputError('ضریب قسط باید بزرگ‌تر از صفر باشد.');
      }

      return { monthlyInstallmentFactor: value.toString() };
    }

    if (value.greaterThanOrEqualTo(100)) {
      throw new UserInputError('درصد باید کمتر از ۱۰۰ باشد.');
    }

    if (field === 'creditPercent' && value.isZero()) {
      throw new UserInputError('درصد اعتبار باید بزرگ‌تر از صفر باشد.');
    }

    const complement = new Decimal(100).minus(value).toString();
    return field === 'creditPercent'
      ? { creditPercent: value.toString(), servicePercent: complement }
      : { servicePercent: value.toString(), creditPercent: complement };
  }

  private auditValue(plan: PlanTerms, field: EditableField): string {
    const value = plan[field];
    return value === null ? 'unlimited' : String(value);
  }

  private validateLimits(plan: PlanTerms, patch: PlanPatch): void {
    const minimum = patch.minimumLoan ?? BigInt(String(plan.minimumLoan));
    const maximum =
      patch.maximumLoan === undefined
        ? plan.maximumLoan === null
          ? null
          : BigInt(String(plan.maximumLoan))
        : patch.maximumLoan;

    if (maximum !== null && maximum < minimum) {
      throw new UserInputError('حداکثر وام نمی‌تواند از حداقل وام کمتر باشد.');
    }
  }
}
