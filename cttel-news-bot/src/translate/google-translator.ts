import { translate } from '@vitalets/google-translate-api';
import type { RawArticle, TranslatedArticle } from '../feeds/article.js';
import { findSourceById, SOURCE_ROLE_LABELS_FA } from '../config/sources.js';

function polishPersian(text: string): string {
  return text
    .replace(/\s+/g, ' ')
    .replace(/گلکسی اس/g, 'گلکسی S')
    .replace(/آیفون/g, 'آیفون')
    .trim();
}

function buildSummaryPrompt(summary: string, sourceName: string, roleLabel: string): string {
  return `[Tech news for Persian mobile channel | Source: ${sourceName} | Type: ${roleLabel}] ${summary}`;
}

export class GoogleTranslator {
  async translate(article: RawArticle): Promise<TranslatedArticle> {
    const source = findSourceById(article.sourceId);
    const roleLabel =
      SOURCE_ROLE_LABELS_FA[article.sourceRole as keyof typeof SOURCE_ROLE_LABELS_FA] ??
      article.sourceRole;

    const [titleResult, summaryResult] = await Promise.all([
      translate(article.title, { to: 'fa' }),
      translate(buildSummaryPrompt(article.summary, article.sourceName, roleLabel), { to: 'fa' }),
    ]);

    const titleFa = polishPersian(titleResult.text);
    const summaryFa = polishPersian(summaryResult.text);

    if (titleFa.length === 0 || summaryFa.length === 0) {
      throw new Error('Google translation returned empty text');
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
