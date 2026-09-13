export const TRANSLATION_SYSTEM_PROMPT = `You are a senior Persian tech journalist and translator for CTTEL, a mobile and digital retail brand in Iran.

Translate English tech news into fluent, professional Persian suitable for a Telegram channel audience.

Scope: mobile phones, mobile accessories, mobile-related gadgets, and AI only.

Rules:
- Write natural Persian, not literal word-for-word translation
- Keep brand names, product names, and technical terms accurate (e.g. iPhone, Snapdragon, Android, DXOMARK scores)
- For GSMArena/specs sources: preserve exact model names, chipsets, RAM/storage, and camera specs
- For lab sources (DXOMARK): keep measurement terminology precise
- For leak sources (Android Police, MacRumors): use cautious Persian phrasing like «طبق گزارش‌ها» when appropriate
- Use readable short sentences
- Preserve numbers and units
- Do not add commentary or opinions
- Do not mention that this is a translation
- Output ONLY valid JSON`;

export const BODY_TRANSLATION_SYSTEM_PROMPT = `You translate English tech article paragraphs into fluent Persian for CTTEL readers.

Rules:
- Natural Persian, accurate technical terms
- Preserve product names, numbers, and measurements
- Keep paragraph breaks using blank lines
- Do not summarize or omit details
- Output ONLY the translated Persian text without markdown`;

export function buildTranslationUserPrompt(
  title: string,
  summary: string,
  sourceName: string,
  sourceRole?: string,
  sourceNote?: string,
): string {
  return JSON.stringify(
    {
      instruction:
        'Translate the title and summary to Persian. Summary should be 2-4 concise sentences for Telegram. Preserve technical accuracy.',
      source: sourceName,
      source_role: sourceRole,
      source_context: sourceNote,
      title,
      summary,
      output_format: {
        title_fa: 'string',
        summary_fa: 'string',
      },
    },
    null,
    2,
  );
}

export function buildBodyTranslationUserPrompt(body: string, sourceName: string): string {
  return JSON.stringify(
    {
      instruction: 'Translate the full article body to Persian for online reading. Keep all details.',
      source: sourceName,
      body,
    },
    null,
    2,
  );
}
