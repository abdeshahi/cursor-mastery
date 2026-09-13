const PERSIAN_DIGITS = '۰۱۲۳۴۵۶۷۸۹';
const ARABIC_INDIC_DIGITS = '٠١٢٣٤٥٦٧٨٩';
export const RIALS_PER_TOMAN = 10n;

export function toPersianDigits(value: string | number | bigint): string {
  return String(value).replace(/\d/g, (digit) => PERSIAN_DIGITS[Number(digit)] ?? digit);
}

export function toEnglishDigits(value: string): string {
  return value
    .replace(/[۰-۹]/g, (digit) => String(PERSIAN_DIGITS.indexOf(digit)))
    .replace(/[٠-٩]/g, (digit) => String(ARABIC_INDIC_DIGITS.indexOf(digit)));
}

export function formatThousands(value: string | number | bigint, persianDigits = true): string {
  const normalized = toEnglishDigits(String(value)).replace(/[٬,\s]/g, '');
  if (!/^-?\d+(?:\.\d+)?$/.test(normalized)) {
    throw new TypeError('value must be a valid decimal number');
  }

  const [integer = '', fraction] = normalized.split('.');
  const grouped = integer.replace(/\B(?=(\d{3})+(?!\d))/g, '٬');
  const result = fraction === undefined ? grouped : `${grouped}.${fraction}`;

  return persianDigits ? toPersianDigits(result) : result;
}

export function rialToToman(rial: bigint): bigint {
  return rial / RIALS_PER_TOMAN;
}

export function tomanToRial(toman: bigint): bigint {
  return toman * RIALS_PER_TOMAN;
}

export function formatToman(value: string | number | bigint): string {
  return `${formatThousands(value)} تومان`;
}

export function formatRialAsToman(rial: bigint): string {
  return formatToman(rialToToman(rial));
}

export function parsePersianInteger(value: string): bigint {
  const normalized = toEnglishDigits(value).replace(/[٬,\s]/g, '');
  if (!/^-?\d+$/.test(normalized)) {
    throw new TypeError('value must be an integer');
  }

  return BigInt(normalized);
}
