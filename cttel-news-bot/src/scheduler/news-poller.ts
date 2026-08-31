import type { Env } from '../config/env.js';
import { parseFeedUrls } from '../config/env.js';
import { resolveSources } from '../config/sources.js';
import { evaluateArticleTopic } from '../filter/topic-filter.js';
import { fetchLatestArticles } from '../feeds/rss-fetcher.js';
import type { TelegramPublisher } from '../publisher/telegram-publisher.js';
import type { SeenStore } from '../store/seen-store.js';
import { Translator } from '../translate/translator.js';
import type { Logger } from '../utils/logger.js';

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

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

    let published = 0;

    for (const article of fresh) {
      if (published >= this.env.MAX_POSTS_PER_RUN) {
        break;
      }

      const topic = evaluateArticleTopic(article);
      if (!topic.allowed) {
        await this.seenStore.markSeen(article.id);
        this.logger.info('Skipped off-topic article', {
          id: article.id,
          source: article.sourceName,
          title: article.title,
          reason: topic.reason,
        });
        continue;
      }

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
        await sleep(2_000);
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
