export function formatAmount(amount: number, currency: string): string {
  return `${amount.toLocaleString('fa-IR')} ${currency}`;
}

export function formatDate(date: Date): string {
  return date.toLocaleString('fa-IR', {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone: 'Asia/Tehran',
  });
}

export function escapeHtml(value: string): string {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}
