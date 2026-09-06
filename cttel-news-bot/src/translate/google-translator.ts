import { translate } from '@vitalets/google-translate-api';
import type { RawArticle, TranslatedArticle } from '../feeds/article.js';
import { findSourceById, SOURCE_ROLE_LABELS_FA } from '../config/sources.js';
import { articleSlug, buildReaderUrl } from '../utils/article-slug.js';
import type { Env } from '../config/env.js';
import { translateTextInChunks } from './chunk-translator.js';

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function polishPersian(text: string): string {
  return text
    .replace(/\s+/g, ' ')
    .replace(/گلکسی اس/g, 'گلکسی S')
    .trim();
}

function buildSummaryPrompt(summary: string, sourceName: string, roleLabel: string): string {
  return `[Tech news for Persian mobile channel | Source: ${sourceName} | Type: ${roleLabel}] ${summary}`;
}

async function translateWithRetry(text: string, attempt = 0): Promise<string> {
  try {
    const result = await translate(text, { to: 'fa' });
    return result.text;
  } catch (error) {
    const message = String(error);
    const isRateLimited = message.includes('Too Many Requests') || message.includes('TooManyRequests');

    if (isRateLimited && attempt < 4) {
      await sleep(2_000 * (attempt + 1));
      return translateWithRetry(text, attempt + 1);
    }

    if (isRateLimited) {
      return translateWithMyMemory(text);
    }

    throw error;
  }
}

async function translateWithMyMemory(text: string): Promise<string> {
  const url = new URL('https://api.mymemory.translated.net/get');
  url.searchParams.set('q', text.slice(0, 500));
  url.searchParams.set('langpair', 'en|fa');

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`MyMemory translation failed (${String(response.status)})`);
  }

  const payload = (await response.json()) as { responseData?: { translatedText?: string } };
  const translated = payload.responseData?.translatedText?.trim();
  if (translated === undefined || translated === '') {
    throw new Error('MyMemory translation returned empty text');
  }

  return translated;
}

export class GoogleTranslator {
  constructor(private readonly env: Env) {}

  async translate(article: RawArticle): Promise<TranslatedArticle> {
    const source = findSourceById(article.sourceId);
    const roleLabel =
      SOURCE_ROLE_LABELS_FA[article.sourceRole as keyof typeof SOURCE_ROLE_LABELS_FA] ??
      article.sourceRole;

    const titleFa = polishPersian(await translateWithRetry(article.title));
    await sleep(1_500);
    const summaryFa = polishPersian(
      await translateWithRetry(buildSummaryPrompt(article.summary, article.sourceName, roleLabel)),
    );

    if (titleFa.length === 0 || summaryFa.length === 0) {
      throw new Error('Translation returned empty text');
    }

    const bodySource = article.bodyText ?? article.summary;
    let bodyFa = summaryFa;
    try {
      bodyFa = polishPersian(
        await translateTextInChunks(bodySource, async (chunk) => translateWithRetry(chunk)),
      );
      if (bodyFa.length === 0) {
        bodyFa = summaryFa;
      }
    } catch {
      bodyFa = summaryFa;
    }

    const slug = articleSlug(article.id);

    return {
      id: article.id,
      sourceId: article.sourceId,
      sourceName: article.sourceName,
      sourceRole: article.sourceRole,
      titleFa,
      summaryFa,
      bodyFa,
      link: article.link,
      slug,
      readerUrl: buildReaderUrl(this.env.PUBLIC_BASE_URL, slug),
      publishedAt: article.publishedAt,
      imageUrl: article.imageUrl,
    };
  }
}
