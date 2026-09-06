import type { NewsSource } from '../config/sources.js';
import type { RawArticle } from './article.js';
import { stripHtml } from './article-content.js';

const FETCH_HEADERS = {
  'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
  Accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
  'Accept-Language': 'fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7',
};

interface HtmlLinkRule {
  pattern: RegExp;
  baseUrl: string;
  absolute?: boolean;
}

const HTML_LINK_RULES: Record<string, HtmlLinkRule[]> = {
  cra: [
    { pattern: /href="(\/fa\/news\/[^"#?]+)"/gi, baseUrl: 'https://www.cra.ir' },
    { pattern: /href="(https:\/\/www\.cra\.ir\/fa\/news\/[^"#?]+)"/gi, baseUrl: '', absolute: true },
  ],
  tci: [
    { pattern: /href="(\/fa\/news\/[^"#?]+)"/gi, baseUrl: 'https://www.tci.ir' },
    { pattern: /href="(https:\/\/www\.tci\.ir\/fa\/news\/[^"#?]+)"/gi, baseUrl: '', absolute: true },
  ],
  isti: [
    { pattern: /href="(\/fa\/news\/[^"#?]+)"/gi, baseUrl: 'https://www.isti.ir' },
    { pattern: /href="(https:\/\/www\.isti\.ir\/fa\/news\/[^"#?]+)"/gi, baseUrl: '', absolute: true },
  ],
  tasnim: [
    {
      pattern: /href="(\/fa\/news\/[^"#?]+)"/gi,
      baseUrl: 'https://www.tasnimnews.com',
    },
    {
      pattern: /href="(https:\/\/www\.tasnimnews\.com\/fa\/news\/[^"#?]+)"/gi,
      baseUrl: '',
      absolute: true,
    },
  ],
  fars: [
    { pattern: /href="(\/science\/[^"#?]+)"/gi, baseUrl: 'https://www.farsnews.ir' },
    { pattern: /href="(https:\/\/www\.farsnews\.ir\/science\/[^"#?]+)"/gi, baseUrl: '', absolute: true },
  ],
};

function articleId(sourceId: string, link: string, title: string): string {
  return `${sourceId}:${link || title}`.slice(0, 512);
}

function normalizeLink(rawLink: string, rule: HtmlLinkRule): string {
  if (rule.absolute === true || rawLink.startsWith('http')) {
    return rawLink;
  }
  return `${rule.baseUrl}${rawLink}`;
}

function cleanTitle(value: string): string {
  return stripHtml(value).replace(/\s+/g, ' ').trim();
}

function extractLinks(html: string, sourceId: string): Array<{ link: string; title: string }> {
  const rules = HTML_LINK_RULES[sourceId] ?? [];
  const found = new Map<string, string>();

  for (const rule of rules) {
    for (const match of html.matchAll(rule.pattern)) {
      const rawLink = match[1];
      if (rawLink === undefined) {
        continue;
      }

      const link = normalizeLink(rawLink, rule);
      if (!found.has(link)) {
        found.set(link, link.split('/').filter(Boolean).pop()?.replace(/-/g, ' ') ?? link);
      }
    }
  }

  return [...found.entries()].map(([link, title]) => ({ link, title: cleanTitle(title) }));
}

async function fetchListingHtml(url: string): Promise<string> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 25_000);

  try {
    const response = await fetch(url, {
      headers: FETCH_HEADERS,
      signal: controller.signal,
      redirect: 'follow',
    });

    if (!response.ok) {
      throw new Error(`Status code ${String(response.status)}`);
    }

    return await response.text();
  } finally {
    clearTimeout(timeout);
  }
}

export async function fetchArticlesFromHtmlSource(source: NewsSource): Promise<RawArticle[]> {
  const html = await fetchListingHtml(source.url);
  const links = extractLinks(html, source.id);
  const articles: RawArticle[] = [];

  for (const item of links.slice(0, 20)) {
    if (item.title.length === 0) {
      continue;
    }

    articles.push({
      id: articleId(source.id, item.link, item.title),
      sourceId: source.id,
      sourceName: source.name,
      sourceRole: source.role,
      title: item.title,
      summary: item.title,
      link: item.link,
    });
  }

  return articles;
}
