import type { Env } from '../config/env.js';
import { findSourceById, SOURCE_ROLE_LABELS_FA } from '../config/sources.js';
import type { RawArticle, TranslatedArticle } from '../feeds/article.js';
import {
  buildTranslationUserPrompt,
  TRANSLATION_SYSTEM_PROMPT,
} from './prompts.js';

interface TranslationResponse {
  title_fa?: string;
  summary_fa?: string;
}

export class Translator {
  constructor(private readonly env: Env) {}

  async translate(article: RawArticle): Promise<TranslatedArticle> {
    const source = findSourceById(article.sourceId);
    const roleLabel = SOURCE_ROLE_LABELS_FA[article.sourceRole as keyof typeof SOURCE_ROLE_LABELS_FA] ?? article.sourceRole;

    const response = await fetch(`${this.env.OPENAI_BASE_URL}/chat/completions`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${this.env.OPENAI_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: this.env.OPENAI_MODEL,
        temperature: 0.3,
        response_format: { type: 'json_object' },
        messages: [
          { role: 'system', content: TRANSLATION_SYSTEM_PROMPT },
          {
            role: 'user',
            content: buildTranslationUserPrompt(
              article.title,
              article.summary,
              article.sourceName,
              roleLabel,
              source?.note,
            ),
          },
        ],
      }),
    });

    if (!response.ok) {
      const body = await response.text();
      throw new Error(`Translation API failed (${String(response.status)}): ${body}`);
    }

    const payload = (await response.json()) as {
      choices?: Array<{ message?: { content?: string } }>;
    };
    const content = payload.choices?.[0]?.message?.content;
    if (content === undefined || content.trim() === '') {
      throw new Error('Translation API returned empty content');
    }

    const parsed = JSON.parse(content) as TranslationResponse;
    const titleFa = parsed.title_fa?.trim();
    const summaryFa = parsed.summary_fa?.trim();

    if (titleFa === undefined || titleFa === '' || summaryFa === undefined || summaryFa === '') {
      throw new Error('Translation JSON missing title_fa or summary_fa');
    }

    return {
      id: article.id,
      sourceId: article.sourceId,
      sourceName: article.sourceName,
      sourceRole: article.sourceRole,
      titleFa,
      summaryFa,
      link: article.link,
      publishedAt: article.publishedAt,
      imageUrl: article.imageUrl,
    };
  }
}
