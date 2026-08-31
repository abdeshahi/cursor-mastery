import type { Env } from '../config/env.js';
import type { RawArticle, TranslatedArticle } from '../feeds/article.js';
import { GoogleTranslator } from './google-translator.js';
import { OpenAiTranslator } from './openai-translator.js';

export class Translator {
  private readonly backend: GoogleTranslator | OpenAiTranslator;

  constructor(env: Env) {
    this.backend = env.TRANSLATION_PROVIDER === 'openai' ? new OpenAiTranslator(env) : new GoogleTranslator(env);
  }

  translate(article: RawArticle): Promise<TranslatedArticle> {
    return this.backend.translate(article);
  }
}
