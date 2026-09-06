import type { Env } from '../config/env.js';
import { findSourceById, SOURCE_ROLE_LABELS_FA } from '../config/sources.js';
import type { RawArticle, TranslatedArticle } from '../feeds/article.js';
import { articleSlug, buildReaderUrl } from '../utils/article-slug.js';
import { translateTextInChunks } from './chunk-translator.js';
import {
  BODY_TRANSLATION_SYSTEM_PROMPT,
  buildBodyTranslationUserPrompt,
  buildTranslationUserPrompt,
  TRANSLATION_SYSTEM_PROMPT,
} from './prompts.js';

interface TranslationResponse {
  title_fa?: string;
  summary_fa?: string;
}

export class OpenAiTranslator {
  constructor(private readonly env: Env) {}

  async translate(article: RawArticle): Promise<TranslatedArticle> {
    const source = findSourceById(article.sourceId);
    const roleLabel =
      SOURCE_ROLE_LABELS_FA[article.sourceRole as keyof typeof SOURCE_ROLE_LABELS_FA] ??
      article.sourceRole;

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

    const bodySource = article.bodyText ?? article.summary;
    const bodyFa = await this.translateBody(bodySource, article.sourceName, summaryFa);
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

  private async translateBody(body: string, sourceName: string, fallback: string): Promise<string> {
    if (body.trim().length === 0) {
      return fallback;
    }

    try {
      const translated = await translateTextInChunks(body, async (chunk) => {
        const response = await fetch(`${this.env.OPENAI_BASE_URL}/chat/completions`, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${this.env.OPENAI_API_KEY}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            model: this.env.OPENAI_MODEL,
            temperature: 0.3,
            messages: [
              { role: 'system', content: BODY_TRANSLATION_SYSTEM_PROMPT },
              {
                role: 'user',
                content: buildBodyTranslationUserPrompt(chunk, sourceName),
              },
            ],
          }),
        });

        if (!response.ok) {
          const errorBody = await response.text();
          throw new Error(`Body translation failed (${String(response.status)}): ${errorBody}`);
        }

        const payload = (await response.json()) as {
          choices?: Array<{ message?: { content?: string } }>;
        };
        const content = payload.choices?.[0]?.message?.content?.trim();
        if (content === undefined || content === '') {
          throw new Error('Body translation returned empty content');
        }

        return content;
      });

      return translated.length > 0 ? translated : fallback;
    } catch {
      return fallback;
    }
  }
}
