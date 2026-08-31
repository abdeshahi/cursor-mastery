import Parser from 'rss-parser';
import type { NewsSource } from '../config/sources.js';
import type { RawArticle } from './article.js';

const parser = new Parser({
  timeout: 20_000,
  headers: {
    'User-Agent':
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    Accept: 'application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.8',
  },
});

function stripHtml(value: string): string {
  return value
    .replace(/<!\[CDATA\[([\s\S]*?)]]>/g, '$1')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, ' ')
    .trim();
}

function articleId(sourceId: string, link: string, title: string): string {
  return `${sourceId}:${link || title}`.slice(0, 512);
}

function itemContent(item: Parser.Item): string {
  const extended = item as Parser.Item & { 'content:encoded'?: string };
  return item.contentSnippet ?? item.summary ?? extended['content:encoded'] ?? item.content ?? '';
}

function itemBodyHtml(item: Parser.Item): string | undefined {
  const extended = item as Parser.Item & { 'content:encoded'?: string };
  const encoded = extended['content:encoded'];
  if (encoded !== undefined && encoded.includes('<')) {
    return encoded;
  }

  const content = item.content ?? item.summary;
  if (content !== undefined && content.includes('<p')) {
    return content;
  }

  return undefined;
}

function itemSummary(item: Parser.Item): string {
  const snippet = item.contentSnippet ?? item.summary;
  if (snippet !== undefined && snippet.length > 0) {
    return stripHtml(snippet);
  }
  return stripHtml(itemContent(item));
}

function firstImage(item: Parser.Item): string | undefined {
  const enclosure = item.enclosure?.url;
  if (enclosure !== undefined && enclosure.startsWith('http')) {
    return enclosure;
  }

  const media = (item as Record<string, unknown>)['media:content'] as
    | { $?: { url?: string } }
    | undefined;
  if (media?.$?.url?.startsWith('http')) {
    return media.$.url;
  }

  const content = itemContent(item);
  const match = /<img[^>]+src=["']([^"']+)["']/i.exec(content);
  return match?.[1]?.startsWith('http') ? match[1] : undefined;
}

export async function fetchArticlesFromSource(source: NewsSource): Promise<RawArticle[]> {
  const feed = await parser.parseURL(source.url);
  const articles: RawArticle[] = [];

  for (const item of feed.items ?? []) {
    const title = stripHtml(item.title ?? '');
    const link = item.link ?? item.guid ?? '';
    const summary = itemSummary(item) || title;

    if (title.length === 0 || link.length === 0) {
      continue;
    }

    articles.push({
      id: articleId(source.id, link, title),
      sourceId: source.id,
      sourceName: source.name,
      sourceRole: source.role,
      title,
      summary: summary.slice(0, 1200),
      link,
      publishedAt: item.isoDate ? new Date(item.isoDate) : item.pubDate ? new Date(item.pubDate) : undefined,
      imageUrl: firstImage(item),
      bodyHtml: itemBodyHtml(item),
    });
  }

  return articles;
}

export async function fetchLatestArticles(sources: NewsSource[]): Promise<RawArticle[]> {
  const batches = await Promise.allSettled(sources.map((source) => fetchArticlesFromSource(source)));

  const articles: RawArticle[] = [];
  for (const [index, result] of batches.entries()) {
    if (result.status === 'fulfilled') {
      articles.push(...result.value);
      continue;
    }

    const source = sources[index];
    console.warn(`Failed to fetch ${source?.name ?? 'unknown source'}: ${String(result.reason)}`);
  }

  return articles.sort((left, right) => {
    const leftTime = left.publishedAt?.getTime() ?? 0;
    const rightTime = right.publishedAt?.getTime() ?? 0;
    return rightTime - leftTime;
  });
}
