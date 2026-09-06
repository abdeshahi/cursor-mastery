import type { StoredArticle } from '../feeds/article.js';
import { SOURCE_ROLE_LABELS_FA } from '../config/sources.js';

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function formatDate(value?: string): string {
  if (value === undefined) {
    return '';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '';
  }

  return new Intl.DateTimeFormat('fa-IR', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

function renderBody(bodyFa: string): string {
  return bodyFa
    .split(/\n{2,}/)
    .map((paragraph) => paragraph.trim())
    .filter((paragraph) => paragraph.length > 0)
    .map((paragraph) => `<p>${escapeHtml(paragraph)}</p>`)
    .join('\n');
}

export function renderArticlePage(article: StoredArticle): string {
  const roleLabel =
    SOURCE_ROLE_LABELS_FA[article.sourceRole as keyof typeof SOURCE_ROLE_LABELS_FA] ??
    article.sourceRole;
  const date = formatDate(article.publishedAt);

  return `<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${escapeHtml(article.titleFa)} | CTTEL</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f8fb;
      --card: #ffffff;
      --text: #1f2937;
      --muted: #6b7280;
      --accent: #2563eb;
      --border: #e5e7eb;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Vazirmatn", "Tahoma", sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.9;
    }
    .wrap {
      max-width: 760px;
      margin: 0 auto;
      padding: 20px 16px 40px;
    }
    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 24px 20px;
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
    }
    .brand {
      color: var(--accent);
      font-weight: 700;
      margin-bottom: 8px;
      font-size: 0.95rem;
    }
    h1 {
      margin: 0 0 12px;
      font-size: 1.55rem;
      line-height: 1.6;
    }
    .meta {
      color: var(--muted);
      font-size: 0.92rem;
      margin-bottom: 18px;
    }
    .summary {
      background: #eff6ff;
      border-right: 4px solid var(--accent);
      padding: 14px 16px;
      border-radius: 10px;
      margin-bottom: 22px;
      font-size: 1rem;
    }
    .hero {
      width: 100%;
      border-radius: 12px;
      margin-bottom: 20px;
    }
    .body p {
      margin: 0 0 16px;
      font-size: 1.02rem;
    }
    .footer {
      margin-top: 28px;
      padding-top: 18px;
      border-top: 1px solid var(--border);
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
    }
    .footer a {
      color: var(--accent);
      text-decoration: none;
      font-weight: 600;
    }
  </style>
</head>
<body>
  <div class="wrap">
    <article class="card">
      <div class="brand">CTTEL News</div>
      <h1>${escapeHtml(article.titleFa)}</h1>
      <div class="meta">📌 ${escapeHtml(article.sourceName)} · ${escapeHtml(roleLabel)}${date ? ` · 🗓 ${escapeHtml(date)}` : ''}</div>
      ${article.imageUrl ? `<img class="hero" src="${escapeHtml(article.imageUrl)}" alt="">` : ''}
      <div class="summary">${escapeHtml(article.summaryFa)}</div>
      <div class="body">
        ${renderBody(article.bodyFa)}
      </div>
      <div class="footer">
        <a href="${escapeHtml(article.sourceLink)}" rel="noopener noreferrer" target="_blank">مشاهده منبع انگلیسی</a>
      </div>
    </article>
  </div>
</body>
</html>`;
}

export function renderNotFoundPage(): string {
  return `<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>مقاله یافت نشد | CTTEL</title>
</head>
<body style="font-family:Tahoma,sans-serif;text-align:center;padding:40px;">
  <h1>مقاله یافت نشد</h1>
  <p>این لینک منقضی شده یا مقاله حذف شده است.</p>
</body>
</html>`;
}
