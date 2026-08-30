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
}

export interface TranslatedArticle {
  id: string;
  sourceId: string;
  sourceName: string;
  sourceRole: string;
  titleFa: string;
  summaryFa: string;
  link: string;
  publishedAt?: Date;
  imageUrl?: string;
}
