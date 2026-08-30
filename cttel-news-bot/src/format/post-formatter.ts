import type { TranslatedArticle } from '../feeds/article.js';
import { escapeHtml, rtl } from '../utils/telegram-html.js';

function formatDate(date?: Date): string {
  if (date === undefined || Number.isNaN(date.getTime())) {
    return '';
  }

  return new Intl.DateTimeFormat('fa-IR', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

export function formatTelegramPost(article: TranslatedArticle): string {
  const lines = [
    rtl(`📰 ${escapeHtml(article.titleFa)}`),
    '',
    rtl(escapeHtml(article.summaryFa)),
    '',
    rtl(`📌 منبع: ${escapeHtml(article.sourceName)}`),
  ];

  const date = formatDate(article.publishedAt);
  if (date.length > 0) {
    lines.push(rtl(`🗓 ${escapeHtml(date)}`));
  }

  lines.push('', rtl(`🔗 <a href="${escapeHtml(article.link)}">مطالعه منبع</a>`));

  return lines.join('\n');
}
