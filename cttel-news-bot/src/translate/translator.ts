import type { Env } from '../config/env.js';
import { isIranSource } from '../config/sources.js';
import type { RawArticle, TranslatedArticle } from '../feeds/article.js';
import { articleSlug, buildReaderUrl } from '../utils/article-slug.js';
import { GoogleTranslator } from './google-translator.js';
import { OpenAiTranslator } from './openai-translator.js';

function shouldUseFallback(error: unknown): boolean {
  const message = String(error).toLowerCase();
  return (
    message.includes('402') ||
    message.includes('429') ||
    message.includes('insufficient_credits') ||
    message.includes('too many requests') ||
    message.includes('rate limit') ||
    message.includes('quota')
  );
}

export class Translator {
  private readonly primary: GoogleTranslator | OpenAiTranslator;
  private readonly fallback: GoogleTranslator;
  private readonly useOpenAiPrimary: boolean;

  constructor(private readonly env: Env) {
    this.fallback = new GoogleTranslator(env);
    this.useOpenAiPrimary = env.TRANSLATION_PROVIDER === 'openai';
    this.primary = this.useOpenAiPrimary ? new OpenAiTranslator(env) : this.fallback;
  }

  async translate(article: RawArticle): Promise<TranslatedArticle> {
    if (isIranSource(article.sourceId)) {
      return preparePersianArticle(article, this.env.PUBLIC_BASE_URL);
    }

    if (!this.useOpenAiPrimary) {
      return this.fallback.translate(article);
    }

    try {
      return await this.primary.translate(article);
    } catch (error) {
      if (!shouldUseFallback(error)) {
        throw error;
      }

      return this.fallback.translate(article);
    }
  }
}

function trimSummary(summary: string, maxLength = 500): string {
  const normalized = summary.replace(/\s+/g, ' ').trim();
  if (normalized.length <= maxLength) {
    return normalized;
  }

  const clipped = normalized.slice(0, maxLength);
  const lastSentence = Math.max(clipped.lastIndexOf('.'), clipped.lastIndexOf('؟'), clipped.lastIndexOf('!'));
  if (lastSentence > maxLength * 0.5) {
    return clipped.slice(0, lastSentence + 1).trim();
  }

  return `${clipped.trim()}…`;
}

export function preparePersianArticle(article: RawArticle, publicBaseUrl: string): TranslatedArticle {
  const slug = articleSlug(article.id);
  return {
    id: article.id,
    sourceId: article.sourceId,
    sourceName: article.sourceName,
    sourceRole: article.sourceRole,
    titleFa: article.title.trim(),
    summaryFa: trimSummary(article.summary),
    bodyFa: article.summary,
    link: article.link,
    slug,
    readerUrl: buildReaderUrl(publicBaseUrl, slug),
    publishedAt: article.publishedAt,
    imageUrl: article.imageUrl,
    nativePersian: true,
  };
}
