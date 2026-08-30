import 'dotenv/config';
import http from 'node:http';
import cron from 'node-cron';
import { loadEnv } from './config/env.js';
import { NewsPoller } from './scheduler/news-poller.js';
import { TelegramPublisher } from './publisher/telegram-publisher.js';
import { SeenStore } from './store/seen-store.js';
import { createLogger } from './utils/logger.js';

async function main(): Promise<void> {
  const env = loadEnv();
  const logger = createLogger(env);
  const seenStore = await SeenStore.open(env.DATA_DIR);
  const publisher = new TelegramPublisher(env, logger);
  const poller = new NewsPoller(env, seenStore, publisher, logger);

  const runPoll = async (): Promise<void> => {
    logger.info('Starting news poll');
    try {
      const count = await poller.runOnce();
      logger.info('News poll finished', { published: count });
    } catch (error) {
      logger.error('News poll crashed', { error: String(error) });
      await publisher.notifyAdmin(`❌ خطا در بات خبر: ${String(error)}`).catch(() => undefined);
    }
  };

  if (process.argv.includes('--once')) {
    const count = await poller.runOnce();
    logger.info('Single poll finished', { published: count });
    return;
  }

  if (env.POLL_ON_START) {
    void runPoll();
  }

  if (!cron.validate(env.POLL_CRON)) {
    throw new Error(`Invalid POLL_CRON expression: ${env.POLL_CRON}`);
  }

  cron.schedule(env.POLL_CRON, () => {
    void runPoll();
  });

  const server = http.createServer((_request, response) => {
    response.writeHead(200, { 'Content-Type': 'application/json' });
    response.end(JSON.stringify({ status: 'ok', service: 'cttel-news-bot' }));
  });

  server.listen(env.PORT, () => {
    logger.info('CTTEL news bot started', {
      port: env.PORT,
      cron: env.POLL_CRON,
      channel: env.CHANNEL_ID,
    });
  });
}

main().catch((error: unknown) => {
  console.error(error);
  process.exit(1);
});
