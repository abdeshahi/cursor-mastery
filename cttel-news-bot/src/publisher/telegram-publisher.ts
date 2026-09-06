import { Telegraf } from 'telegraf';
import { HttpsProxyAgent } from 'https-proxy-agent';
import type { Env } from '../config/env.js';
import type { TranslatedArticle } from '../feeds/article.js';
import { formatTelegramPost } from '../format/post-formatter.js';
import { chunkTelegramMessage } from '../utils/telegram-html.js';
import type { Logger } from '../utils/logger.js';

export class TelegramPublisher {
  private readonly bot: Telegraf;

  constructor(
    private readonly env: Env,
    private readonly logger: Logger,
  ) {
    const agent = env.TELEGRAM_PROXY ? new HttpsProxyAgent(env.TELEGRAM_PROXY) : undefined;
    this.bot = new Telegraf(env.BOT_TOKEN, {
      telegram: agent ? { agent } : undefined,
    });
  }

  async publish(article: TranslatedArticle): Promise<void> {
    const text = formatTelegramPost(article);
    const chunks = chunkTelegramMessage(text);

    if (article.imageUrl !== undefined) {
      try {
        await this.bot.telegram.sendPhoto(this.env.CHANNEL_ID, article.imageUrl, {
          caption: chunks[0],
          parse_mode: 'HTML',
        });

        for (const chunk of chunks.slice(1)) {
          await this.bot.telegram.sendMessage(this.env.CHANNEL_ID, chunk, { parse_mode: 'HTML' });
        }
        return;
      } catch (error) {
        this.logger.warn('Photo publish failed, falling back to text', { error: String(error) });
      }
    }

    for (const chunk of chunks) {
      await this.bot.telegram.sendMessage(this.env.CHANNEL_ID, chunk, { parse_mode: 'HTML' });
    }
  }

  async notifyAdmin(message: string): Promise<void> {
    if (this.env.ADMIN_ID === undefined) {
      return;
    }

    await this.bot.telegram.sendMessage(this.env.ADMIN_ID, message);
  }
}
