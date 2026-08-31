import type { Env } from '../config/env.js';
import type { RawArticle, TranslatedArticle } from '../feeds/article.js';
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
