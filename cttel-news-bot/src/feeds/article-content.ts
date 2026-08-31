const FETCH_HEADERS = {
  'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
  Accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
  'Accept-Language': 'en-US,en;q=0.9',
};

const MAX_BODY_CHARS = 8_000;
const MIN_USEFUL_BODY_CHARS = 280;

function decodeHtmlEntities(value: string): string {
  return value
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&#x27;/g, "'")
    .replace(/&#(\d+);/g, (_, code: string) => String.fromCharCode(Number(code)));
}

export function stripHtml(value: string): string {
  return decodeHtmlEntities(
    value
      .replace(/<!\[CDATA\[([\s\S]*?)]]>/g, '$1')
      .replace(/<br\s*\/?>/gi, '\n')
      .replace(/<\/p>/gi, '\n\n')
      .replace(/<[^>]+>/g, ' ')
      .replace(/\r/g, '')
      .replace(/[ \t]+\n/g, '\n')
      .replace(/\n{3,}/g, '\n\n')
      .replace(/[ \t]{2,}/g, ' ')
      .trim(),
  );
}

function normalizeBody(text: string): string {
  return text.replace(/\n{3,}/g, '\n\n').trim().slice(0, MAX_BODY_CHARS);
}

function extractParagraphsFromHtml(html: string): string {
  const withoutNoise = html
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<noscript[\s\S]*?<\/noscript>/gi, ' ')
    .replace(/<!--[\s\S]*?-->/g, ' ');

  const scoped =
    /<article[\s\S]*?>([\s\S]*?)<\/article>/i.exec(withoutNoise)?.[1] ??
    /class=["'][^"']*(?:entry-content|article-body|post-content|content-body|article__content)[^"']*["'][^>]*>([\s\S]*?)<\/div>/i.exec(
      withoutNoise,
    )?.[1] ??
    withoutNoise;

  const paragraphs: string[] = [];
  const paragraphPattern = /<p[^>]*>([\s\S]*?)<\/p>/gi;
  let match = paragraphPattern.exec(scoped);
  while (match !== null) {
    const text = stripHtml(match[1] ?? '');
    if (text.length >= 40) {
      paragraphs.push(text);
    }
    match = paragraphPattern.exec(scoped);
  }

  if (paragraphs.length >= 2) {
    return normalizeBody(paragraphs.join('\n\n'));
  }

  const fallback = stripHtml(scoped);
  return normalizeBody(fallback);
}

async function fetchHtml(url: string): Promise<string | undefined> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 20_000);

  try {
    const response = await fetch(url, {
      headers: FETCH_HEADERS,
      signal: controller.signal,
      redirect: 'follow',
    });

    if (!response.ok) {
      return undefined;
    }

    const contentType = response.headers.get('content-type') ?? '';
    if (!contentType.includes('text/html') && !contentType.includes('application/xhtml')) {
      return undefined;
    }

    return await response.text();
  } catch {
    return undefined;
  } finally {
    clearTimeout(timeout);
  }
}

export async function fetchArticleBody(link: string, bodyHtml?: string, summary?: string): Promise<string> {
  if (bodyHtml !== undefined && bodyHtml.includes('<')) {
    const fromRss = extractParagraphsFromHtml(bodyHtml);
    if (fromRss.length >= MIN_USEFUL_BODY_CHARS) {
      return fromRss;
    }
  }

  const html = await fetchHtml(link);
  if (html !== undefined) {
    const extracted = extractParagraphsFromHtml(html);
    if (extracted.length >= MIN_USEFUL_BODY_CHARS) {
      return extracted;
    }
  }

  const fallback = normalizeBody(summary ?? '');
  return fallback.length >= 80 ? fallback : summary ?? '';
}
