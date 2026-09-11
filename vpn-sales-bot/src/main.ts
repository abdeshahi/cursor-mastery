import { createBot } from './bot/create-bot.js';
import { startHealthServer } from './bot/health-server.js';
import { loadEnvironment } from './config/env.js';
import { createLogger } from './config/logger.js';
import { createPool } from './database/client.js';
import { runMigrations } from './database/migrate.js';
import { Repositories } from './database/repositories.js';
import { MarzbanClient } from './marzban/client.js';
import { ProvisioningService, type Notifier } from './services/provisioning-service.js';
import { SalesService } from './services/sales-service.js';

async function main(): Promise<void> {
  const env = loadEnvironment();
  const logger = createLogger(env.LOG_LEVEL);
  const pool = createPool(env.DATABASE_URL);
  const db = new Repositories(pool);

  const applied = await runMigrations(pool);
  if (applied.length > 0) {
    logger.info('migrations.applied', { applied });
  }

  const marzban = new MarzbanClient({
    baseUrl: env.MARZBAN_BASE_URL,
    username: env.MARZBAN_USERNAME,
    password: env.MARZBAN_PASSWORD,
    timeoutMs: env.MARZBAN_TIMEOUT_MS,
    proxies: env.MARZBAN_PROXIES,
    inbounds: env.MARZBAN_INBOUNDS,
    subscriptionUrlPrefix: env.MARZBAN_SUBSCRIPTION_URL_PREFIX,
    insecureTls: env.MARZBAN_INSECURE_TLS,
  });

  const telegramRef: { send?: Notifier } = {};
  const notifier: Notifier = {
    async notifyCustomer(telegramId, html) {
      if (telegramRef.send === undefined) {
        throw new Error('telegram notifier not ready');
      }
      await telegramRef.send.notifyCustomer(telegramId, html);
    },
    async notifyAdmins(html) {
      if (telegramRef.send === undefined) {
        throw new Error('telegram notifier not ready');
      }
      await telegramRef.send.notifyAdmins(html);
    },
  };

  const provisioning = new ProvisioningService(env, logger, db, marzban, notifier);
  const sales = new SalesService(env, logger, db, provisioning);
  const bot = createBot({ env, logger, sales });
  const health = startHealthServer(env, pool, marzban, logger);

  telegramRef.send = {
    async notifyCustomer(telegramId, html) {
      await bot.telegram.sendMessage(telegramId, html, { parse_mode: 'HTML' });
    },
    async notifyAdmins(html) {
      for (const adminId of env.ADMIN_TELEGRAM_IDS) {
        await bot.telegram.sendMessage(adminId, html, { parse_mode: 'HTML' }).catch((error: unknown) => {
          logger.error('admin.notify.failed', {
            adminId,
            error: error instanceof Error ? error.message : String(error),
          });
        });
      }
    },
  };

  await db.markExpiredSubscriptions();
  await provisioning.syncSubscriptionUrls();
  await provisioning.recoverStuckOrders();

  await bot.launch({ dropPendingUpdates: false });
  logger.info('bot.started', { admins: env.ADMIN_TELEGRAM_IDS.length, defaultNode: env.DEFAULT_NODE });

  // Reclaim only expired provisioning leases. This is not a queue; it is a
  // safety net for a process crash between the Marzban and PostgreSQL writes.
  const recoveryTimer = setInterval(() => {
    void provisioning.recoverStuckOrders().catch((error: unknown) => {
      logger.error('order.recover.failed', {
        error: error instanceof Error ? error.message : String(error),
      });
    });
  }, 60_000);
  recoveryTimer.unref();

  const shutdown = async (signal: string) => {
    logger.info('bot.stopping', { signal });
    clearInterval(recoveryTimer);
    bot.stop(signal);
    health.close();
    await pool.end();
    process.exit(0);
  };

  process.once('SIGINT', () => {
    void shutdown('SIGINT');
  });
  process.once('SIGTERM', () => {
    void shutdown('SIGTERM');
  });
}

main().catch((error: unknown) => {
  console.error(error);
  process.exit(1);
});
