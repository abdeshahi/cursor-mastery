import type { TranslatedArticle } from '../feeds/article.js';
import { SOURCE_ROLE_LABELS_FA } from '../config/sources.js';
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
  const roleLabel =
    SOURCE_ROLE_LABELS_FA[article.sourceRole as keyof typeof SOURCE_ROLE_LABELS_FA] ??
    article.sourceRole;

  const lines = [
    rtl(`📰 ${escapeHtml(article.titleFa)}`),
    '',
    rtl(escapeHtml(article.summaryFa)),
    '',
    rtl(`📌 منبع: ${escapeHtml(article.sourceName)} · ${escapeHtml(roleLabel)}`),
  ];

  const date = formatDate(article.publishedAt);
  if (date.length > 0) {
    lines.push(rtl(`🗓 ${escapeHtml(date)}`));
  }

  lines.push('', rtl(`📖 <a href="${escapeHtml(article.readerUrl)}">مطالعه کامل به فارسی</a>`));
  lines.push(rtl(`🔗 <a href="${escapeHtml(article.link)}">منبع انگلیسی</a>`));

  return lines.join('\n');
}
