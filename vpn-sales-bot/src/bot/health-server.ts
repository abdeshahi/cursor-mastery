import { createServer, type Server, type ServerResponse } from 'node:http';
import type { Pool } from 'pg';

import type { Environment } from '../config/env.js';
import type { Logger } from '../config/logger.js';

export interface HealthMarzban {
  health(): Promise<{ ok: boolean; detail: string }>;
}

function json(res: ServerResponse, status: number, body: object): void {
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json');
  res.end(JSON.stringify(body));
}

export function createHealthServer(pool: Pool, marzban: HealthMarzban, logger: Logger): Server {
  return createServer((req, res) => {
    const path = (req.url ?? '/').split('?')[0];
    if (req.method !== 'GET') {
      json(res, 405, { status: 'error', error: 'method_not_allowed' });
      return;
    }

    if (path === '/health/live') {
      json(res, 200, { status: 'ok', service: 'vpn-sales-bot' });
      return;
    }

    if (path === '/health/ready') {
      void Promise.allSettled([pool.query('SELECT 1 AS ok'), marzban.health()]).then(
        ([databaseResult, marzbanResult]) => {
          const databaseOk = databaseResult.status === 'fulfilled';
          const marzbanOk =
            marzbanResult.status === 'fulfilled' && marzbanResult.value.ok;
          if (!databaseOk) {
            logger.error('health.database.failed', {
              error:
                databaseResult.status === 'rejected'
                  ? String(databaseResult.reason)
                  : 'unknown',
            });
          }
          if (!marzbanOk) {
            logger.error('health.marzban.failed', {
              detail:
                marzbanResult.status === 'fulfilled'
                  ? marzbanResult.value.detail
                  : String(marzbanResult.reason),
            });
          }
          json(res, databaseOk && marzbanOk ? 200 : 503, {
            status: databaseOk && marzbanOk ? 'ok' : 'error',
            database: databaseOk ? 'ok' : 'error',
            marzban: marzbanOk ? 'ok' : 'error',
            config: 'ok',
          });
        },
      );
      return;
    }

    // Backward compatibility: /health retains its original DB-only contract.
    if (path !== '/health') {
      json(res, 404, { ok: false, error: 'not_found' });
      return;
    }
    void pool
      .query('SELECT 1 AS ok')
      .then(() => {
        json(res, 200, { ok: true, db: true, service: 'vpn-sales-bot' });
      })
      .catch((error: unknown) => {
        logger.error('health.db.failed', {
          error: error instanceof Error ? error.message : String(error),
        });
        json(res, 503, { ok: false, db: false });
      });
  });
}

export function startHealthServer(
  env: Environment,
  pool: Pool,
  marzban: HealthMarzban,
  logger: Logger,
): Server {
  const server = createHealthServer(pool, marzban, logger);
  server.listen(env.HEALTH_PORT, env.HEALTH_HOST, () => {
    logger.info('health.listening', { host: env.HEALTH_HOST, port: env.HEALTH_PORT });
  });

  return server;
}
