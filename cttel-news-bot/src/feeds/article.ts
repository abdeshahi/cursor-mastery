export interface RawArticle {
  id: string;
  sourceId: string;
  sourceName: string;
  sourceRole: string;
  title: string;
  summary: string;
  link: string;
  publishedAt?: Date;
  imageUrl?: string;
  bodyHtml?: string;
  bodyText?: string;
}

export interface TranslatedArticle {
  id: string;
  sourceId: string;
  sourceName: string;
  sourceRole: string;
  titleFa: string;
  summaryFa: string;
  bodyFa: string;
  link: string;
  slug: string;
  readerUrl: string;
  publishedAt?: Date;
  imageUrl?: string;
  /** Iranian sources: already Persian, skip translation and reader page */
  nativePersian?: boolean;
}

export interface StoredArticle {
  slug: string;
  id: string;
  titleFa: string;
  summaryFa: string;
  bodyFa: string;
  sourceName: string;
  sourceRole: string;
  sourceLink: string;
  imageUrl?: string;
  publishedAt?: string;
  createdAt: string;
}
