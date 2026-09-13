import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import type { StoredArticle } from '../feeds/article.js';

export class ArticleStore {
  private readonly articlesDir: string;

  private constructor(articlesDir: string) {
    this.articlesDir = articlesDir;
  }

  static async open(dataDir: string): Promise<ArticleStore> {
    const articlesDir = path.join(dataDir, 'articles');
    await mkdir(articlesDir, { recursive: true });
    return new ArticleStore(articlesDir);
  }

  async save(article: StoredArticle): Promise<void> {
    const filePath = path.join(this.articlesDir, `${article.slug}.json`);
    await writeFile(filePath, JSON.stringify(article, null, 2), 'utf8');
  }

  async get(slug: string): Promise<StoredArticle | undefined> {
    try {
      const raw = await readFile(path.join(this.articlesDir, `${slug}.json`), 'utf8');
      return JSON.parse(raw) as StoredArticle;
    } catch {
      return undefined;
    }
  }
}
