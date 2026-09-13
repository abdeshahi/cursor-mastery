import { escapeHtml } from '../utils/format.js';

export const START_TEXT = [
  'سلام، به فروش VPN خوش آمدید.',
  'پلن را انتخاب کنید، مبلغ را واریز کنید و رسید را همین‌جا بفرستید.',
  'بعد از تأیید ادمین، سرویس به‌صورت خودکار برایتان ساخته می‌شود.',
].join('\n');

export function supportText(username: string, fallback: string): string {
  const handle = username.trim().replace(/^@/, '');
  if (handle.length > 0) {
    return `پشتیبانی: @${escapeHtml(handle)}\n${escapeHtml(fallback)}`;
  }
  return escapeHtml(fallback);
}

export const NO_PLANS = 'در حال حاضر پلنی برای فروش فعال نیست. بعداً سر بزنید.';
export const NO_SERVICES = 'هنوز سرویسی ندارید. از «خرید VPN» شروع کنید.';
export const BLOCKED = 'حساب شما مسدود است.';
export const UNKNOWN_CALLBACK = 'این دکمه نامعتبر است.';
export const NOT_ADMIN = 'این عملیات فقط برای ادمین است.';
export const RECEIPT_SAVED = 'رسید دریافت شد. پس از بررسی ادمین نتیجه برایتان ارسال می‌شود.';
export const REJECTED_CUSTOMER =
  'رسید پرداخت تأیید نشد. اگر اشتباهی رخ داده با پشتیبانی صحبت کنید یا دوباره خرید کنید.';
export const CANCELLED = 'سفارش لغو شد.';
