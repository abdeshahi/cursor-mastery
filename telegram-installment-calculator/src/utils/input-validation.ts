import { toEnglishDigits } from './persian.js';

export const MAX_SIGNED_64 = 9223372036854775807n;
export const MAX_CASH_PRICE_TOMAN = MAX_SIGNED_64 / 10n;
export const MAX_NUMERIC_INPUT_LENGTH = 64;

export class UserInputError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'UserInputError';
  }
}

export function normalizeNumericText(input: string): string {
  if (input.length > MAX_NUMERIC_INPUT_LENGTH) {
    throw new UserInputError('مقدار واردشده بیش از حد طولانی است.');
  }

  return toEnglishDigits(input.trim()).replace(/[٬,\s]/g, '');
}

export function parseBoundedUnsignedInteger(
  input: string,
  maximum: bigint,
  options: { allowZero: boolean; label: string },
): bigint {
  const normalized = normalizeNumericText(input);
  if (!/^\d+$/.test(normalized)) {
    throw new UserInputError(`${options.label} باید عدد صحیح نامنفی باشد.`);
  }

  const canonical = normalized.replace(/^0+(?=\d)/, '');
  const maximumText = maximum.toString();
  if (
    canonical.length > maximumText.length ||
    (canonical.length === maximumText.length && canonical > maximumText)
  ) {
    throw new UserInputError(`${options.label} از بیشترین مقدار مجاز بزرگ‌تر است.`);
  }

  const value = BigInt(canonical);
  if (!options.allowZero && value === 0n) {
    throw new UserInputError(`${options.label} باید بزرگ‌تر از صفر باشد.`);
  }

  return value;
}
