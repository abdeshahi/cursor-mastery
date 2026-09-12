import type { Pool, QueryResult } from 'pg';

import type { OrderStatus, PaymentStatus } from '../utils/state-machine.js';

export interface UserRow {
  id: number;
  telegram_id: string;
  telegram_username: string | null;
  first_name: string | null;
  phone: string | null;
  status: 'active' | 'blocked';
}

export interface PlanRow {
  id: number;
  name: string;
  traffic_gb: number;
  duration_days: number;
  price: number;
  currency: string;
  marzban_profile: string | null;
  node: string | null;
  is_active: boolean;
}

export interface ConnectionProfileRow {
  id: number;
  node_id: number;
  node_name: string;
  name: string;
  protocol: string;
  transport: string;
  security: string;
  port: number;
  sni: string | null;
  flow: string | null;
  fingerprint: string | null;
  marzban_inbound_tag: string;
  marzban_proxies: Record<string, unknown>;
  marzban_inbounds: Record<string, unknown>;
  enabled: boolean;
  priority: number;
  notes: string | null;
}

export interface OrderRow {
  id: number;
  user_id: number;
  plan_id: number;
  amount: number;
  status: OrderStatus;
  kind: 'new' | 'renewal';
  renewal_subscription_id: number | null;
  connection_profile_id: number | null;
  account_name: string | null;
  paid_at: Date | null;
  provisioning_started_at: Date | null;
  completed_at: Date | null;
}

export interface PaymentRow {
  id: number;
  order_id: number;
  user_id: number;
  amount: number;
  method: string;
  reference: string | null;
  receipt_file_id: string | null;
  receipt_kind: 'photo' | 'document' | null;
  status: PaymentStatus;
  verified_by: string | null;
  reviewed_by: string | null;
  reviewed_at: Date | null;
  rejection_reason: string | null;
}

export interface SubscriptionRow {
  id: number;
  user_id: number;
  order_id: number;
  marzban_username: string;
  account_name: string;
  subscription_url: string;
  traffic_gb: number;
  start_at: Date;
  expire_at: Date;
  status: 'active' | 'expired' | 'suspended' | 'cancelled';
  node: string | null;
  connection_profile_id: number | null;
  connection_profile_name: string | null;
  plan_name: string | null;
}

function num(value: unknown): number {
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed)) {
    throw new Error(`invalid numeric id: ${String(value)}`);
  }
  return parsed;
}

function str(value: unknown): string {
  if (typeof value !== 'string') {
    throw new Error('expected string');
  }
  return value;
}

function optionalStr(value: unknown): string | null {
  return value === null || value === undefined ? null : str(value);
}

function optionalNum(value: unknown): number | null {
  return value === null || value === undefined ? null : num(value);
}

function object(value: unknown): Record<string, unknown> {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error('expected object');
  }
  return value as Record<string, unknown>;
}

export class Repositories {
  constructor(private readonly db: Pool) {}

  private async query<T extends Record<string, unknown>>(
    text: string,
    params: unknown[] = [],
  ): Promise<QueryResult<T>> {
    return this.db.query<T>(text, params);
  }

  async upsertUser(input: {
    telegramId: number;
    username?: string;
    firstName?: string;
  }): Promise<UserRow> {
    const result = await this.query(
      `INSERT INTO users (telegram_id, telegram_username, first_name, status)
       VALUES ($1, $2, $3, 'active')
       ON CONFLICT (telegram_id) DO UPDATE SET
         telegram_username = EXCLUDED.telegram_username,
         first_name = EXCLUDED.first_name,
         updated_at = now()
       RETURNING id, telegram_id, telegram_username, first_name, phone, status`,
      [input.telegramId, input.username ?? null, input.firstName ?? null],
    );
    return this.mapUser(result.rows[0]);
  }

  async getUserById(id: number): Promise<UserRow | null> {
    const result = await this.query(
      `SELECT id, telegram_id, telegram_username, first_name, phone, status
       FROM users WHERE id = $1`,
      [id],
    );
    const row = result.rows[0];
    return row === undefined ? null : this.mapUser(row);
  }

  async listActivePlans(): Promise<PlanRow[]> {
    const result = await this.query(
      `SELECT id, name, traffic_gb, duration_days, price, currency, marzban_profile, node, is_active
       FROM plans
       WHERE is_active = TRUE
       ORDER BY sort_order ASC, id ASC`,
    );
    return result.rows.map((row) => this.mapPlan(row));
  }

  async getPlan(id: number): Promise<PlanRow | null> {
    const result = await this.query(
      `SELECT id, name, traffic_gb, duration_days, price, currency, marzban_profile, node, is_active
       FROM plans WHERE id = $1`,
      [id],
    );
    const row = result.rows[0];
    return row === undefined ? null : this.mapPlan(row);
  }

  async listProfilesForPlan(planId: number): Promise<ConnectionProfileRow[]> {
    const result = await this.query(
      `SELECT cp.id, cp.node_id, n.name AS node_name, cp.name, cp.protocol, cp.transport,
              cp.security, cp.port, cp.sni, cp.flow, cp.fingerprint, cp.marzban_inbound_tag,
              cp.marzban_proxies, cp.marzban_inbounds, cp.enabled, cp.priority, cp.notes
       FROM plan_connection_profiles pcp
       JOIN connection_profiles cp ON cp.id = pcp.profile_id
       JOIN nodes n ON n.id = cp.node_id
       WHERE pcp.plan_id = $1 AND cp.enabled = TRUE AND n.enabled = TRUE
       ORDER BY pcp.is_default DESC, cp.priority ASC, cp.id ASC`,
      [planId],
    );
    return result.rows.map((row) => this.mapConnectionProfile(row));
  }

  async getDefaultProfileForPlan(planId: number): Promise<ConnectionProfileRow | null> {
    const result = await this.query(
      `SELECT cp.id, cp.node_id, n.name AS node_name, cp.name, cp.protocol, cp.transport,
              cp.security, cp.port, cp.sni, cp.flow, cp.fingerprint, cp.marzban_inbound_tag,
              cp.marzban_proxies, cp.marzban_inbounds, cp.enabled, cp.priority, cp.notes
       FROM plan_connection_profiles pcp
       JOIN connection_profiles cp ON cp.id = pcp.profile_id
       JOIN nodes n ON n.id = cp.node_id
       WHERE pcp.plan_id = $1
         AND pcp.is_default = TRUE
         AND cp.enabled = TRUE
         AND n.enabled = TRUE`,
      [planId],
    );
    const row = result.rows[0];
    return row === undefined ? null : this.mapConnectionProfile(row);
  }

  async getProfileForPlan(planId: number, profileId: number): Promise<ConnectionProfileRow | null> {
    const result = await this.query(
      `SELECT cp.id, cp.node_id, n.name AS node_name, cp.name, cp.protocol, cp.transport,
              cp.security, cp.port, cp.sni, cp.flow, cp.fingerprint, cp.marzban_inbound_tag,
              cp.marzban_proxies, cp.marzban_inbounds, cp.enabled, cp.priority, cp.notes
       FROM plan_connection_profiles pcp
       JOIN connection_profiles cp ON cp.id = pcp.profile_id
       JOIN nodes n ON n.id = cp.node_id
       WHERE pcp.plan_id = $1
         AND pcp.profile_id = $2
         AND cp.enabled = TRUE
         AND n.enabled = TRUE`,
      [planId, profileId],
    );
    const row = result.rows[0];
    return row === undefined ? null : this.mapConnectionProfile(row);
  }

  async getConnectionProfile(id: number): Promise<ConnectionProfileRow | null> {
    const result = await this.query(
      `SELECT cp.id, cp.node_id, n.name AS node_name, cp.name, cp.protocol, cp.transport,
              cp.security, cp.port, cp.sni, cp.flow, cp.fingerprint, cp.marzban_inbound_tag,
              cp.marzban_proxies, cp.marzban_inbounds, cp.enabled, cp.priority, cp.notes
       FROM connection_profiles cp
       JOIN nodes n ON n.id = cp.node_id
       WHERE cp.id = $1`,
      [id],
    );
    const row = result.rows[0];
    return row === undefined ? null : this.mapConnectionProfile(row);
  }

  async createOrder(input: {
    userId: number;
    planId: number;
    amount: number;
    kind: 'new' | 'renewal';
    renewalSubscriptionId?: number;
    connectionProfileId?: number;
  }): Promise<OrderRow> {
    const result = await this.query(
      `INSERT INTO orders (
         user_id, plan_id, amount, status, kind, renewal_subscription_id, connection_profile_id
       )
       VALUES ($1, $2, $3, 'waiting_payment', $4, $5, $6)
       RETURNING id, user_id, plan_id, amount, status, kind, renewal_subscription_id,
                 connection_profile_id, account_name, paid_at, provisioning_started_at, completed_at`,
      [
        input.userId,
        input.planId,
        input.amount,
        input.kind,
        input.renewalSubscriptionId ?? null,
        input.connectionProfileId ?? null,
      ],
    );
    return this.mapOrder(result.rows[0]);
  }

  async getOrder(id: number): Promise<OrderRow | null> {
    const result = await this.query(
      `SELECT id, user_id, plan_id, amount, status, kind, renewal_subscription_id,
              connection_profile_id, account_name, paid_at, provisioning_started_at, completed_at
       FROM orders WHERE id = $1`,
      [id],
    );
    const row = result.rows[0];
    return row === undefined ? null : this.mapOrder(row);
  }

  async findOpenOrderForUser(userId: number): Promise<OrderRow | null> {
    const result = await this.query(
      `SELECT id, user_id, plan_id, amount, status, kind, renewal_subscription_id,
              connection_profile_id, account_name, paid_at, provisioning_started_at, completed_at
       FROM orders
       WHERE user_id = $1 AND status = 'waiting_payment'
       ORDER BY created_at DESC
       LIMIT 1`,
      [userId],
    );
    const row = result.rows[0];
    return row === undefined ? null : this.mapOrder(row);
  }

  async cancelOpenOrders(userId: number): Promise<void> {
    await this.query(
      `UPDATE orders
       SET status = 'cancelled', updated_at = now()
       WHERE user_id = $1 AND status IN ('pending', 'waiting_payment')`,
      [userId],
    );
  }

  async cancelOrder(orderId: number, userId: number): Promise<boolean> {
    const result = await this.query(
      `UPDATE orders
       SET status = 'cancelled', updated_at = now()
       WHERE id = $1 AND user_id = $2 AND status IN ('pending', 'waiting_payment')
       RETURNING id`,
      [orderId, userId],
    );
    if ((result.rowCount ?? 0) === 0) {
      return false;
    }
    await this.query(
      `UPDATE payments
       SET status = 'rejected', verified_at = now()
       WHERE order_id = $1 AND status = 'pending'`,
      [orderId],
    );
    return true;
  }

  async updateOrderStatus(
    id: number,
    from: OrderStatus[],
    to: OrderStatus,
    extra: { paidAt?: Date } = {},
  ): Promise<OrderRow | null> {
    const result = await this.query(
      `UPDATE orders
       SET status = $3,
           paid_at = COALESCE($4, paid_at),
           updated_at = now()
       WHERE id = $1 AND status = ANY($2::text[])
       RETURNING id, user_id, plan_id, amount, status, kind, renewal_subscription_id,
                 connection_profile_id, account_name, paid_at, provisioning_started_at, completed_at`,
      [id, from, to, extra.paidAt ?? null],
    );
    const row = result.rows[0];
    return row === undefined ? null : this.mapOrder(row);
  }

  async claimOrderForProvisioning(id: number): Promise<OrderRow | null> {
    const result = await this.query(
      `UPDATE orders
       SET status = 'provisioning',
           provisioning_started_at = now(),
           updated_at = now()
       WHERE id = $1 AND status IN ('paid', 'failed')
       RETURNING id, user_id, plan_id, amount, status, kind, renewal_subscription_id,
                 connection_profile_id, account_name, paid_at, provisioning_started_at, completed_at`,
      [id],
    );
    const row = result.rows[0];
    return row === undefined ? null : this.mapOrder(row);
  }

  async completeProvisioning(id: number): Promise<OrderRow | null> {
    const result = await this.query(
      `UPDATE orders
       SET status = 'completed',
           completed_at = now(),
           updated_at = now()
       WHERE id = $1 AND status = 'provisioning'
       RETURNING id, user_id, plan_id, amount, status, kind, renewal_subscription_id,
                 connection_profile_id, account_name, paid_at, provisioning_started_at, completed_at`,
      [id],
    );
    const row = result.rows[0];
    return row === undefined ? null : this.mapOrder(row);
  }

  async releaseStaleProvisioningClaims(staleMinutes = 5): Promise<OrderRow[]> {
    const result = await this.query(
      `UPDATE orders
       SET status = 'failed', updated_at = now()
       WHERE status = 'provisioning'
         AND provisioning_started_at < now() - ($1 * INTERVAL '1 minute')
       RETURNING id, user_id, plan_id, amount, status, kind, renewal_subscription_id,
                 connection_profile_id, account_name, paid_at, provisioning_started_at, completed_at`,
      [staleMinutes],
    );
    return result.rows.map((row) => this.mapOrder(row));
  }

  async listRecoverableOrders(): Promise<OrderRow[]> {
    const result = await this.query(
      `SELECT id, user_id, plan_id, amount, status, kind, renewal_subscription_id,
              connection_profile_id, account_name, paid_at, provisioning_started_at, completed_at
       FROM orders
       WHERE status IN ('paid', 'failed')
       ORDER BY id ASC`,
    );
    return result.rows.map((row) => this.mapOrder(row));
  }

  async upsertPendingPayment(input: {
    orderId: number;
    userId: number;
    amount: number;
    receiptFileId: string;
    receiptKind: 'photo' | 'document';
  }): Promise<PaymentRow> {
    const result = await this.query(
      `INSERT INTO payments (order_id, user_id, amount, method, receipt_file_id, receipt_kind, status)
       VALUES ($1, $2, $3, 'card_to_card', $4, $5, 'pending')
       ON CONFLICT (order_id) WHERE status = 'pending'
       DO UPDATE SET
         receipt_file_id = EXCLUDED.receipt_file_id,
         receipt_kind = EXCLUDED.receipt_kind,
         amount = EXCLUDED.amount
       RETURNING id, order_id, user_id, amount, method, reference, receipt_file_id, receipt_kind,
                 status, verified_by, reviewed_by, reviewed_at, rejection_reason`,
      [input.orderId, input.userId, input.amount, input.receiptFileId, input.receiptKind],
    );
    return this.mapPayment(result.rows[0]);
  }

  async getPayment(id: number): Promise<PaymentRow | null> {
    const result = await this.query(
      `SELECT id, order_id, user_id, amount, method, reference, receipt_file_id, receipt_kind,
              status, verified_by, reviewed_by, reviewed_at, rejection_reason
       FROM payments WHERE id = $1`,
      [id],
    );
    const row = result.rows[0];
    return row === undefined ? null : this.mapPayment(row);
  }

  async approvePayment(id: number, adminTelegramId: number): Promise<PaymentRow | null> {
    const result = await this.query(
      `UPDATE payments p
       SET status = 'approved',
           verified_at = now(),
           verified_by = $2,
           reviewed_at = now(),
           reviewed_by = $2,
           rejection_reason = NULL
       FROM orders o
       WHERE p.id = $1
         AND p.status = 'pending'
         AND o.id = p.order_id
         AND o.status IN ('pending', 'waiting_payment', 'paid', 'provisioning', 'failed')
       RETURNING p.id, p.order_id, p.user_id, p.amount, p.method, p.reference,
                 p.receipt_file_id, p.receipt_kind, p.status, p.verified_by,
                 p.reviewed_by, p.reviewed_at, p.rejection_reason`,
      [id, adminTelegramId],
    );
    const row = result.rows[0];
    return row === undefined ? null : this.mapPayment(row);
  }

  async rejectPayment(
    id: number,
    adminTelegramId: number,
    rejectionReason?: string,
  ): Promise<PaymentRow | null> {
    const result = await this.query(
      `UPDATE payments
       SET status = 'rejected',
           verified_at = now(),
           verified_by = $2,
           reviewed_at = now(),
           reviewed_by = $2,
           rejection_reason = $3
       WHERE id = $1 AND status = 'pending'
       RETURNING id, order_id, user_id, amount, method, reference, receipt_file_id, receipt_kind,
                 status, verified_by, reviewed_by, reviewed_at, rejection_reason`,
      [id, adminTelegramId, rejectionReason?.trim() || null],
    );
    const row = result.rows[0];
    return row === undefined ? null : this.mapPayment(row);
  }

  async getSubscriptionByOrder(orderId: number): Promise<SubscriptionRow | null> {
    const result = await this.query(
      `SELECT s.id, s.user_id, s.order_id, s.marzban_username, s.account_name,
              s.subscription_url, s.traffic_gb,
              s.start_at, s.expire_at, s.status, s.node, s.connection_profile_id,
              cp.name AS connection_profile_name, p.name AS plan_name
       FROM subscriptions s
       JOIN orders o ON o.id = s.order_id
       JOIN plans p ON p.id = o.plan_id
       LEFT JOIN connection_profiles cp ON cp.id = s.connection_profile_id
       WHERE s.order_id = $1`,
      [orderId],
    );
    const row = result.rows[0];
    return row === undefined ? null : this.mapSubscription(row);
  }

  async getSubscription(id: number): Promise<SubscriptionRow | null> {
    const result = await this.query(
      `SELECT s.id, s.user_id, s.order_id, s.marzban_username, s.account_name,
              s.subscription_url, s.traffic_gb,
              s.start_at, s.expire_at, s.status, s.node, s.connection_profile_id,
              cp.name AS connection_profile_name, p.name AS plan_name
       FROM subscriptions s
       JOIN orders o ON o.id = s.order_id
       JOIN plans p ON p.id = o.plan_id
       LEFT JOIN connection_profiles cp ON cp.id = s.connection_profile_id
       WHERE s.id = $1`,
      [id],
    );
    const row = result.rows[0];
    return row === undefined ? null : this.mapSubscription(row);
  }

  async listUserSubscriptions(userId: number): Promise<SubscriptionRow[]> {
    const result = await this.query(
      `SELECT s.id, s.user_id, s.order_id, s.marzban_username, s.account_name,
              s.subscription_url, s.traffic_gb,
              s.start_at, s.expire_at, s.status, s.node, s.connection_profile_id,
              cp.name AS connection_profile_name, p.name AS plan_name
       FROM subscriptions s
       JOIN orders o ON o.id = s.order_id
       JOIN plans p ON p.id = o.plan_id
       LEFT JOIN connection_profiles cp ON cp.id = s.connection_profile_id
       WHERE s.user_id = $1 AND s.status IN ('active', 'expired', 'suspended')
       ORDER BY s.status ASC, s.expire_at DESC`,
      [userId],
    );
    return result.rows.map((row) => this.mapSubscription(row));
  }

  async insertSubscription(input: {
    userId: number;
    orderId: number;
    marzbanUsername: string;
    accountName: string;
    subscriptionUrl: string;
    trafficGb: number;
    startAt: Date;
    expireAt: Date;
    node: string;
    connectionProfileId?: number;
  }): Promise<SubscriptionRow> {
    const result = await this.query(
      `INSERT INTO subscriptions (
         user_id, order_id, marzban_username, account_name, subscription_url, traffic_gb,
         start_at, expire_at, status, node, connection_profile_id
       ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'active', $9, $10)
       ON CONFLICT (order_id) DO UPDATE SET
         account_name = EXCLUDED.account_name,
         subscription_url = EXCLUDED.subscription_url,
         traffic_gb = EXCLUDED.traffic_gb,
         expire_at = EXCLUDED.expire_at,
         status = 'active',
         node = EXCLUDED.node,
         connection_profile_id = EXCLUDED.connection_profile_id,
         updated_at = now()
       RETURNING id, user_id, order_id, marzban_username, account_name, subscription_url, traffic_gb,
                 start_at, expire_at, status, node, connection_profile_id,
                 NULL::text AS connection_profile_name, NULL::text AS plan_name`,
      [
        input.userId,
        input.orderId,
        input.marzbanUsername,
        input.accountName,
        input.subscriptionUrl,
        input.trafficGb,
        input.startAt,
        input.expireAt,
        input.node,
        input.connectionProfileId ?? null,
      ],
    );
    return this.mapSubscription(result.rows[0]);
  }

  async updateSubscriptionUrl(id: number, subscriptionUrl: string): Promise<SubscriptionRow> {
    const result = await this.query(
      `UPDATE subscriptions
       SET subscription_url = $2, updated_at = now()
       WHERE id = $1
       RETURNING id, user_id, order_id, marzban_username, account_name, subscription_url, traffic_gb,
                 start_at, expire_at, status, node, connection_profile_id,
                 NULL::text AS connection_profile_name, NULL::text AS plan_name`,
      [id, subscriptionUrl],
    );
    return this.mapSubscription(result.rows[0]);
  }

  async listActiveSubscriptions(): Promise<SubscriptionRow[]> {
    const result = await this.query(
      `SELECT s.id, s.user_id, s.order_id, s.marzban_username, s.account_name,
              s.subscription_url, s.traffic_gb,
              s.start_at, s.expire_at, s.status, s.node, s.connection_profile_id,
              cp.name AS connection_profile_name, p.name AS plan_name
       FROM subscriptions s
       LEFT JOIN orders o ON o.id = s.order_id
       LEFT JOIN plans p ON p.id = o.plan_id
       LEFT JOIN connection_profiles cp ON cp.id = s.connection_profile_id
       WHERE s.status = 'active'
       ORDER BY s.id ASC`,
    );
    return result.rows.map((row) => this.mapSubscription(row));
  }

  async updateSubscriptionRenewal(input: {
    id: number;
    subscriptionUrl: string;
    trafficGb: number;
    expireAt: Date;
    node: string;
  }): Promise<SubscriptionRow> {
    const result = await this.query(
      `UPDATE subscriptions
       SET subscription_url = $2,
           traffic_gb = $3,
           expire_at = $4,
           status = 'active',
           node = $5,
           updated_at = now()
       WHERE id = $1
       RETURNING id, user_id, order_id, marzban_username, account_name, subscription_url, traffic_gb,
                 start_at, expire_at, status, node, connection_profile_id,
                 NULL::text AS connection_profile_name, NULL::text AS plan_name`,
      [input.id, input.subscriptionUrl, input.trafficGb, input.expireAt, input.node],
    );
    return this.mapSubscription(result.rows[0]);
  }

  async reserveOrderAccountName(orderId: number): Promise<string> {
    const reserved = await this.query(
      `UPDATE orders
       SET account_name = 'FOX' || nextval('vpn_account_number_seq')::text,
           updated_at = now()
       WHERE id = $1
         AND kind = 'new'
         AND account_name IS NULL
       RETURNING account_name`,
      [orderId],
    );
    const newName = reserved.rows[0]?.['account_name'];
    if (typeof newName === 'string') {
      return newName;
    }

    const existing = await this.query(
      `SELECT account_name
       FROM orders
       WHERE id = $1 AND kind = 'new'`,
      [orderId],
    );
    const existingName = existing.rows[0]?.['account_name'];
    if (typeof existingName !== 'string') {
      throw new Error('new order account name could not be reserved');
    }
    return existingName;
  }

  async recordProfileTestForUser(input: {
    userId: number;
    subscriptionId: number;
    isp: string;
    networkType: string;
    connected: boolean;
    downloadOk: boolean | null;
    clientApp: string;
    failureStage?: string;
  }): Promise<boolean> {
    const result = await this.query(
      `INSERT INTO profile_test_results (
         profile_id, isp, network_type, connected, download_ok, client_app, failure_stage, source
       )
       SELECT s.connection_profile_id, $3, $4, $5, $6, $7, $8, 'customer_bot'
       FROM subscriptions s
       WHERE s.id = $1
         AND s.user_id = $2
         AND s.connection_profile_id IS NOT NULL
       RETURNING id`,
      [
        input.subscriptionId,
        input.userId,
        input.isp,
        input.networkType,
        input.connected,
        input.downloadOk,
        input.clientApp,
        input.failureStage ?? null,
      ],
    );
    return (result.rowCount ?? 0) === 1;
  }

  async markExpiredSubscriptions(now: Date = new Date()): Promise<number> {
    const result = await this.query(
      `UPDATE subscriptions
       SET status = 'expired', updated_at = now()
       WHERE status = 'active' AND expire_at <= $1`,
      [now],
    );
    return result.rowCount ?? 0;
  }

  private mapUser(row: Record<string, unknown> | undefined): UserRow {
    if (row === undefined) {
      throw new Error('user row missing');
    }
    return {
      id: num(row['id']),
      telegram_id: String(row['telegram_id']),
      telegram_username: optionalStr(row['telegram_username']),
      first_name: optionalStr(row['first_name']),
      phone: optionalStr(row['phone']),
      status: str(row['status']) as UserRow['status'],
    };
  }

  private mapPlan(row: Record<string, unknown> | undefined): PlanRow {
    if (row === undefined) {
      throw new Error('plan row missing');
    }
    return {
      id: num(row['id']),
      name: str(row['name']),
      traffic_gb: num(row['traffic_gb']),
      duration_days: num(row['duration_days']),
      price: num(row['price']),
      currency: str(row['currency']),
      marzban_profile: optionalStr(row['marzban_profile']),
      node: optionalStr(row['node']),
      is_active: Boolean(row['is_active']),
    };
  }

  private mapConnectionProfile(row: Record<string, unknown> | undefined): ConnectionProfileRow {
    if (row === undefined) {
      throw new Error('connection profile row missing');
    }
    return {
      id: num(row['id']),
      node_id: num(row['node_id']),
      node_name: str(row['node_name']),
      name: str(row['name']),
      protocol: str(row['protocol']),
      transport: str(row['transport']),
      security: str(row['security']),
      port: num(row['port']),
      sni: optionalStr(row['sni']),
      flow: optionalStr(row['flow']),
      fingerprint: optionalStr(row['fingerprint']),
      marzban_inbound_tag: str(row['marzban_inbound_tag']),
      marzban_proxies: object(row['marzban_proxies']),
      marzban_inbounds: object(row['marzban_inbounds']),
      enabled: Boolean(row['enabled']),
      priority: num(row['priority']),
      notes: optionalStr(row['notes']),
    };
  }

  private mapOrder(row: Record<string, unknown> | undefined): OrderRow {
    if (row === undefined) {
      throw new Error('order row missing');
    }
    return {
      id: num(row['id']),
      user_id: num(row['user_id']),
      plan_id: num(row['plan_id']),
      amount: num(row['amount']),
      status: str(row['status']) as OrderStatus,
      kind: str(row['kind']) as OrderRow['kind'],
      renewal_subscription_id:
        row['renewal_subscription_id'] === null ? null : num(row['renewal_subscription_id']),
      connection_profile_id: optionalNum(row['connection_profile_id']),
      account_name: optionalStr(row['account_name']),
      paid_at: row['paid_at'] instanceof Date ? row['paid_at'] : null,
      provisioning_started_at:
        row['provisioning_started_at'] instanceof Date ? row['provisioning_started_at'] : null,
      completed_at: row['completed_at'] instanceof Date ? row['completed_at'] : null,
    };
  }

  private mapPayment(row: Record<string, unknown> | undefined): PaymentRow {
    if (row === undefined) {
      throw new Error('payment row missing');
    }
    return {
      id: num(row['id']),
      order_id: num(row['order_id']),
      user_id: num(row['user_id']),
      amount: num(row['amount']),
      method: str(row['method']),
      reference: optionalStr(row['reference']),
      receipt_file_id: optionalStr(row['receipt_file_id']),
      receipt_kind:
        row['receipt_kind'] === null || row['receipt_kind'] === undefined
          ? null
          : (str(row['receipt_kind']) as PaymentRow['receipt_kind']),
      status: str(row['status']) as PaymentStatus,
      verified_by:
        row['verified_by'] === null || row['verified_by'] === undefined
          ? null
          : String(row['verified_by']),
      reviewed_by:
        row['reviewed_by'] === null || row['reviewed_by'] === undefined
          ? null
          : String(row['reviewed_by']),
      reviewed_at: row['reviewed_at'] instanceof Date ? row['reviewed_at'] : null,
      rejection_reason: optionalStr(row['rejection_reason']),
    };
  }

  private mapSubscription(row: Record<string, unknown> | undefined): SubscriptionRow {
    if (row === undefined) {
      throw new Error('subscription row missing');
    }
    const startAt = row['start_at'];
    const expireAt = row['expire_at'];
    if (!(startAt instanceof Date) || !(expireAt instanceof Date)) {
      throw new Error('invalid subscription timestamps');
    }
    return {
      id: num(row['id']),
      user_id: num(row['user_id']),
      order_id: num(row['order_id']),
      marzban_username: str(row['marzban_username']),
      account_name: str(row['account_name']),
      subscription_url: str(row['subscription_url']),
      traffic_gb: num(row['traffic_gb']),
      start_at: startAt,
      expire_at: expireAt,
      status: str(row['status']) as SubscriptionRow['status'],
      node: optionalStr(row['node']),
      connection_profile_id: optionalNum(row['connection_profile_id']),
      connection_profile_name: optionalStr(row['connection_profile_name']),
      plan_name: optionalStr(row['plan_name']),
    };
  }
}
