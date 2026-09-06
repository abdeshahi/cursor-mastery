import { Decimal } from 'decimal.js';
import { roundToNearestThousand } from '../calculator/installment-calculator.js';
import { MAX_CASH_PRICE_TOMAN } from './input-validation.js';
import { rialToToman, tomanToRial } from './persian.js';

export const STORE_COMMISSION_PERCENT = new Decimal(10);

export interface StoreDepositBreakdown {
  deductionRial: bigint;
  depositRial: bigint;
}

export function calculateStoreDepositFromCredit(creditRial: bigint): StoreDepositBreakdown {
  const credit = new Decimal(creditRial.toString());
  const deductionRial = roundToNearestThousand(
    credit.times(STORE_COMMISSION_PERCENT).dividedBy(100),
  );
  const depositRial = creditRial - deductionRial;

  return { deductionRial, depositRial };
}

export function storeDepositTomanFromCreditRial(creditRial: bigint): bigint {
  return rialToToman(calculateStoreDepositFromCredit(creditRial).depositRial);
}

export const MAX_STORE_DEPOSIT_TOMAN = storeDepositTomanFromCreditRial(
  tomanToRial(MAX_CASH_PRICE_TOMAN),
);

export function cashPriceTomanFromStoreDepositToman(storeDepositToman: bigint): bigint {
  const storeDepositRial = tomanToRial(storeDepositToman);
  const creditRial = roundToNearestThousand(
    new Decimal(storeDepositRial.toString())
      .times(100)
      .dividedBy(new Decimal(100).minus(STORE_COMMISSION_PERCENT)),
  );

  return rialToToman(creditRial);
}
