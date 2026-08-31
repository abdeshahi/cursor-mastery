import { describe, expect, it } from 'vitest';
import { formatTelegramPost } from '../src/format/post-formatter.js';
import type { RawArticle, TranslatedArticle } from '../src/feeds/article.js';
import { DEFAULT_NEWS_SOURCES, SOURCE_ROLE_LABELS_FA } from '../src/config/sources.js';
import { evaluateArticleTopic, isRelevantArticle } from '../src/filter/topic-filter.js';
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
  it('includes curated mobile-focused sources without Notebookcheck', () => {
    const ids = DEFAULT_NEWS_SOURCES.map((source) => source.id);
    expect(ids).toEqual([
      'gsmarena',
      'android-authority',
      'phonearena',
      'theverge',
      'engadget',
      'cnet',
      'techradar',
      'android-police',
      '9to5google',
      '9to5mac',
      'macrumors',
      'dxomark',
    ]);
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
  it('allows mobile phone news from mixed sources', () => {
    expect(
      isRelevantArticle(
        article({
          title: 'Samsung Galaxy S26 Ultra leak reveals bigger battery',
          summary: 'The upcoming flagship smartphone may ship with a 5500 mAh cell.',
        }),
      ),
    ).toBe(true);
  });

  it('allows AI news from mixed sources', () => {
    expect(
      isRelevantArticle(
        article({
          title: 'Google Gemini gets smarter on Android phones',
          summary: 'The new AI assistant features roll out to Pixel devices first.',
        }),
      ),
    ).toBe(true);
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

    expect(
      evaluateArticleTopic(
        article({
          title: 'Mechanical keyboard review: best switches for typing',
          summary: 'We tested keycaps and RGB lighting on desktop setups.',
        }),
      ).reason,
    ).toBe('blocked-computer');
  });

  it('allows trusted mobile sources even with sparse keywords', () => {
    expect(
      isRelevantArticle(
        article({
          sourceId: 'gsmarena',
          sourceName: 'GSMArena',
          title: 'Weekly poll results',
          summary: 'Readers voted for their favorite handset of the month.',
        }),
      ),
    ).toBe(true);
  });

  it('blocks Mac news from Apple sources', () => {
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
      link: 'https://example.com/news/1',
      publishedAt: new Date('2026-08-30T10:00:00.000Z'),
    };

    const post = formatTelegramPost(article);
    expect(post).toContain('گلکسی S26');
    expect(post).toContain('GSMArena');
    expect(post).toContain('مشخصات فنی');
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
