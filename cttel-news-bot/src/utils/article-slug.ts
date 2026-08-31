import { createHash } from 'node:crypto';

export function articleSlug(articleId: string): string {
  return createHash('sha256').update(articleId).digest('hex').slice(0, 12);
}

export function buildReaderUrl(baseUrl: string, slug: string): string {
  return `${baseUrl.replace(/\/$/, '')}/read/${slug}`;
}
