import { toPersianDigits } from './persian.js';

const jalaliPartsFormatter = new Intl.DateTimeFormat('en-US-u-ca-persian-nu-latn', {
  timeZone: 'UTC',
  year: 'numeric',
  month: 'numeric',
  day: 'numeric',
});

export interface JalaliDate {
  year: number;
  month: number;
  day: number;
}

export function toJalali(date: Date): JalaliDate {
  if (Number.isNaN(date.getTime())) {
    throw new RangeError('date must be valid');
  }

  const parts = jalaliPartsFormatter.formatToParts(date);
  const getPart = (type: Intl.DateTimeFormatPartTypes): number => {
    const value = parts.find((part) => part.type === type)?.value;
    if (value === undefined) {
      throw new Error(`Intl did not return a ${type} part`);
    }

    return Number(value);
  };

  return {
    year: getPart('year'),
    month: getPart('month'),
    day: getPart('day'),
  };
}

export function formatJalali(date: Date, persianDigits = true): string {
  const { year, month, day } = toJalali(date);
  const formatted = `${String(year)}/${String(month).padStart(2, '0')}/${String(day).padStart(2, '0')}`;

  return persianDigits ? toPersianDigits(formatted) : formatted;
}
