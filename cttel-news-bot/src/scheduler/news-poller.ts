import type { Env } from '../config/env.js';
import { parseFeedUrls } from '../config/env.js';
import { resolveSources } from '../config/sources.js';
import { fetchLatestArticles } from '../feeds/rss-fetcher.js';
import type { TelegramPublisher } from '../publisher/telegram-publisher.js';
import type { SeenStore } from '../store/seen-store.js';
import { Translator } from '../translate/translator.js';
import type { Logger } from '../utils/logger.js';

export class NewsPoller {
  private readonly translator: Translator;

  constructor(
    private readonly env: Env,
    private readonly seenStore: SeenStore,
    private readonly publisher: TelegramPublisher,
    private readonly logger: Logger,
  ) {
    this.translator = new Translator(env);
  }

  async runOnce(): Promise<number> {
    const sources = resolveSources(parseFeedUrls(this.env.FEED_URLS));
    const articles = await fetchLatestArticles(sources);
    const fresh = articles.filter((article) => !this.seenStore.has(article.id));

    if (fresh.length === 0) {
      this.logger.info('No new articles found');
      return 0;
    }

    const toPublish = fresh.slice(0, this.env.MAX_POSTS_PER_RUN);
    let published = 0;

    for (const article of toPublish) {
      try {
        const translated = await this.translator.translate(article);
        await this.publisher.publish(translated);
        await this.seenStore.markSeen(article.id);
        published += 1;
        this.logger.info('Published article', {
          id: article.id,
          source: article.sourceName,
          title: article.title,
        });
      } catch (error) {
        this.logger.error('Failed to publish article', {
          id: article.id,
          source: article.sourceName,
          error: String(error),
        });
      }
    }

    return published;
  }
}
