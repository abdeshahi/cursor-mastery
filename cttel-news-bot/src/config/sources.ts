export type SourceRole =
  | 'specs'
  | 'review'
  | 'news'
  | 'leaks'
  | 'apple'
  | 'lab'
  | 'buyers-guide';

export interface NewsSource {
  id: string;
  name: string;
  url: string;
  role: SourceRole;
  /** Lower number = higher editorial priority when ranking sources */
  priority: number;
  note: string;
}

/** Curated mobile/tech sources for CTTEL channel. Override with FEED_URLS in .env */
export const DEFAULT_NEWS_SOURCES: NewsSource[] = [
  {
    id: 'gsmarena',
    name: 'GSMArena',
    url: 'https://www.gsmarena.com/rss-news-reviews.php3',
    role: 'specs',
    priority: 1,
    note: 'Primary reference for phone specs, comparisons, and fast mobile news',
  },
  {
    id: 'android-authority',
    name: 'Android Authority',
    url: 'https://www.androidauthority.com/feed/',
    role: 'review',
    priority: 2,
    note: 'Android coverage, video reviews, and buying guides',
  },
  {
    id: 'phonearena',
    name: 'PhoneArena',
    url: 'https://www.phonearena.com/feed/news',
    role: 'review',
    priority: 3,
    note: 'Hands-on reviews, comparison tools, and tested scores',
  },
  {
    id: 'theverge',
    name: 'The Verge',
    url: 'https://www.theverge.com/rss/index.xml',
    role: 'news',
    priority: 4,
    note: 'Fast gadget news and high-quality product analysis',
  },
  {
    id: 'engadget',
    name: 'Engadget',
    url: 'https://www.engadget.com/rss.xml',
    role: 'news',
    priority: 5,
    note: 'Fast gadget news and product analysis',
  },
  {
    id: 'cnet',
    name: 'CNET',
    url: 'https://www.cnet.com/rss/news/mobile/',
    role: 'buyers-guide',
    priority: 6,
    note: 'Mobile news, reviews, and buying guides',
  },
  {
    id: 'techradar',
    name: 'TechRadar',
    url: 'https://www.techradar.com/feeds/tag/phones',
    role: 'buyers-guide',
    priority: 7,
    note: 'Phone reviews and buying guides',
  },
  {
    id: 'android-police',
    name: 'Android Police',
    url: 'https://androidpolice.com/feed',
    role: 'leaks',
    priority: 8,
    note: 'Leaks, teasers, and pre-launch Android news',
  },
  {
    id: '9to5google',
    name: '9to5Google',
    url: 'https://9to5google.com/feed/',
    role: 'news',
    priority: 9,
    note: 'Google, Pixel, and Android ecosystem news',
  },
  {
    id: '9to5mac',
    name: '9to5Mac',
    url: 'https://9to5mac.com/feed/',
    role: 'apple',
    priority: 10,
    note: 'Apple hardware and software news',
  },
  {
    id: 'macrumors',
    name: 'MacRumors',
    url: 'https://www.macrumors.com/macrumors.xml',
    role: 'apple',
    priority: 11,
    note: 'Apple rumors, leaks, and launch coverage',
  },
  {
    id: 'dxomark',
    name: 'DXOMARK',
    url: 'https://www.dxomark.com/feed/',
    role: 'lab',
    priority: 12,
    note: 'Lab camera, audio, display, and battery test results',
  },
];

export const SOURCE_ROLE_LABELS_FA: Record<SourceRole, string> = {
  specs: 'مشخصات فنی',
  review: 'بررسی تخصصی',
  news: 'خبر گجت',
  leaks: 'لیك و پیش‌رونمایی',
  apple: 'اکوسیستم اپل',
  lab: 'تست آزمایشگاهی',
  'buyers-guide': 'راهنمای خرید',
};

export function resolveSources(feedUrls: string[]): NewsSource[] {
  if (feedUrls.length === 0) {
    return [...DEFAULT_NEWS_SOURCES].sort((left, right) => left.priority - right.priority);
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
      role: 'news',
      priority: 100 + index,
      note: 'Custom feed URL',
    };
  });
}

export function findSourceById(sourceId: string): NewsSource | undefined {
  return DEFAULT_NEWS_SOURCES.find((source) => source.id === sourceId);
}
