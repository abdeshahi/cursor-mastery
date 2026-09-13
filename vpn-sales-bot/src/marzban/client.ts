import { Agent, fetch as undiciFetch } from 'undici';

export class MarzbanError extends Error {
  constructor(
    message: string,
    readonly statusCode?: number,
    readonly body?: string,
  ) {
    super(message);
    this.name = 'MarzbanError';
  }
}

export interface MarzbanUser {
  username: string;
  status: string;
  expire: number | null;
  data_limit: number | null;
  subscription_url: string;
  used_traffic?: number;
}

export interface MarzbanClientOptions {
  baseUrl: string;
  username: string;
  password: string;
  timeoutMs: number;
  proxies: Record<string, unknown>;
  inbounds: Record<string, unknown>;
  subscriptionUrlPrefix?: string;
  /** Allow self-signed HTTPS when the bot talks to Marzban on the same VPS. */
  insecureTls?: boolean;
  fetchImpl?: typeof fetch;
}

function createMarzbanFetch(insecureTls: boolean): typeof fetch {
  if (!insecureTls) {
    return fetch;
  }
  const dispatcher = new Agent({ connect: { rejectUnauthorized: false } });
  return ((input, init) =>
    undiciFetch(input as never, { dispatcher, ...(init as object) })) as typeof fetch;
}

export class MarzbanClient {
  private token: string | null = null;
  private readonly fetchImpl: typeof fetch;

  constructor(private readonly options: MarzbanClientOptions) {
    this.fetchImpl =
      options.fetchImpl ?? createMarzbanFetch(options.insecureTls ?? false);
  }

  async authenticate(): Promise<void> {
    const body = new URLSearchParams({
      username: this.options.username,
      password: this.options.password,
      grant_type: 'password',
    });

    const response = await this.request('/api/admin/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body,
      auth: false,
    });

    const payload = (await this.readJson(response)) as { access_token?: unknown };
    if (typeof payload.access_token !== 'string' || payload.access_token.length === 0) {
      throw new MarzbanError('Marzban token missing from response', response.status);
    }
    this.token = payload.access_token;
  }

  async ping(): Promise<boolean> {
    try {
      await this.ensureAuth();
      const response = await this.request('/api/system', { method: 'GET' });
      return response.ok;
    } catch {
      return false;
    }
  }

  async createUser(input: {
    username: string;
    expireUnix: number;
    dataLimitBytes: number;
    note?: string;
    proxies?: Record<string, unknown>;
    inbounds?: Record<string, unknown>;
  }): Promise<MarzbanUser> {
    await this.ensureAuth();
    const response = await this.request('/api/user', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: input.username,
        expire: input.expireUnix,
        data_limit: input.dataLimitBytes,
        data_limit_reset_strategy: 'no_reset',
        status: 'active',
        note: input.note ?? '',
        proxies: input.proxies ?? this.options.proxies,
        inbounds: input.inbounds ?? this.options.inbounds,
      }),
    });
    return this.parseUser(await this.readJson(response));
  }

  async getUser(username: string): Promise<MarzbanUser | null> {
    await this.ensureAuth();
    const response = await this.request(`/api/user/${encodeURIComponent(username)}`, {
      method: 'GET',
      allowStatuses: [404],
    });
    if (response.status === 404) {
      return null;
    }
    return this.parseUser(await this.readJson(response));
  }

  async getUserStatus(username: string): Promise<string | null> {
    const user = await this.getUser(username);
    return user?.status ?? null;
  }

  async modifyUser(
    username: string,
    patch: {
      expireUnix?: number;
      dataLimitBytes?: number;
      status?: 'active' | 'disabled';
      note?: string;
      proxies?: Record<string, unknown>;
      inbounds?: Record<string, unknown>;
    },
  ): Promise<MarzbanUser> {
    await this.ensureAuth();
    const body: Record<string, unknown> = {};
    if (patch.expireUnix !== undefined) {
      body['expire'] = patch.expireUnix;
    }
    if (patch.dataLimitBytes !== undefined) {
      body['data_limit'] = patch.dataLimitBytes;
    }
    if (patch.status !== undefined) {
      body['status'] = patch.status;
    }
    if (patch.note !== undefined) {
      body['note'] = patch.note;
    }
    if (patch.proxies !== undefined) {
      body['proxies'] = patch.proxies;
    }
    if (patch.inbounds !== undefined) {
      body['inbounds'] = patch.inbounds;
    }

    const response = await this.request(`/api/user/${encodeURIComponent(username)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return this.parseUser(await this.readJson(response));
  }

  async resetTraffic(username: string): Promise<void> {
    await this.ensureAuth();
    await this.request(`/api/user/${encodeURIComponent(username)}/reset`, { method: 'POST' });
  }

  async disableUser(username: string): Promise<MarzbanUser> {
    return this.modifyUser(username, { status: 'disabled' });
  }

  async health(): Promise<{ ok: boolean; detail: string }> {
    try {
      const ok = await this.ping();
      return { ok, detail: ok ? 'marzban api reachable' : 'marzban api unhealthy' };
    } catch (error) {
      return {
        ok: false,
        detail: error instanceof Error ? error.message : String(error),
      };
    }
  }

  /** Fetch decoded proxy links (vless://, vmess://, …) from a subscription URL. */
  async fetchSubscriptionLinks(subscriptionUrl: string): Promise<string[]> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.options.timeoutMs);
    try {
      const response = await this.fetchImpl(subscriptionUrl, {
        method: 'GET',
        signal: controller.signal,
      });
      if (!response.ok) {
        throw new MarzbanError(`subscription fetch HTTP ${response.status}`, response.status);
      }
      const raw = (await response.text()).trim();
      if (raw.length === 0) {
        return [];
      }
      let decoded = raw;
      try {
        decoded = Buffer.from(raw, 'base64').toString('utf8');
      } catch {
        // Some panels return plain text already.
      }
      return decoded
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter((line) => /^[a-z0-9+.-]+:\/\//i.test(line));
    } catch (error) {
      if (error instanceof MarzbanError) {
        throw error;
      }
      const message = error instanceof Error ? error.message : String(error);
      throw new MarzbanError(`subscription fetch failed: ${message}`);
    } finally {
      clearTimeout(timer);
    }
  }

  private async ensureAuth(): Promise<void> {
    if (this.token === null) {
      await this.authenticate();
    }
  }

  private parseUser(payload: unknown): MarzbanUser {
    if (payload === null || typeof payload !== 'object') {
      throw new MarzbanError('invalid Marzban user payload');
    }
    const row = payload as Record<string, unknown>;
    if (typeof row['username'] !== 'string') {
      throw new MarzbanError('Marzban user username missing');
    }
    const rawUrl = row['subscription_url'];
    return {
      username: row['username'],
      status: typeof row['status'] === 'string' ? row['status'] : 'unknown',
      expire: typeof row['expire'] === 'number' ? row['expire'] : null,
      data_limit: typeof row['data_limit'] === 'number' ? row['data_limit'] : null,
      subscription_url: typeof rawUrl === 'string' ? rawUrl : '',
      used_traffic: typeof row['used_traffic'] === 'number' ? row['used_traffic'] : undefined,
    };
  }

  private async readJson(response: Response): Promise<unknown> {
    const text = await response.text();
    if (text.length === 0) {
      return {};
    }
    try {
      return JSON.parse(text) as unknown;
    } catch {
      throw new MarzbanError('Marzban returned non-JSON', response.status, text.slice(0, 500));
    }
  }

  private async request(
    pathname: string,
    init: {
      method: string;
      headers?: Record<string, string>;
      body?: RequestInit['body'];
      auth?: boolean;
      allowStatuses?: number[];
    },
  ): Promise<Response> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.options.timeoutMs);
    const headers: Record<string, string> = { ...(init.headers ?? {}) };
    if (init.auth !== false && this.token !== null) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    const base = this.options.baseUrl.endsWith('/') ? this.options.baseUrl : `${this.options.baseUrl}/`;

    try {
      const response = await this.fetchImpl(new URL(pathname, base), {
        method: init.method,
        headers,
        body: init.body,
        signal: controller.signal,
      });

      if (response.status === 401 && init.auth !== false) {
        this.token = null;
        await this.authenticate();
        headers['Authorization'] = `Bearer ${this.token ?? ''}`;
        const retry = await this.fetchImpl(new URL(pathname, base), {
          method: init.method,
          headers,
          body: init.body,
          signal: controller.signal,
        });
        return this.assertOk(retry, init.allowStatuses);
      }

      return this.assertOk(response, init.allowStatuses);
    } catch (error) {
      if (error instanceof MarzbanError) {
        throw error;
      }
      const message = error instanceof Error ? error.message : String(error);
      throw new MarzbanError(`Marzban request failed: ${message}`);
    } finally {
      clearTimeout(timer);
    }
  }

  private assertOk(response: Response, allowStatuses: number[] = []): Response {
    if (response.ok || allowStatuses.includes(response.status)) {
      return response;
    }
    throw new MarzbanError(`Marzban HTTP ${response.status}`, response.status);
  }
}
