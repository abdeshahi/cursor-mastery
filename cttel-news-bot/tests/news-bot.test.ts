import { describe, expect, it } from 'vitest';
import { formatTelegramPost } from '../src/format/post-formatter.js';
import type { RawArticle, TranslatedArticle } from '../src/feeds/article.js';
import {
  DEFAULT_NEWS_SOURCES,
  SOURCE_ROLE_LABELS_FA,
  isIranSource,
  resolveSources,
} from '../src/config/sources.js';
import { evaluateArticleTopic, isRelevantArticle } from '../src/filter/topic-filter.js';
import { stripHtml } from '../src/feeds/article-content.js';
import { renderArticlePage } from '../src/server/article-page.js';
import { articleSlug, buildReaderUrl } from '../src/utils/article-slug.js';
import { chunkTelegramMessage, escapeHtml, rtl } from '../src/utils/telegram-html.js';
import { SeenStore } from '../src/store/seen-store.js';
import { mkdtemp, rm } from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';

function article(partial: Partial<RawArticle> & Pick<RawArticle, 'title'>): RawArticle {
  return {
    id: 'test:1',
    sourceId: 'theverge',
    sourceName: 'The Verge',
    sourceRole: 'news',
    summary: partial.summary ?? '',
    link: 'https://example.com/news/1',
    ...partial,
  };
}

describe('default news sources', () => {
  it('includes international and Iranian sources', () => {
    const ids = DEFAULT_NEWS_SOURCES.map((source) => source.id);
    expect(ids).toContain('gsmarena');
    expect(ids).toContain('ict-gov');
    expect(ids).toContain('citna');
    expect(ids).toContain('zoomit');
    expect(ids).toContain('asreertebat');
    expect(ids).toContain('isti');
    expect(DEFAULT_NEWS_SOURCES.every((source) => source.enabled)).toBe(true);
  });

  it('resolves only enabled sources by default', () => {
    expect(resolveSources([]).length).toBe(DEFAULT_NEWS_SOURCES.length);
  });

  it('marks Iranian sources correctly', () => {
    expect(isIranSource('citna')).toBe(true);
    expect(isIranSource('gsmarena')).toBe(false);
  });

  it('uses mobile-only feeds for CNET and TechRadar', () => {
    const cnet = DEFAULT_NEWS_SOURCES.find((source) => source.id === 'cnet');
    const techradar = DEFAULT_NEWS_SOURCES.find((source) => source.id === 'techradar');
    expect(cnet?.url).toContain('/mobile/');
    expect(techradar?.url).toContain('/phones');
  });

  it('prioritizes GSMArena for specs coverage', () => {
    const gsmarena = DEFAULT_NEWS_SOURCES.find((source) => source.id === 'gsmarena');
    expect(gsmarena?.role).toBe('specs');
    expect(gsmarena?.priority).toBe(1);
  });

  it('maps every role to a Persian label', () => {
    for (const source of DEFAULT_NEWS_SOURCES) {
      expect(SOURCE_ROLE_LABELS_FA[source.role]).toBeTruthy();
    }
  });
});

describe('topic filter', () => {
  it('allows Iranian sources without brand filtering', () => {
    expect(
      isRelevantArticle(
        article({
          sourceId: 'citna',
          sourceName: 'سیتنا',
          title: 'افزایش تعرفه اینترنت',
          summary: 'خبر داخلی حوزه ICT',
        }),
      ),
    ).toBe(true);
  });

  it('allows foreign news only for Samsung, Apple, Xiaomi, Nothing, and Honor', () => {
    expect(
      isRelevantArticle(
        article({
          title: 'Samsung Galaxy S26 Ultra leak reveals bigger battery',
          summary: 'The upcoming flagship smartphone may ship with a 5500 mAh cell.',
        }),
      ),
    ).toBe(true);

    expect(
      evaluateArticleTopic(
        article({
          title: 'Google Pixel 10 review',
          summary: 'Google latest Android phone with Tensor chip.',
        }),
      ).reason,
    ).toBe('no-allowed-brand');
  });

  it('blocks computer and laptop news', () => {
    expect(
      evaluateArticleTopic(
        article({
          title: 'Best gaming laptops for 2026',
          summary: 'These RTX-powered notebooks dominate PC gaming.',
        }),
      ).reason,
    ).toBe('blocked-computer');
  });

  it('blocks Mac news from Apple sources when iPhone is not mentioned', () => {
    expect(
      evaluateArticleTopic(
        article({
          sourceId: '9to5mac',
          sourceName: '9to5Mac',
          title: 'M4 MacBook Pro refresh rumored for fall',
          summary: 'Apple may update its laptop lineup with faster chips.',
        }),
      ).allowed,
    ).toBe(false);
  });

  it('allows iPhone news from Apple sources', () => {
    expect(
      isRelevantArticle(
        article({
          sourceId: 'macrumors',
          sourceName: 'MacRumors',
          title: 'iPhone 18 Pro may adopt new camera sensor',
          summary: 'Supply chain reports point to improved telephoto hardware.',
        }),
      ),
    ).toBe(true);
  });
});

describe('post formatter', () => {
  it('formats a Persian Telegram post with source and link', () => {
    const article: TranslatedArticle = {
      id: 'test:1',
      sourceId: 'gsmarena',
      sourceName: 'GSMArena',
      sourceRole: 'specs',
      titleFa: 'گلکسی S26 با باتری بزرگ‌تر',
      summaryFa: 'سامسونگ در نسل بعدی ظرفیت باتری را افزایش می‌دهد.',
      bodyFa: 'سامسونگ در نسل بعدی ظرفیت باتری را افزایش می‌دهد و جزئیات بیشتری در متن کامل آمده است.',
      link: 'https://example.com/news/1',
      slug: 'abc123def456',
      readerUrl: 'http://185.18.214.66:3002/read/abc123def456',
      publishedAt: new Date('2026-08-30T10:00:00.000Z'),
    };

    const post = formatTelegramPost(article);
    expect(post).toContain('گلکسی S26');
    expect(post).toContain('GSMArena');
    expect(post).toContain('مشخصات فنی');
    expect(post).toContain('مطالعه کامل به فارسی');
    expect(post).toContain('http://185.18.214.66:3002/read/abc123def456');
    expect(post).toContain('https://example.com/news/1');
  });
});

describe('article reader', () => {
  it('builds stable slugs and reader urls', () => {
    const slug = articleSlug('gsmarena:https://example.com/news/1');
    expect(slug).toHaveLength(12);
    expect(buildReaderUrl('http://185.18.214.66:3002', slug)).toBe(
      `http://185.18.214.66:3002/read/${slug}`,
    );
  });

  it('renders a Persian reader page with full body', () => {
    const html = renderArticlePage({
      slug: 'abc123def456',
      id: 'test:1',
      titleFa: 'آیفون ۱۸ پرو',
      summaryFa: 'خلاصه خبر',
      bodyFa: 'پارagraph اول.\n\nپارagraph دوم.',
      sourceName: 'MacRumors',
      sourceRole: 'apple',
      sourceLink: 'https://example.com/news/1',
      createdAt: new Date().toISOString(),
    });

    expect(html).toContain('lang="fa"');
    expect(html).toContain('dir="rtl"');
    expect(html).toContain('آیفون ۱۸ پرو');
    expect(html).toContain('پارagraph اول.');
    expect(html).toContain('پارagraph دوم.');
  });

  it('strips html from article content', () => {
    expect(stripHtml('<p>Hello <strong>world</strong></p>')).toBe('Hello world');
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
