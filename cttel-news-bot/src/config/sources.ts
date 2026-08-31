export type SourceRole =
  | 'specs'
  | 'review'
  | 'news'
  | 'leaks'
  | 'apple'
  | 'lab'
  | 'buyers-guide';

export type SourceRegion = 'intl' | 'ir';
export type SourceFormat = 'rss' | 'html';

export interface NewsSource {
  id: string;
  name: string;
  url: string;
  siteUrl?: string;
  role: SourceRole;
  /** Lower number = higher editorial priority when ranking sources */
  priority: number;
  note: string;
  enabled: boolean;
  region: SourceRegion;
  format?: SourceFormat;
}

/** Curated mobile/tech sources for CTTEL channel. Override with FEED_URLS in .env */
export const DEFAULT_NEWS_SOURCES: NewsSource[] = [
  // --- International (filtered to Samsung, Apple, Xiaomi, Nothing, Honor) ---
  {
    id: 'gsmarena',
    name: 'GSMArena',
    url: 'https://www.gsmarena.com/rss-news-reviews.php3',
    siteUrl: 'https://www.gsmarena.com',
    role: 'specs',
    priority: 1,
    note: 'Primary reference for phone specs, comparisons, and fast mobile news',
    enabled: true,
    region: 'intl',
    format: 'rss',
  },
  {
    id: 'android-authority',
    name: 'Android Authority',
    url: 'https://www.androidauthority.com/feed/',
    siteUrl: 'https://www.androidauthority.com',
    role: 'review',
    priority: 2,
    note: 'Android coverage, video reviews, and buying guides',
    enabled: true,
    region: 'intl',
    format: 'rss',
  },
  {
    id: 'phonearena',
    name: 'PhoneArena',
    url: 'https://www.phonearena.com/feed/news',
    siteUrl: 'https://www.phonearena.com',
    role: 'review',
    priority: 3,
    note: 'Hands-on reviews, comparison tools, and tested scores',
    enabled: true,
    region: 'intl',
    format: 'rss',
  },
  {
    id: 'theverge',
    name: 'The Verge',
    url: 'https://www.theverge.com/rss/index.xml',
    siteUrl: 'https://www.theverge.com',
    role: 'news',
    priority: 4,
    note: 'Fast gadget news and high-quality product analysis',
    enabled: true,
    region: 'intl',
    format: 'rss',
  },
  {
    id: 'engadget',
    name: 'Engadget',
    url: 'https://www.engadget.com/rss.xml',
    siteUrl: 'https://www.engadget.com',
    role: 'news',
    priority: 5,
    note: 'Fast gadget news and product analysis',
    enabled: true,
    region: 'intl',
    format: 'rss',
  },
  {
    id: 'cnet',
    name: 'CNET',
    url: 'https://www.cnet.com/rss/news/mobile/',
    siteUrl: 'https://www.cnet.com',
    role: 'buyers-guide',
    priority: 6,
    note: 'Mobile news, reviews, and buying guides',
    enabled: true,
    region: 'intl',
    format: 'rss',
  },
  {
    id: 'techradar',
    name: 'TechRadar',
    url: 'https://www.techradar.com/feeds/tag/phones',
    siteUrl: 'https://www.techradar.com',
    role: 'buyers-guide',
    priority: 7,
    note: 'Phone reviews and buying guides',
    enabled: true,
    region: 'intl',
    format: 'rss',
  },
  {
    id: 'android-police',
    name: 'Android Police',
    url: 'https://androidpolice.com/feed',
    siteUrl: 'https://androidpolice.com',
    role: 'leaks',
    priority: 8,
    note: 'Leaks, teasers, and pre-launch Android news',
    enabled: true,
    region: 'intl',
    format: 'rss',
  },
  {
    id: '9to5google',
    name: '9to5Google',
    url: 'https://9to5google.com/feed/',
    siteUrl: 'https://9to5google.com',
    role: 'news',
    priority: 9,
    note: 'Google, Pixel, and Android ecosystem news',
    enabled: true,
    region: 'intl',
    format: 'rss',
  },
  {
    id: '9to5mac',
    name: '9to5Mac',
    url: 'https://9to5mac.com/feed/',
    siteUrl: 'https://9to5mac.com',
    role: 'apple',
    priority: 10,
    note: 'Apple hardware and software news',
    enabled: true,
    region: 'intl',
    format: 'rss',
  },
  {
    id: 'macrumors',
    name: 'MacRumors',
    url: 'https://www.macrumors.com/macrumors.xml',
    siteUrl: 'https://www.macrumors.com',
    role: 'apple',
    priority: 11,
    note: 'Apple rumors, leaks, and launch coverage',
    enabled: true,
    region: 'intl',
    format: 'rss',
  },
  {
    id: 'dxomark',
    name: 'DXOMARK',
    url: 'https://www.dxomark.com/feed/',
    siteUrl: 'https://www.dxomark.com',
    role: 'lab',
    priority: 12,
    note: 'Lab camera, audio, display, and battery test results',
    enabled: true,
    region: 'intl',
    format: 'rss',
  },

  // --- Iran: official & regulatory ---
  {
    id: 'ict-gov',
    name: 'وزارت ارتباطات',
    url: 'https://ict.gov.ir/fa/news/rss',
    siteUrl: 'https://ict.gov.ir',
    role: 'news',
    priority: 100,
    note: 'Official ICT ministry news',
    enabled: true,
    region: 'ir',
    format: 'rss',
  },
  {
    id: 'cra',
    name: 'سازمان تنظیم مقررات',
    url: 'https://www.cra.ir/fa/news',
    siteUrl: 'https://www.cra.ir',
    role: 'news',
    priority: 101,
    note: 'CRA regulatory and telecom news',
    enabled: true,
    region: 'ir',
    format: 'html',
  },
  {
    id: 'tci',
    name: 'مخابرات ایران',
    url: 'https://www.tci.ir/fa/news',
    siteUrl: 'https://www.tci.ir',
    role: 'news',
    priority: 102,
    note: 'Telecom Iran corporate news',
    enabled: true,
    region: 'ir',
    format: 'html',
  },

  // --- Iran: ICT / telecom media ---
  {
    id: 'citna',
    name: 'سیتنا',
    url: 'https://www.citna.ir/rss',
    siteUrl: 'https://www.citna.ir',
    role: 'news',
    priority: 110,
    note: 'Iran ICT and telecom news',
    enabled: true,
    region: 'ir',
    format: 'rss',
  },
  {
    id: 'peivast',
    name: 'پیوست',
    url: 'https://peivast.com/feed/',
    siteUrl: 'https://peivast.com',
    role: 'news',
    priority: 111,
    note: 'Iran ICT business and telecom media',
    enabled: true,
    region: 'ir',
    format: 'rss',
  },
  {
    id: 'ictnews',
    name: 'آی‌سی‌تی‌نیوز',
    url: 'https://ictnews.ir/feed/',
    siteUrl: 'https://ictnews.ir',
    role: 'news',
    priority: 112,
    note: 'Iran ICT news',
    enabled: true,
    region: 'ir',
    format: 'rss',
  },
  {
    id: 'asreertebat',
    name: 'عصر ارتباط',
    url: 'https://asreertebat.com/feed/',
    siteUrl: 'https://asreertebat.com',
    role: 'news',
    priority: 113,
    note: 'Iran telecom weekly and ICT media',
    enabled: true,
    region: 'ir',
    format: 'rss',
  },

  // --- Iran: mobile & market ---
  {
    id: 'digiato',
    name: 'دیجیاتو',
    url: 'https://digiato.com/feed/',
    siteUrl: 'https://digiato.com',
    role: 'news',
    priority: 120,
    note: 'Iran mobile and tech news',
    enabled: true,
    region: 'ir',
    format: 'rss',
  },
  {
    id: 'zoomit',
    name: 'زومیت',
    url: 'https://www.zoomit.ir/feed/',
    siteUrl: 'https://www.zoomit.ir',
    role: 'news',
    priority: 121,
    note: 'Iran tech and mobile news',
    enabled: true,
    region: 'ir',
    format: 'rss',
  },
  {
    id: 'gsm-ir',
    name: 'GSM.ir',
    url: 'https://www.gsm.ir/mag/category/news/feed/',
    siteUrl: 'https://gsm.ir',
    role: 'news',
    priority: 122,
    note: 'Iran mobile market news',
    enabled: true,
    region: 'ir',
    format: 'rss',
  },
  {
    id: 'mobile-ir',
    name: 'موبایل.آی‌آر',
    url: 'https://www.mobile.ir/news/rss.aspx',
    siteUrl: 'https://www.mobile.ir',
    role: 'news',
    priority: 123,
    note: 'Iran mobile industry news',
    enabled: true,
    region: 'ir',
    format: 'rss',
  },

  // --- Iran: agencies (tech/science sections) ---
  {
    id: 'irna-sci',
    name: 'ایرنا · علم و فناوری',
    url: 'https://www.irna.ir/rss?plq=sci',
    siteUrl: 'https://www.irna.ir/service/sci',
    role: 'news',
    priority: 130,
    note: 'IRNA science and technology',
    enabled: false,
    region: 'ir',
    format: 'rss',
  },
  {
    id: 'isna-sci',
    name: 'ایسنا · علم و فناوری',
    url: 'https://www.isna.ir/rss/tp/science',
    siteUrl: 'https://www.isna.ir/service/Science',
    role: 'news',
    priority: 131,
    note: 'ISNA science and technology',
    enabled: false,
    region: 'ir',
    format: 'rss',
  },
  {
    id: 'mehr-sci',
    name: 'مهر · دانش و فناوری',
    url: 'https://www.mehrnews.com/rss?k=sci',
    siteUrl: 'https://www.mehrnews.com/service/sci',
    role: 'news',
    priority: 132,
    note: 'Mehr science and technology',
    enabled: false,
    region: 'ir',
    format: 'rss',
  },
  {
    id: 'tasnim-tech',
    name: 'تسنیم · فناوری',
    url: 'https://www.tasnimnews.com/fa/service/14',
    siteUrl: 'https://www.tasnimnews.com/fa/service/14',
    role: 'news',
    priority: 133,
    note: 'Tasnim technology section',
    enabled: false,
    region: 'ir',
    format: 'html',
  },
  {
    id: 'fars-sci',
    name: 'فارس · فناوری',
    url: 'https://www.farsnews.ir/science',
    siteUrl: 'https://www.farsnews.ir/science',
    role: 'news',
    priority: 134,
    note: 'Fars science and technology',
    enabled: false,
    region: 'ir',
    format: 'html',
  },
  {
    id: 'khabaronline-ict',
    name: 'خبرآنلاین · فناوری',
    url: 'https://www.khabaronline.ir/rss/tp/ict',
    siteUrl: 'https://www.khabaronline.ir/service/ict',
    role: 'news',
    priority: 135,
    note: 'Khabar Online ICT section',
    enabled: false,
    region: 'ir',
    format: 'rss',
  },

  // --- Iran: AI ---
  {
    id: 'isti',
    name: 'معاونت علمی ریاست جمهوری',
    url: 'https://www.isti.ir/fa/news',
    siteUrl: 'https://www.isti.ir',
    role: 'news',
    priority: 140,
    note: 'Vice Presidency for science and technology affairs',
    enabled: true,
    region: 'ir',
    format: 'html',
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
    return [...DEFAULT_NEWS_SOURCES]
      .filter((source) => source.enabled)
      .sort((left, right) => left.priority - right.priority);
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
      enabled: true,
      region: 'ir',
      format: 'rss',
    };
  });
}

export function findSourceById(sourceId: string): NewsSource | undefined {
  return DEFAULT_NEWS_SOURCES.find((source) => source.id === sourceId);
}

export function isIranSource(sourceId: string): boolean {
  return findSourceById(sourceId)?.region === 'ir';
}
