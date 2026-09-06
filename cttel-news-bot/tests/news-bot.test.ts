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
    expect(DEFAULT_NEWS_SOURCES.some((source) => source.enabled)).toBe(true);
    expect(DEFAULT_NEWS_SOURCES.filter((source) => source.enabled).length).toBeGreaterThan(10);
  });

  it('resolves only enabled sources by default', () => {
    const enabledCount = DEFAULT_NEWS_SOURCES.filter((source) => source.enabled).length;
    expect(resolveSources([]).length).toBe(enabledCount);
    expect(enabledCount).toBe(24);
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
  it('allows Iranian ICT news about mobile, internet, registry, AI, or operators', () => {
    expect(
      isRelevantArticle(
        article({
          sourceId: 'citna',
          sourceName: 'سیتنا',
          title: 'افزایش تعرفه اینترنت همراه',
          summary: 'اپراتورها از وزارت ارتباطات مجوز گرفتند.',
        }),
      ),
    ).toBe(true);

    expect(
      evaluateArticleTopic(
        article({
          sourceId: 'zoomit',
          sourceName: 'زومیت',
          title: 'رجیستری گوشی‌های جدید در سامانه همتا',
          summary: 'ثبت HWI برای واردات موبایل',
        }),
      ).reason,
    ).toBe('iran-ict-topic');
  });

  it('blocks unrelated Iranian political or economic news', () => {
    expect(
      evaluateArticleTopic(
        article({
          sourceId: 'irna-sci',
          sourceName: 'ایرنا',
          title: 'رشد صادرات کشاورزی',
          summary: 'بازار داخلی و صادرات غیرنفتی',
        }),
      ).allowed,
    ).toBe(false);

    expect(
      evaluateArticleTopic(
        article({
          sourceId: 'mehr-sci',
          sourceName: 'مهر',
          title: 'پیروزی تیم ملی فوتبال',
          summary: 'ورزش',
        }),
      ).reason,
    ).toBe('no-iran-ict-topic');
  });

  it('allows Iranian AI and operator network news', () => {
    expect(
      isRelevantArticle(
        article({
          sourceId: 'ictnews',
          sourceName: 'آی‌سی‌تی‌نیوز',
          title: 'سرمایه‌گذاری در هوش مصنوعی بومی',
          summary: 'شبکه اپراتور همراه برای سرویس‌های AI',
        }),
      ),
    ).toBe(true);
  });

  it('blocks miscategorized Iranian military or political news', () => {
    expect(
      evaluateArticleTopic(
        article({
          sourceId: 'khabaronline-ict',
          sourceName: 'خبرآنلاین',
          title: 'ببینید | سردار نقدی: بیش از ۹۰ درصد ذخایر موشکی ایران دست‌نخورده باقی مانده است',
          summary: 'سردار محمدرضا نقدی مشاور فرمانده کل سپاه صحبت کرد',
        }),
      ).allowed,
    ).toBe(false);

    expect(
      evaluateArticleTopic(
        article({
          sourceId: 'khabaronline-ict',
          sourceName: 'خبرآنلاین',
          title: 'چرا ترامپ ویدیوی بمباران جزیره خارک که با هوش مصنوعی ساخته شده را منتشر کرد؟',
          summary: 'ترامپ در شبکه‌های اجتماعی پیام سیاسی داد',
        }),
      ).allowed,
    ).toBe(false);
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
  it('formats a Persian native post with source link only', () => {
    const article: TranslatedArticle = {
      id: 'test:2',
      sourceId: 'citna',
      sourceName: 'سیتنا',
      sourceRole: 'news',
      titleFa: 'افزایش پوشش اینترنت پرسرعت',
      summaryFa: 'وزارت ارتباطات از گسترش شبکه در مناطق روستایی خبر داد.',
      bodyFa: 'وزارت ارتباطات از گسترش شبکه در مناطق روستایی خبر داد.',
      link: 'https://www.citna.ir/news/example',
      slug: 'abc123def456',
      readerUrl: 'http://185.18.214.66:3002/read/abc123def456',
      nativePersian: true,
    };

    const post = formatTelegramPost(article);
    expect(post).toContain('افزایش پوشش اینترنت پرسرعت');
    expect(post).toContain('مطالعه در منبع');
    expect(post).toContain('https://www.citna.ir/news/example');
    expect(post).not.toContain('مطالعه کامل به فارسی');
    expect(post).not.toContain('منبع انگلیسی');
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
