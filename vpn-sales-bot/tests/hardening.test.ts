import type { AddressInfo } from 'node:net';
import type { Pool, QueryResult } from 'pg';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { createHealthServer } from '../src/bot/health-server.js';
import { loadEnvironment } from '../src/config/env.js';
import type { Logger } from '../src/config/logger.js';
import {
  type ConnectionProfileRow,
  Repositories,
  type OrderRow,
  type PaymentRow,
  type SubscriptionRow,
} from '../src/database/repositories.js';
import type { MarzbanClient, MarzbanUser } from '../src/marzban/client.js';
import { ProvisioningService } from '../src/services/provisioning-service.js';
import { SalesService } from '../src/services/sales-service.js';

const logger: Logger = {
  error: vi.fn(),
  warn: vi.fn(),
  info: vi.fn(),
  debug: vi.fn(),
};

function env() {
  return loadEnvironment({
    DATABASE_URL: 'postgres://vpn:test@127.0.0.1:5432/vpn_sales',
    BOT_TOKEN: '123:test',
    ADMIN_TELEGRAM_IDS: '111',
    PAYMENT_CARD_NUMBER: '0000',
    PAYMENT_CARD_HOLDER: 'Seller',
    MARZBAN_BASE_URL: 'https://127.0.0.1:8000',
    MARZBAN_USERNAME: 'admin',
    MARZBAN_PASSWORD: 'secret',
    MARZBAN_PROXIES: '{"vless":{}}',
    MARZBAN_INBOUNDS: '{}',
  });
}

const paidOrder: OrderRow = {
  id: 10,
  user_id: 1,
  plan_id: 2,
  amount: 150_000,
  status: 'paid',
  kind: 'new',
  renewal_subscription_id: null,
  connection_profile_id: null,
  account_name: 'ct_10',
  paid_at: new Date('2026-01-01T00:00:00Z'),
  provisioning_started_at: null,
  completed_at: null,
};

const claimedOrder: OrderRow = {
  ...paidOrder,
  status: 'provisioning',
  provisioning_started_at: new Date('2026-01-01T00:01:00Z'),
};

const subscription: SubscriptionRow = {
  id: 7,
  user_id: 1,
  order_id: 10,
  marzban_username: 'ct_10',
  account_name: 'ct_10',
  subscription_url: 'https://panel.example/sub/token',
  traffic_gb: 30,
  start_at: new Date('2026-01-01T00:00:00Z'),
  expire_at: new Date('2026-01-31T00:00:00Z'),
  status: 'active',
  node: 'node1',
  connection_profile_id: null,
  connection_profile_name: null,
  plan_name: '30 GB',
};

const connectionProfile: ConnectionProfileRow = {
  id: 3,
  node_id: 1,
  node_name: 'node1',
  name: 'VLESS Reality baseline',
  protocol: 'vless',
  transport: 'tcp',
  security: 'reality',
  port: 443,
  sni: 'www.apple.com',
  flow: 'xtls-rprx-vision',
  fingerprint: 'chrome',
  marzban_inbound_tag: 'VLESS TCP REALITY',
  marzban_proxies: { vless: { flow: 'xtls-rprx-vision' } },
  marzban_inbounds: { vless: ['VLESS TCP REALITY'] },
  enabled: true,
  priority: 10,
  notes: null,
};

const marzbanUser: MarzbanUser = {
  username: 'ct_10',
  status: 'active',
  expire: 1_800_000_000,
  data_limit: 30 * 1024 ** 3,
  subscription_url: subscription.subscription_url,
};

function payment(status: PaymentRow['status']): PaymentRow {
  return {
    id: 5,
    order_id: 10,
    user_id: 1,
    amount: 150_000,
    method: 'card_to_card',
    reference: null,
    receipt_file_id: 'file',
    receipt_kind: 'photo',
    status,
    verified_by: status === 'pending' ? null : '111',
    reviewed_by: status === 'pending' ? null : '111',
    reviewed_at: status === 'pending' ? null : new Date(),
    rejection_reason: null,
  };
}

describe('provisioning idempotency', () => {
  it('does not provision twice when admin approval callback is delivered twice', async () => {
    let paymentState = payment('pending');
    let order: OrderRow = { ...paidOrder, status: 'waiting_payment' };
    const db = {
      getPayment: vi.fn(async () => paymentState),
      approvePayment: vi.fn(async () => {
        paymentState = payment('approved');
        return paymentState;
      }),
      updateOrderStatus: vi.fn(async () => {
        if (order.status !== 'waiting_payment' && order.status !== 'pending') {
          return null;
        }
        order = { ...order, status: 'paid' };
        return order;
      }),
      getOrder: vi.fn(async () => order),
    };
    const provisioning = {
      provisionOrder: vi.fn(async () => {
        order = { ...order, status: 'completed', completed_at: new Date() };
        return subscription;
      }),
    };
    const service = new SalesService(
      env(),
      logger,
      db as unknown as Repositories,
      provisioning as unknown as ProvisioningService,
    );

    await service.approve(5, 111);
    const duplicate = await service.approve(5, 111);

    expect(provisioning.provisionOrder).toHaveBeenCalledTimes(1);
    expect(db.approvePayment).toHaveBeenCalledTimes(1);
    expect(duplicate.duplicate).toBe(true);
  });

  it('allows only one simultaneous provisioning claim', async () => {
    const db = {
      getOrder: vi
        .fn()
        .mockResolvedValueOnce(paidOrder)
        .mockResolvedValueOnce(paidOrder)
        .mockResolvedValue({ ...claimedOrder }),
      claimOrderForProvisioning: vi
        .fn()
        .mockResolvedValueOnce(claimedOrder)
        .mockResolvedValueOnce(null),
      getPlan: vi.fn(async () => ({
        id: 2,
        name: '30 GB',
        traffic_gb: 30,
        duration_days: 30,
        price: 150_000,
        currency: 'TOMAN',
        marzban_profile: null,
        node: null,
        is_active: true,
      })),
      getUserById: vi.fn(async () => ({
        id: 1,
        telegram_id: '123',
        telegram_username: null,
        first_name: null,
        phone: null,
        status: 'active',
      })),
      getSubscriptionByOrder: vi.fn(async () => subscription),
      completeProvisioning: vi.fn(async () => ({ ...claimedOrder, status: 'completed' })),
      updateSubscriptionUrl: vi.fn(async () => subscription),
      updateOrderStatus: vi.fn(),
    };
    const marzban = {
      getUser: vi.fn(async () => marzbanUser),
      createUser: vi.fn(),
      fetchSubscriptionLinks: vi.fn(async () => []),
    };
    const service = new ProvisioningService(
      env(),
      logger,
      db as unknown as Repositories,
      marzban as unknown as MarzbanClient,
      {
        notifyCustomer: vi.fn(async () => undefined),
        notifyCustomerPhoto: vi.fn(async () => undefined),
        notifyAdmins: vi.fn(async () => undefined),
      },
    );

    const results = await Promise.all([service.provisionOrder(10), service.provisionOrder(10)]);

    expect(results.filter(Boolean)).toHaveLength(1);
    expect(db.claimOrderForProvisioning).toHaveBeenCalledTimes(2);
    expect(db.completeProvisioning).toHaveBeenCalledTimes(1);
    expect(marzban.createUser).not.toHaveBeenCalled();
  });

  it('reuses an existing subscription and does not create a Marzban user', async () => {
    const db = {
      getOrder: vi.fn(async () => paidOrder),
      claimOrderForProvisioning: vi.fn(async () => claimedOrder),
      getPlan: vi.fn(async () => ({
        id: 2,
        name: '30 GB',
        traffic_gb: 30,
        duration_days: 30,
        price: 150_000,
        currency: 'TOMAN',
        marzban_profile: null,
        node: null,
        is_active: true,
      })),
      getUserById: vi.fn(async () => ({
        id: 1,
        telegram_id: '123',
        telegram_username: null,
        first_name: null,
        phone: null,
        status: 'active',
      })),
      getSubscriptionByOrder: vi.fn(async () => subscription),
      completeProvisioning: vi.fn(async () => ({ ...claimedOrder, status: 'completed' })),
      updateSubscriptionUrl: vi.fn(async () => subscription),
      updateOrderStatus: vi.fn(),
    };
    const marzban = {
      getUser: vi.fn(async () => marzbanUser),
      createUser: vi.fn(),
      fetchSubscriptionLinks: vi.fn(async () => []),
    };
    const service = new ProvisioningService(
      env(),
      logger,
      db as unknown as Repositories,
      marzban as unknown as MarzbanClient,
      {
        notifyCustomer: vi.fn(async () => undefined),
        notifyCustomerPhoto: vi.fn(async () => undefined),
        notifyAdmins: vi.fn(async () => undefined),
      },
    );

    await expect(service.provisionOrder(10)).resolves.toEqual(subscription);
    expect(marzban.createUser).not.toHaveBeenCalled();
  });

  it('provisions from the order profile instead of a hardcoded global protocol', async () => {
    const profiledOrder = {
      ...paidOrder,
      account_name: 'FOX1001',
      connection_profile_id: connectionProfile.id,
    };
    const profiledClaim = {
      ...claimedOrder,
      account_name: 'FOX1001',
      connection_profile_id: connectionProfile.id,
    };
    const profiledSubscription = {
      ...subscription,
      marzban_username: 'FOX1001',
      account_name: 'FOX1001',
      connection_profile_id: connectionProfile.id,
      connection_profile_name: connectionProfile.name,
    };
    const db = {
      getOrder: vi.fn(async () => profiledOrder),
      claimOrderForProvisioning: vi.fn(async () => profiledClaim),
      getPlan: vi.fn(async () => ({
        id: 2,
        name: '30 GB',
        traffic_gb: 30,
        duration_days: 30,
        price: 150_000,
        currency: 'TOMAN',
        marzban_profile: null,
        node: null,
        is_active: true,
      })),
      getUserById: vi.fn(async () => ({
        id: 1,
        telegram_id: '123',
        telegram_username: null,
        first_name: null,
        phone: null,
        status: 'active',
      })),
      getConnectionProfile: vi.fn(async () => connectionProfile),
      getSubscriptionByOrder: vi.fn(async () => null),
      insertSubscription: vi.fn(async () => profiledSubscription),
      completeProvisioning: vi.fn(async () => ({ ...profiledClaim, status: 'completed' })),
      updateSubscriptionUrl: vi.fn(async () => profiledSubscription),
      updateOrderStatus: vi.fn(),
    };
    const marzban = {
      getUser: vi.fn().mockResolvedValueOnce(null).mockResolvedValue(marzbanUser),
      createUser: vi.fn(async () => marzbanUser),
      fetchSubscriptionLinks: vi.fn(async () => []),
    };
    const service = new ProvisioningService(
      env(),
      logger,
      db as unknown as Repositories,
      marzban as unknown as MarzbanClient,
      {
        notifyCustomer: vi.fn(async () => undefined),
        notifyCustomerPhoto: vi.fn(async () => undefined),
        notifyAdmins: vi.fn(async () => undefined),
      },
    );

    await service.provisionOrder(10);

    expect(marzban.createUser).toHaveBeenCalledWith(
      expect.objectContaining({
        username: 'FOX1001',
        proxies: connectionProfile.marzban_proxies,
        inbounds: connectionProfile.marzban_inbounds,
      }),
    );
    expect(db.insertSubscription).toHaveBeenCalledWith(
      expect.objectContaining({
        accountName: 'FOX1001',
        marzbanUsername: 'FOX1001',
        connectionProfileId: connectionProfile.id,
      }),
    );
  });

  it('includes both direct config and subscription URL in the customer message', async () => {
    const directConfig =
      'vless://00000000-0000-0000-0000-000000000000@example.com:443?security=reality';
    const marzban = {
      getUser: vi.fn(async () => marzbanUser),
      fetchSubscriptionLinks: vi.fn(async () => [directConfig]),
    };
    const service = new ProvisioningService(
      env(),
      logger,
      {} as Repositories,
      marzban as unknown as MarzbanClient,
      {
        notifyCustomer: vi.fn(async () => undefined),
        notifyCustomerPhoto: vi.fn(async () => undefined),
        notifyAdmins: vi.fn(async () => undefined),
      },
    );

    const message = await service.formatServiceMessage(subscription);

    expect(message).toContain(directConfig);
    expect(message).toContain('🔗 لینک اشتراک:');
    expect(message).toContain(subscription.subscription_url);
    expect(message).toContain(subscription.account_name);
  });

  it('creates local PNG QR images for both subscription and direct config', async () => {
    const directConfig =
      'vless://00000000-0000-0000-0000-000000000000@example.com:443?security=reality';
    const marzban = {
      getUser: vi.fn(async () => marzbanUser),
      fetchSubscriptionLinks: vi.fn(async () => [directConfig]),
    };
    const service = new ProvisioningService(
      env(),
      logger,
      {} as Repositories,
      marzban as unknown as MarzbanClient,
      {
        notifyCustomer: vi.fn(async () => undefined),
        notifyCustomerPhoto: vi.fn(async () => undefined),
        notifyAdmins: vi.fn(async () => undefined),
      },
    );

    const deliveries = await service.formatServiceQrDeliveries(subscription);

    expect(deliveries).toHaveLength(2);
    expect(deliveries[0]?.image.subarray(0, 8)).toEqual(
      Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    );
    expect(deliveries[0]?.caption).toContain(subscription.account_name);
    expect(deliveries[0]?.caption).toContain(subscription.subscription_url);
    expect(deliveries[1]?.caption).toContain(directConfig);
  });

  it('snapshots the selected profile on a new order', async () => {
    const db = {
      getPlan: vi.fn(async () => ({
        id: 2,
        name: '30 GB',
        traffic_gb: 30,
        duration_days: 30,
        price: 150_000,
        currency: 'TOMAN',
        marzban_profile: null,
        node: null,
        is_active: true,
      })),
      getProfileForPlan: vi.fn(async () => connectionProfile),
      cancelOpenOrders: vi.fn(async () => undefined),
      createOrder: vi.fn(async () => ({
        ...paidOrder,
        status: 'waiting_payment',
        connection_profile_id: connectionProfile.id,
      })),
    };
    const service = new SalesService(
      env(),
      logger,
      db as unknown as Repositories,
      {} as ProvisioningService,
    );

    const result = await service.createPurchase(1, 2, connectionProfile.id);

    expect(result.profile).toEqual(connectionProfile);
    expect(db.createOrder).toHaveBeenCalledWith(
      expect.objectContaining({ connectionProfileId: connectionProfile.id }),
    );
  });
});

describe('repository hardening SQL', () => {
  it('atomically reserves and then reuses the FOX account name on the order', async () => {
    const query = vi
      .fn()
      .mockResolvedValueOnce({ rows: [{ account_name: 'FOX1001' }], rowCount: 1 })
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })
      .mockResolvedValueOnce({ rows: [{ account_name: 'FOX1001' }], rowCount: 1 });
    const repository = new Repositories({ query } as unknown as Pool);

    await expect(repository.reserveOrderAccountName(10)).resolves.toBe('FOX1001');
    await expect(repository.reserveOrderAccountName(10)).resolves.toBe('FOX1001');

    const reserveSql = String(query.mock.calls[0]?.[0]);
    expect(reserveSql).toContain("nextval('vpn_account_number_seq')");
    expect(reserveSql).toContain('account_name IS NULL');
    expect(reserveSql).toContain("kind = 'new'");
  });

  it('claims paid -> provisioning atomically', async () => {
    const query = vi.fn(async () => ({ rows: [claimedOrder], rowCount: 1 }));
    const repository = new Repositories({ query } as unknown as Pool);

    await repository.claimOrderForProvisioning(10);

    const sql = String(query.mock.calls[0]?.[0]);
    expect(sql).toContain("status IN ('paid', 'failed')");
    expect(sql).toContain("SET status = 'provisioning'");
    expect(sql).not.toContain("'provisioning', 'failed'");
  });

  it('records payment approval audit fields', async () => {
    const approved = payment('approved');
    const query = vi.fn(async () => ({ rows: [approved], rowCount: 1 }));
    const repository = new Repositories({ query } as unknown as Pool);

    const result = await repository.approvePayment(5, 111);

    const sql = String(query.mock.calls[0]?.[0]);
    expect(sql).toContain('reviewed_by = $2');
    expect(sql).toContain('reviewed_at = now()');
    expect(result?.reviewed_by).toBe('111');
    expect(result?.amount).toBe(150_000);
  });

  it('records payment rejection audit fields and reason', async () => {
    const rejected = { ...payment('rejected'), rejection_reason: 'رسید نامعتبر' };
    const query = vi.fn(async () => ({ rows: [rejected], rowCount: 1 }));
    const repository = new Repositories({ query } as unknown as Pool);

    const result = await repository.rejectPayment(5, 111, 'رسید نامعتبر');

    const sql = String(query.mock.calls[0]?.[0]);
    expect(sql).toContain('rejection_reason = $3');
    expect(query.mock.calls[0]?.[1]).toEqual([5, 111, 'رسید نامعتبر']);
    expect(result?.reviewed_by).toBe('111');
    expect(result?.rejection_reason).toBe('رسید نامعتبر');
  });

  it('renews in place without replacing the subscription original order id', async () => {
    const query = vi.fn(async () => ({ rows: [subscription], rowCount: 1 }));
    const repository = new Repositories({ query } as unknown as Pool);

    await repository.updateSubscriptionRenewal({
      id: 7,
      subscriptionUrl: 'https://panel.example/sub/new',
      trafficGb: 50,
      expireAt: new Date('2026-03-02T00:00:00Z'),
      node: 'node1',
    });

    const sql = String(query.mock.calls[0]?.[0]);
    expect(sql).not.toContain('SET order_id');
    expect(query.mock.calls[0]?.[1]).toHaveLength(5);
  });

  it('records field tests without storing a customer identifier', async () => {
    const query = vi.fn(async () => ({ rows: [{ id: 1 }], rowCount: 1 }));
    const repository = new Repositories({ query } as unknown as Pool);

    await expect(
      repository.recordProfileTestForUser({
        userId: 1,
        subscriptionId: 7,
        isp: 'mci',
        networkType: '4g',
        connected: false,
        downloadOk: null,
        clientApp: 'v2rayng',
        failureStage: 'connect',
      }),
    ).resolves.toBe(true);

    const sql = String(query.mock.calls[0]?.[0]);
    const insertColumns = sql.slice(sql.indexOf('INSERT INTO'), sql.indexOf('SELECT'));
    expect(insertColumns).not.toContain('user_id');
    expect(insertColumns).not.toContain('subscription_id');
    expect(sql).toContain('s.user_id = $2');
  });
});

describe('health endpoints', () => {
  const servers: Array<ReturnType<typeof createHealthServer>> = [];
  afterEach(async () => {
    await Promise.all(
      servers.splice(0).map(
        (server) => new Promise<void>((resolve) => server.close(() => resolve())),
      ),
    );
  });

  async function start(pool: object, marzban: object) {
    const server = createHealthServer(
      pool as Pool,
      marzban as { health(): Promise<{ ok: boolean; detail: string }> },
      logger,
    );
    servers.push(server);
    await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', resolve));
    const port = (server.address() as AddressInfo).port;
    return `http://127.0.0.1:${port}`;
  }

  it('health live is fast and does not call dependencies', async () => {
    const query = vi.fn();
    const health = vi.fn();
    const base = await start({ query }, { health });

    const response = await fetch(`${base}/health/live`);

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ status: 'ok', service: 'vpn-sales-bot' });
    expect(query).not.toHaveBeenCalled();
    expect(health).not.toHaveBeenCalled();
  });

  it('health ready returns non-2xx when a dependency fails', async () => {
    const base = await start(
      { query: vi.fn(async () => ({ rows: [{ ok: 1 }] } as QueryResult)) },
      { health: vi.fn(async () => ({ ok: false, detail: 'down' })) },
    );

    const response = await fetch(`${base}/health/ready`);

    expect(response.status).toBe(503);
    expect(await response.json()).toEqual({
      status: 'error',
      database: 'ok',
      marzban: 'error',
      config: 'ok',
    });
  });
});
