export function boldHtml(text: string): string {
  return `<b>${text}</b>`;
}

export const TELEGRAM_HTML_PARSE_MODE = { parse_mode: 'HTML' as const };
