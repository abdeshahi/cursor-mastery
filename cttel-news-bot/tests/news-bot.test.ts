import { describe, expect, it } from 'vitest';
import { formatTelegramPost } from '../src/format/post-formatter.js';
import type { TranslatedArticle } from '../src/feeds/article.js';
import { chunkTelegramMessage, escapeHtml, rtl } from '../src/utils/telegram-html.js';
import { SeenStore } from '../src/store/seen-store.js';
import { mkdtemp, rm } from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';

describe('post formatter', () => {
  it('formats a Persian Telegram post with source and link', () => {
    const article: TranslatedArticle = {
      id: 'test:1',
      sourceId: 'gsmarena',
      sourceName: 'GSMArena',
      titleFa: 'گلکسی S26 با باتری بزرگ‌تر',
      summaryFa: 'سامسونگ در نسل بعدی ظرفیت باتری را افزایش می‌دهد.',
      link: 'https://example.com/news/1',
      publishedAt: new Date('2026-08-30T10:00:00.000Z'),
    };

    const post = formatTelegramPost(article);
    expect(post).toContain('گلکسی S26');
    expect(post).toContain('GSMArena');
    expect(post).toContain('https://example.com/news/1');
  });
});

describe('telegram html utils', () => {
  it('escapes html characters', () => {
    expect(escapeHtml('a & b < c')).toBe('a &amp; b &lt; c');
  });

  it('wraps rtl isolates', () => {
    expect(rtl('سلام')).toBe('\u2067سلام\u2069');
  });

  it('chunks long messages', () => {
    const chunks = chunkTelegramMessage('a'.repeat(5000), 2000);
    expect(chunks.length).toBeGreaterThan(1);
    expect(chunks.join('').length).toBe(5000);
  });
});

describe('seen store', () => {
  it('persists seen article ids', async () => {
    const dir = await mkdtemp(path.join(os.tmpdir(), 'cttel-news-'));
    const store = await SeenStore.open(dir);

    expect(store.has('article-1')).toBe(false);
    await store.markSeen('article-1');
    expect(store.has('article-1')).toBe(true);

    const reopened = await SeenStore.open(dir);
    expect(reopened.has('article-1')).toBe(true);

    await rm(dir, { recursive: true, force: true });
  });
});
