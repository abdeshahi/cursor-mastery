import { describe, expect, it } from 'vitest';

import { loadEnvironment } from '../src/config/env.js';

describe('loadEnvironment', () => {
  it('accepts TELEGRAM_BOT_TOKEN alias and trims admin id', () => {
    const env = loadEnvironment({
      TELEGRAM_BOT_TOKEN: ' 123:abc ',
      ADMIN_TELEGRAM_ID: '"987654321"',
      DATABASE_URL: 'file:./data/bot.db',
    });

    expect(env.BOT_TOKEN).toBe('123:abc');
    expect(env.ADMIN_TELEGRAM_ID).toBe('987654321');
  });

  it('supports comma-separated admin ids', () => {
    const env = loadEnvironment({
      BOT_TOKEN: 'token',
      ADMIN_TELEGRAM_IDS: '111, 222',
      DATABASE_URL: 'file:./data/bot.db',
    });

    expect(env.ADMIN_TELEGRAM_ID).toBe('111, 222');
  });
});
