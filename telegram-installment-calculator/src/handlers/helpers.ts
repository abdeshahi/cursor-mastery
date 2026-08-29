import type { Context } from 'telegraf';
import type { BotDependencies } from './dependencies.js';
import { MAX_CASH_PRICE_TOMAN, parseBoundedUnsignedInteger } from '../utils/input-validation.js';
import { cashPriceTomanFromStoreDepositToman, MAX_STORE_DEPOSIT_TOMAN } from '../utils/store-deposit.js';
import { tomanToRial } from '../utils/persian.js';
import type { FundingSource } from '../types/result.js';

export function isAdmin(ctx: Context, adminId: string): boolean {
  return ctx.from !== undefined && String(ctx.from.id) === adminId;
}

export interface StoreDepositInput {
  storeDepositToman: string;
  cashPriceToman: string;
}

export function parseStoreDepositInput(text: string): StoreDepositInput {
  const storeDepositToman = parseBoundedUnsignedInteger(text, MAX_STORE_DEPOSIT_TOMAN, {
    allowZero: false,
    label: 'مبلغ واریز به فروشگاه',
  });
  const cashPriceToman = cashPriceTomanFromStoreDepositToman(storeDepositToman);

  return {
    storeDepositToman: storeDepositToman.toString(),
    cashPriceToman: cashPriceToman.toString(),
  };
}

export function parseInstallmentCapacityInput(text: string): string {
  const toman = parseBoundedUnsignedInteger(text, MAX_CASH_PRICE_TOMAN, {
    allowZero: false,
    label: 'توان پرداخت قسط',
  });

  return tomanToRial(toman).toString();
}

export function fundingSourceFromCode(code: string): FundingSource | null {
  const values: Record<string, FundingSource> = {
    melli: 'bank-melli',
    saman: 'bank-saman',
    blu: 'blubank',
  };

  return values[code] ?? null;
}

export type HandlerDependencies = BotDependencies;
