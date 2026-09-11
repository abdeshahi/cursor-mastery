import { describe, expect, it } from 'vitest';

import { isAdmin, loadEnvironment } from '../src/config/env.js';
import { encodeCallback, parseCallback } from '../src/utils/callback.js';
import {
  assignNode,
  bytesFromGb,
  marzbanUsernameForOrder,
  nextExpiry,
  resolveSubscriptionUrl,
} from '../src/utils/provisioning.js';
import { canStartProvisioning, nextPaymentApproval, nextPaymentRejection } from '../src/utils/state-machine.js';

function validEnv(overrides: Record<string, string> = {}): NodeJS.ProcessEnv {
  return {
    DATABASE_URL: 'postgres://vpn:vpn@127.0.0.1:5432/vpn_sales',
    BOT_TOKEN: '123:token',
    ADMIN_TELEGRAM_IDS: '111,222',
    PAYMENT_CARD_NUMBER: '6037991111111111',
    PAYMENT_CARD_HOLDER: 'Seller',
    MARZBAN_BASE_URL: 'https://panel.example.com',
    MARZBAN_USERNAME: 'admin',
    MARZBAN_PASSWORD: 'secret',
    MARZBAN_PROXIES: '{"vless":{}}',
    MARZBAN_INBOUNDS: '{}',
    ...overrides,
  };
}

describe('callbacks', () => {
  it('parses valid menu and plan callbacks', () => {
    expect(parseCallback('m:buy')).toEqual({ type: 'menu', page: 'buy' });
    expect(parseCallback(encodeCallback({ type: 'plan', planId: 7 }))).toEqual({ type: 'plan', planId: 7 });
    expect(parseCallback(encodeCallback({ type: 'approve', paymentId: 99 }))).toEqual({
      type: 'approve',
      paymentId: 99,
    });
  });

  it('rejects invalid callbacks', () => {
    expect(parseCallback('')).toBeNull();
    expect(parseCallback('explode')).toBeNull();
    expect(parseCallback('a:0')).toBeNull();
    expect(parseCallback('p:abc')).toBeNull();
    expect(parseCallback('m:hack')).toBeNull();
    expect(parseCallback('x'.repeat(65))).toBeNull();
  });

  it('round-trips profile selection and privacy-minimal field test callbacks', () => {
    expect(parseCallback(encodeCallback({ type: 'selectProfile', planId: 2, profileId: 3 }))).toEqual({
      type: 'selectProfile',
      planId: 2,
      profileId: 3,
    });
    const report = {
      type: 'testResult' as const,
      subscriptionId: 7,
      isp: 'mci' as const,
      networkType: '4g' as const,
      clientApp: 'v2rayng' as const,
      result: 'failed' as const,
    };
    expect(parseCallback(encodeCallback(report))).toEqual(report);
    expect(parseCallback('tr:7:unknown:4g:v2rayng:failed')).toBeNull();
  });
});

describe('admin whitelist', () => {
  it('allows only configured admin ids', () => {
    const env = loadEnvironment(validEnv());
    expect(isAdmin(env, 111)).toBe(true);
    expect(isAdmin(env, 999)).toBe(false);
  });

  it('rejects malformed admin ids', () => {
    expect(() => loadEnvironment(validEnv({ ADMIN_TELEGRAM_IDS: 'abc' }))).toThrow(/ADMIN_TELEGRAM_IDS/);
  });
});

describe('provisioning helpers', () => {
  it('builds deterministic marzban usernames', () => {
    expect(marzbanUsernameForOrder(42)).toBe('ct_42');
  });

  it('renews an active subscription from its current expiry', () => {
    const now = new Date('2026-01-10T00:00:00Z');
    const current = new Date('2026-01-20T00:00:00Z');
    expect(nextExpiry(current, now, 30).toISOString()).toBe('2026-02-19T00:00:00.000Z');
  });

  it('renews an expired subscription from the current time', () => {
    const now = new Date('2026-01-10T00:00:00Z');
    const current = new Date('2026-01-01T00:00:00Z');
    expect(nextExpiry(current, now, 30).toISOString()).toBe('2026-02-09T00:00:00.000Z');
  });

  it('converts GB to bytes', () => {
    expect(bytesFromGb(1)).toBe(1073741824);
  });

  it('resolves relative subscription urls', () => {
    expect(resolveSubscriptionUrl('/sub/abc', 'https://cdn.example.com')).toBe(
      'https://cdn.example.com/sub/abc',
    );
  });

  it('upgrades http subscription urls when prefix is https on the same host', () => {
    expect(
      resolveSubscriptionUrl(
        'http://185.18.214.66:8000/sub/token',
        'https://185.18.214.66:8000',
      ),
    ).toBe('https://185.18.214.66:8000/sub/token');
  });

  it('moves absolute Marzban subscription paths to the configured HTTPS origin', () => {
    expect(
      resolveSubscriptionUrl(
        'http://185.18.214.66:8090/sub/token?client=v2rayng',
        'https://185.18.214.66:8443',
      ),
    ).toBe('https://185.18.214.66:8443/sub/token?client=v2rayng');
  });

  it('uses plan node then default node', () => {
    expect(assignNode('node2', 'node1')).toBe('node2');
    expect(assignNode(null, 'node1')).toBe('node1');
  });
});

describe('idempotent payment and provisioning states', () => {
  it('does not approve a rejected payment', () => {
    expect(nextPaymentApproval('pending')).toBe('approve');
    expect(nextPaymentApproval('approved')).toBe('duplicate');
    expect(nextPaymentApproval('rejected')).toBe('invalid');
  });

  it('does not reject an approved payment', () => {
    expect(nextPaymentRejection('pending')).toBe('approve');
    expect(nextPaymentRejection('rejected')).toBe('duplicate');
    expect(nextPaymentRejection('approved')).toBe('invalid');
  });

  it('starts provisioning once, retries failed jobs, and rejects active claims', () => {
    expect(canStartProvisioning('paid')).toBe('start');
    expect(canStartProvisioning('provisioning')).toBe('conflict');
    expect(canStartProvisioning('failed')).toBe('retry');
    expect(canStartProvisioning('completed')).toBe('skip');
    expect(canStartProvisioning('waiting_payment')).toBe('conflict');
  });
});
