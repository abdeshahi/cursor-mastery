export interface NewsSource {
  id: string;
  name: string;
  url: string;
  category: 'mobile' | 'tech' | 'ai' | 'general';
}

/** Default RSS feeds for mobile/tech news. Override with FEED_URLS in .env */
export const DEFAULT_NEWS_SOURCES: NewsSource[] = [
  {
    id: 'gsmarena',
    name: 'GSMArena',
    url: 'https://www.gsmarena.com/rss-news-reviews.php3',
    category: 'mobile',
  },
  {
    id: 'theverge',
    name: 'The Verge',
    url: 'https://www.theverge.com/rss/index.xml',
    category: 'tech',
  },
  {
    id: 'techcrunch',
    name: 'TechCrunch',
    url: 'https://techcrunch.com/feed/',
    category: 'tech',
  },
  {
    id: '9to5google',
    name: '9to5Google',
    url: 'https://9to5google.com/feed/',
    category: 'mobile',
  },
  {
    id: 'androidauthority',
    name: 'Android Authority',
    url: 'https://www.androidauthority.com/feed/',
    category: 'mobile',
  },
  {
    id: 'engadget',
    name: 'Engadget',
    url: 'https://www.engadget.com/rss.xml',
    category: 'tech',
  },
];

export function resolveSources(feedUrls: string[]): NewsSource[] {
  if (feedUrls.length === 0) {
    return DEFAULT_NEWS_SOURCES;
  }

  return feedUrls.map((url, index) => {
    let hostname = `source-${String(index + 1)}`;
    try {
      hostname = new URL(url).hostname.replace(/^www\./, '');
    } catch {
      // keep fallback id
    }

    return {
      id: hostname.replace(/\./g, '-'),
      name: hostname,
      url,
      category: 'general',
    };
  });
}
