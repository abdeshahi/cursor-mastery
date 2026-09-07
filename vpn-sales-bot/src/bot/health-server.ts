import { createServer, type Server } from 'node:http';
import type { Pool } from 'pg';

import type { Environment } from '../config/env.js';
import type { Logger } from '../config/logger.js';

export function startHealthServer(env: Environment, pool: Pool, logger: Logger): Server {
  const server = createServer((req, res) => {
    const url = req.url ?? '/';
    if (url.split('?')[0] !== '/health') {
      res.statusCode = 404;
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify({ ok: false, error: 'not_found' }));
      return;
    }

    void pool
      .query('SELECT 1 AS ok')
      .then(() => {
        res.statusCode = 200;
        res.setHeader('Content-Type', 'application/json');
        res.end(JSON.stringify({ ok: true, db: true, service: 'vpn-sales-bot' }));
      })
      .catch((error: unknown) => {
        logger.error('health.db.failed', {
          error: error instanceof Error ? error.message : String(error),
        });
        res.statusCode = 503;
        res.setHeader('Content-Type', 'application/json');
        res.end(JSON.stringify({ ok: false, db: false }));
      });
  });

  server.listen(env.HEALTH_PORT, env.HEALTH_HOST, () => {
    logger.info('health.listening', { host: env.HEALTH_HOST, port: env.HEALTH_PORT });
  });

  return server;
}
