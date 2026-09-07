import { describe, expect, it, vi } from 'vitest';

import { MarzbanClient, MarzbanError } from '../src/marzban/client.js';

describe('Marzban client', () => {
  it('authenticates and creates a user', async () => {
    const fetchImpl = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith('/api/admin/token')) {
        return new Response(JSON.stringify({ access_token: 'tok' }), { status: 200 });
      }
      if (url.endsWith('/api/user') && init?.method === 'POST') {
        return new Response(
          JSON.stringify({
            username: 'ct_1',
            status: 'active',
            expire: 1,
            data_limit: 10,
            subscription_url: 'https://panel.example.com/sub/abc',
          }),
          { status: 200 },
        );
      }
      return new Response('nope', { status: 500 });
    });

    const client = new MarzbanClient({
      baseUrl: 'https://panel.example.com',
      username: 'admin',
      password: 'secret',
      timeoutMs: 5000,
      proxies: { vless: {} },
      inbounds: {},
      fetchImpl: fetchImpl as unknown as typeof fetch,
    });

    const user = await client.createUser({
      username: 'ct_1',
      expireUnix: 1_700_000_000,
      dataLimitBytes: 1024,
    });
    expect(user.subscription_url).toContain('/sub/abc');
  });

  it('surfaces API failures', async () => {
    const fetchImpl = vi.fn(async () => new Response('down', { status: 503 }));
    const client = new MarzbanClient({
      baseUrl: 'https://panel.example.com',
      username: 'admin',
      password: 'secret',
      timeoutMs: 5000,
      proxies: {},
      inbounds: {},
      fetchImpl: fetchImpl as unknown as typeof fetch,
    });

    await expect(client.authenticate()).rejects.toBeInstanceOf(MarzbanError);
  });

  it('returns null when user is missing', async () => {
    const fetchImpl = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith('/api/admin/token')) {
        return new Response(JSON.stringify({ access_token: 'tok' }), { status: 200 });
      }
      return new Response('missing', { status: 404 });
    });
    const client = new MarzbanClient({
      baseUrl: 'https://panel.example.com',
      username: 'admin',
      password: 'secret',
      timeoutMs: 5000,
      proxies: {},
      inbounds: {},
      fetchImpl: fetchImpl as unknown as typeof fetch,
    });
    await expect(client.getUser('ct_9')).resolves.toBeNull();
  });
});
